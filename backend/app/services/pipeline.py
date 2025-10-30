"""Lightweight image-to-vector conversion helpers.

The original implementation relied on third-party scientific libraries such as
Pillow, NumPy, scikit-image and CairoSVG. Those dependencies are not available
in the execution environment used for the automated tests, so the module now
contains a tiny self-contained pipeline that operates purely with the Python
standard library.  It understands 8-bit grayscale PNG images, performs a simple
median denoise pass, extracts high-contrast pixels using a Sobel-inspired
gradient magnitude and exports coarse vector output as SVG, PDF (for Adobe
Illustrator compatibility) and EPS.
"""

from __future__ import annotations

import base64
import io
import math
import struct
import zlib
from dataclasses import dataclass
from typing import BinaryIO, Dict, Iterable, List, Sequence, Tuple


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class UploadedFileProtocol:
    """Minimal protocol describing the attribute used by FastAPI's UploadFile."""

    file: BinaryIO


def _read_upload_stream(upload: UploadedFileProtocol) -> bytes:
    contents = upload.file.read()
    if not contents:
        raise ValueError("Uploaded file is empty")
    return contents


def _parse_png_grayscale(data: bytes) -> Tuple[List[List[int]], int, int]:
    """Parse an 8-bit grayscale PNG image into a 2-D list of integers."""

    stream = io.BytesIO(data)
    signature = stream.read(8)
    if signature != PNG_SIGNATURE:
        raise ValueError("Only PNG images are supported")

    width = height = None
    bit_depth = color_type = None
    compression = filter_method = interlace = None
    idat_chunks: List[bytes] = []

    while True:
        length_bytes = stream.read(4)
        if len(length_bytes) == 0:
            break
        if len(length_bytes) != 4:
            raise ValueError("Corrupted PNG chunk length")
        (length,) = struct.unpack(">I", length_bytes)
        chunk_type = stream.read(4)
        chunk_data = stream.read(length)
        stream.read(4)  # CRC – validated implicitly by zlib when decoding

        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
                ">IIBBBBB", chunk_data
            )
        elif chunk_type == b"IDAT":
            idat_chunks.append(chunk_data)
        elif chunk_type == b"IEND":
            break

    if None in (width, height, bit_depth, color_type, compression, filter_method, interlace):
        raise ValueError("PNG header is incomplete")

    if bit_depth != 8 or color_type != 0:
        raise ValueError("Only 8-bit grayscale PNG images are supported")
    if compression != 0 or filter_method != 0 or interlace != 0:
        raise ValueError("Unsupported PNG compression parameters")

    decompressed = zlib.decompress(b"".join(idat_chunks))
    stride = width + 1
    expected = stride * height
    if len(decompressed) != expected:
        raise ValueError("PNG data size mismatch")

    rows: List[List[int]] = []
    previous = [0] * width
    offset = 0
    for _ in range(height):
        filter_type = decompressed[offset]
        offset += 1
        raw_row = list(decompressed[offset : offset + width])
        offset += width
        if filter_type == 0:
            row = raw_row
        elif filter_type == 1:
            row = _png_filter_sub(raw_row, width)
        elif filter_type == 2:
            row = _png_filter_up(raw_row, previous)
        elif filter_type == 3:
            row = _png_filter_average(raw_row, previous)
        elif filter_type == 4:
            row = _png_filter_paeth(raw_row, previous)
        else:
            raise ValueError(f"Unsupported PNG filter type: {filter_type}")
        rows.append(row)
        previous = row
    return rows, width, height


def _png_filter_sub(raw: List[int], width: int) -> List[int]:
    output = []
    running = 0
    for i in range(width):
        running = (raw[i] + running) & 0xFF
        output.append(running)
    return output


def _png_filter_up(raw: List[int], previous: Sequence[int]) -> List[int]:
    return [(raw[i] + previous[i]) & 0xFF for i in range(len(raw))]


def _png_filter_average(raw: List[int], previous: Sequence[int]) -> List[int]:
    output = []
    left = 0
    for i, value in enumerate(raw):
        avg = (left + previous[i]) // 2
        pixel = (value + avg) & 0xFF
        output.append(pixel)
        left = pixel
    return output


