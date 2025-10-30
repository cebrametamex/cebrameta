import pytest

from app.main import convert


class DummyUpload:
    def __init__(self, data: bytes):
        from io import BytesIO

        self.file = BytesIO(data)


def create_png(width: int, height: int, value: int) -> bytes:
    import struct
    import zlib

    def chunk(kind: bytes, payload: bytes) -> bytes:
        crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)

    scanline = bytes([0] + [value] * width)
    raw = scanline * height
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    idat = zlib.compress(raw)
    return b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            chunk(b"IHDR", ihdr),
            chunk(b"IDAT", idat),
            chunk(b"IEND", b""),
        ]
    )


def test_convert_endpoint_success():
    png = create_png(8, 8, 200)
    upload = DummyUpload(png)

    import asyncio

    response = asyncio.run(
        convert(
        file=upload,
        denoise_strength=1.0,
        edge_sigma=1.0,
        threshold=0.2,
        )
    )

    assert response.status_code == 200
    payload = dict(response)
    assert payload["svg"].startswith("<?xml")
    assert payload["ai"].startswith("JVBER")
    assert payload["eps"].startswith("JSFQ")


def test_convert_endpoint_empty_upload():
    upload = DummyUpload(b"\x00")

    with pytest.raises(Exception):
        import asyncio

        asyncio.run(
            convert(
                file=upload,
                denoise_strength=1.0,
                edge_sigma=1.0,
                threshold=0.2,
            )
        )
