"""Módulos relacionados con la síntesis de voz."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

try:  # pragma: no cover - dependencia opcional
    import edge_tts
except ImportError:  # pragma: no cover - dependencia opcional
    edge_tts = None  # type: ignore[assignment]

from .config import GenerationConfig, VoiceProfile


@dataclass
class TTSAudioResult:
    """Resultado de generar audio con TTS."""

    audio_path: Path
    subtitles_path: Optional[Path] = None


class TTSEngine:
    """Interfaz para implementar motores de síntesis de voz."""

    async def synthesize(self, config: GenerationConfig) -> TTSAudioResult:  # pragma: no cover - interface
        raise NotImplementedError


class EdgeTTSEngine(TTSEngine):
    """Implementación basada en el servicio Edge TTS (gratuito)."""

    def __init__(self, voice: VoiceProfile) -> None:
        if edge_tts is None:  # pragma: no cover - verificación de dependencia
            raise ImportError(
                "El paquete 'edge-tts' es necesario para usar EdgeTTSEngine. Instálalo con 'pip install edge-tts'."
            )
        self._voice = voice

    async def synthesize(self, config: GenerationConfig) -> TTSAudioResult:
        output_path = config.output_audio_path()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        communicate = edge_tts.Communicate(
            config.script_text,
            self._voice.voice_id,
            pitch=f"{self._voice.pitch:+}st" if self._voice.pitch is not None else None,
            rate=f"{self._voice.rate:+.0%}" if self._voice.rate is not None else None,
            voice_locale=self._voice.locale,
            style=self._voice.style,
        )

        subtitles_path = config.subtitles_path() if config.subtitles else None

        async def _iter_chunks() -> Iterable[bytes]:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
                elif chunk["type"] == "WordBoundary" and subtitles_path:
                    _write_subtitle_event(subtitles_path, chunk)

        audio_bytes = bytearray()
        async for data in _iter_chunks():
            audio_bytes.extend(data)

        output_path.write_bytes(bytes(audio_bytes))
        return TTSAudioResult(audio_path=output_path, subtitles_path=subtitles_path)


def _write_subtitle_event(path: Path, event: dict) -> None:
    """Registra eventos de palabras en un archivo SRT sencillo."""

    path.parent.mkdir(parents=True, exist_ok=True)
    index = 1
    if path.exists():
        existing = path.read_text(encoding="utf-8").strip()
        if existing:
            index = existing.count("\n\n") + 1
    start_ms = int(event["offset"])
    duration_ms = int(event["duration"])
    end_ms = start_ms + duration_ms

    def _format(ms: int) -> str:
        hours = ms // 3_600_000
        minutes = (ms % 3_600_000) // 60_000
        seconds = (ms % 60_000) // 1000
        millis = ms % 1000
        return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"

    text = event.get("text", "").strip()
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"{index}\n{_format(start_ms)} --> {_format(end_ms)}\n{text}\n\n")


def build_tts_engine(config: GenerationConfig) -> TTSEngine:
    """Crea una instancia de motor TTS según la configuración."""

    provider = config.tts_provider.lower()
    if provider == "edge":
        return EdgeTTSEngine(config.voice)
    raise ValueError(f"Proveedor de TTS no soportado: {config.tts_provider}")


def run_tts(config: GenerationConfig) -> TTSAudioResult:
    """Ejecuta el motor TTS correspondiente y devuelve el resultado."""

    engine = build_tts_engine(config)
    return asyncio.run(engine.synthesize(config))
