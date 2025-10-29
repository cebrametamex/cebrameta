"""Orquestador del flujo completo de generación."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .audio import TTSAudioResult, run_tts
from .config import GenerationConfig
from .lipsync import LipSyncResult, run_lipsync
from .utils import load_environment_file


@dataclass
class PipelineArtifacts:
    """Rutas clave producidas por el pipeline."""

    audio: Path
    video: Path
    subtitles: Optional[Path]


class AvatarGenerationPipeline:
    """Pipeline de alto nivel para generar avatares hablantes."""

    def __init__(self, config: GenerationConfig) -> None:
        self.config = config

    def run(self) -> PipelineArtifacts:
        load_environment_file(self.config.environment_file)

        tts_result = self._generate_audio()
        video_result = self._generate_video()
        self._persist_manifest(tts_result, video_result)
        return PipelineArtifacts(
            audio=tts_result.audio_path,
            video=video_result.video_path,
            subtitles=tts_result.subtitles_path,
        )

    def _generate_audio(self) -> TTSAudioResult:
        return run_tts(self.config)

    def _generate_video(self) -> LipSyncResult:
        return run_lipsync(self.config)

    def _persist_manifest(self, audio: TTSAudioResult, video: LipSyncResult) -> None:
        manifest = {
            "image": str(self.config.image_path),
            "script": self.config.script_text,
            "audio": str(audio.audio_path),
            "video": str(video.video_path),
            "subtitles": str(audio.subtitles_path) if audio.subtitles_path else None,
            "voice": self.config.voice.to_dict(),
            "tts_provider": self.config.tts_provider,
            "lipsync_engine": self.config.lipsync_engine,
            "fps": self.config.fps,
        }

        manifest_path = self.config.output_dir / f"{self.config.project_name}_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

        if not self.config.keep_intermediate:
            self._cleanup_intermediate()

    def _cleanup_intermediate(self) -> None:
        cache_dir = self.config.output_dir / "temp"
        if cache_dir.exists():
            for path in cache_dir.glob("**/*"):
                if path.is_file():
                    path.unlink()
            for path in sorted(cache_dir.glob("**/*"), reverse=True):
                if path.is_dir():
                    path.rmdir()