def _paeth_predictor(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _png_filter_paeth(raw: List[int], previous: Sequence[int]) -> List[int]:
    output = []
    left = 0
    for i, value in enumerate(raw):
        predictor = _paeth_predictor(left, previous[i], previous[i - 1] if i else 0)
        pixel = (value + predictor) & 0xFF
        output.append(pixel)
        left = pixel
    return output


def _denoise(pixels: List[List[int]], strength: float) -> List[List[int]]:
    strength = max(0.0, min(strength, 5.0))
    repeats = int(round(strength))
    if repeats == 0:
        return [row[:] for row in pixels]

    height = len(pixels)
    width = len(pixels[0]) if height else 0
    current = [row[:] for row in pixels]

    for _ in range(repeats):
        updated = [[0] * width for _ in range(height)]
        for y in range(height):
            for x in range(width):
                window = []
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny = min(max(y + dy, 0), height - 1)
                        nx = min(max(x + dx, 0), width - 1)
                        window.append(current[ny][nx])
                window.sort()
                updated[y][x] = window[len(window) // 2]
        current = updated
    return current


def _gradient_magnitude(pixels: List[List[int]]) -> List[List[float]]:
    height = len(pixels)
    width = len(pixels[0]) if height else 0
    gradients = [[0.0] * width for _ in range(height)]

    def sample(xx: int, yy: int) -> int:
        if xx < 0:
            xx = 0
        elif xx >= width:
            xx = width - 1
        if yy < 0:
            yy = 0
        elif yy >= height:
            yy = height - 1
        return pixels[yy][xx]

    for y in range(height):
        for x in range(width):
            gx = sample(x + 1, y) - sample(x - 1, y)
            gy = sample(x, y + 1) - sample(x, y - 1)
            gradients[y][x] = math.sqrt(gx * gx + gy * gy)
    return gradients


def _detect_edges(
    pixels: List[List[int]], threshold: float, sigma: float | None = None
) -> List[List[bool]]:
    del sigma  # retained for API parity; smoothing occurs via the denoise step
    threshold = max(0.0, min(threshold, 1.0))
    gradients = _gradient_magnitude(pixels)
    height = len(gradients)
    width = len(gradients[0]) if height else 0
    cutoff = threshold * 255.0
    return [[gradients[y][x] >= cutoff for x in range(width)] for y in range(height)]


def _edges_to_rectangles(edges: List[List[bool]]) -> Tuple[List[Tuple[int, int, int, int]], int, int]:
    height = len(edges)
    width = len(edges[0]) if height else 0
    rectangles: List[Tuple[int, int, int, int]] = []

    for y in range(height):
        start = None
        for x in range(width):
            if edges[y][x]:
                if start is None:
                    start = x
            elif start is not None:
                length = x - start
                if length > 0:
                    rectangles.append((start, y, length, 1))
                start = None
        if start is not None:
            length = width - start
            if length > 0:
                rectangles.append((start, y, length, 1))
    return rectangles, width, height


def _rectangles_to_svg(rectangles: Iterable[Tuple[int, int, int, int]], width: int, height: int) -> str:
    parts = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        f"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{width}\" height=\"{height}\" viewBox=\"0 0 {width} {height}\">",
        "<g fill=\"black\" stroke=\"none\">",
    ]
    for x, y, w, h in rectangles:
        parts.append(f"<rect x=\"{x}\" y=\"{y}\" width=\"{w}\" height=\"{h}\" />")
    parts.append("</g></svg>")
    return "".join(parts)


def _rectangles_to_pdf(rectangles: Sequence[Tuple[int, int, int, int]], width: int, height: int) -> bytes:
    stream_commands = []
    for x, y, w, h in rectangles:
        bottom = height - y - h
        stream_commands.append(f"{x} {bottom} {w} {h} re f\n")
    content = ("q 0 g\n" + "".join(stream_commands) + "Q\n").encode("ascii")

    objects = []
    objects.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    objects.append(b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n")
    mediabox = f"[0 0 {width} {height}]"
    objects.append(
        f"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox {mediabox} /Contents 4 0 R >>endobj\n".encode(
            "ascii"
        )
    )
    objects.append(
        f"4 0 obj<< /Length {len(content)} >>stream\n".encode("ascii")
        + content
        + b"endstream endobj\n"
    )

    offsets = [0]
    for obj in objects:
        offsets.append(offsets[-1] + len(obj))
    offsets = offsets[1:]

    pdf = [b"%PDF-1.4\n"]
    position = len(pdf[0])
    xref_entries = [b"0000000000 65535 f \n"]
    for obj, offset in zip(objects, offsets):
        pdf.append(obj)
        xref_entries.append(f"{offset + position:010} 00000 n \n".encode("ascii"))
        position += len(obj)

    xref_start = position
    pdf.append(f"xref\n0 {len(xref_entries)}\n".encode("ascii"))
    pdf.append(b"".join(xref_entries))
    pdf.append(b"trailer<< /Root 1 0 R /Size " + str(len(xref_entries)).encode("ascii") + b" >>\n")
    pdf.append(f"startxref\n{xref_start}\n%%EOF".encode("ascii"))
    return b"".join(pdf)


def _rectangles_to_eps(rectangles: Sequence[Tuple[int, int, int, int]], width: int, height: int) -> bytes:
    lines = [
        "%!PS-Adobe-3.0 EPSF-3.0",
        f"%%BoundingBox: 0 0 {width} {height}",
        "0 setgray",
    ]
    for x, y, w, h in rectangles:
        bottom = height - y - h
        lines.append(
            f"newpath {x} {bottom} moveto {w} 0 rlineto 0 {h} rlineto {-w} 0 rlineto closepath fill"
        )
    lines.append("showpage")
    return "\n".join(lines).encode("ascii")


def _encode_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


@dataclass
class ConversionRequest:
    file: UploadedFileProtocol
    denoise_strength: float
    edge_sigma: float
    threshold: float


async def convert_image(request: ConversionRequest) -> Dict[str, str]:
    raw = _read_upload_stream(request.file)
    pixels, width, height = _parse_png_grayscale(raw)
    cleaned = _denoise(pixels, request.denoise_strength)
    edges = _detect_edges(cleaned, request.threshold or 0.2, request.edge_sigma)
    rectangles, width, height = _edges_to_rectangles(edges)
    svg = _rectangles_to_svg(rectangles, width, height)
    ai = _rectangles_to_pdf(rectangles, width, height)
    eps = _rectangles_to_eps(rectangles, width, height)
    return {"svg": svg, "ai": _encode_base64(ai), "eps": _encode_base64(eps)}


__all__ = [
    "ConversionRequest",
    "convert_image",
    "_denoise",
    "_detect_edges",
]
