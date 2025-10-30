from app.services.pipeline import (
    ConversionRequest,
    convert_image,
    _denoise,
    _detect_edges,
)


def create_png(width: int, height: int, value: int) -> bytes:
    """Create a solid grayscale PNG image with the given value."""

    import struct
    import zlib

    if not 0 <= value <= 255:
        raise ValueError("value must be between 0 and 255")

    def chunk(kind: bytes, payload: bytes) -> bytes:
        crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)

    scanline = bytes([0] + [value] * width)
    raw = scanline * height
    idat = zlib.compress(raw)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    return b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            chunk(b"IHDR", ihdr),
            chunk(b"IDAT", idat),
            chunk(b"IEND", b""),
        ]
    )


class DummyUpload:
    def __init__(self, data: bytes):
        from io import BytesIO

        self.file = BytesIO(data)


def create_test_image(size: int = 64) -> list[list[int]]:
    return [
        [
            255 if size // 4 <= x < 3 * size // 4 and size // 4 <= y < 3 * size // 4 else 0
            for x in range(size)
        ]
        for y in range(size)
    ]


def test_denoise_limits_strength():
    img = create_test_image()
    result = _denoise(img, strength=10)
    assert len(result) == 64
    assert len(result[0]) == 64


def test_edge_detection_threshold():
    img = create_test_image()
    edges = _detect_edges(img, threshold=0.1)
    assert any(any(row) for row in edges)


def test_full_conversion_pipeline():
    png_bytes = create_png(16, 16, 255)
    upload = DummyUpload(png_bytes)

    request = ConversionRequest(
        file=upload,
        denoise_strength=1.0,
        edge_sigma=1.0,
        threshold=0.2,
    )
    import asyncio

    result = asyncio.run(convert_image(request))

    assert result["svg"].startswith("<?xml")
    assert result["ai"].startswith("JVBER")
    assert result["eps"].startswith("JSFQ")
