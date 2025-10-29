"""Integraciones con motores de animación facial y lip-sync."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .config import GenerationConfig


@dataclass
class LipSyncResult:
    """Resultado de ejecutar el motor de lip-sync."""

    video_path: Path


class LipSyncEngine:
    """Interfaz base para motores de lip-sync."""

    def generate(self, config: GenerationConfig) -> LipSyncResult:  # pragma: no cover
        raise NotImplementedError


class SadTalkerEngine(LipSyncEngine):
    """Wrapper para SadTalker ejecutado vía línea de comandos."""

    def __init__(self, command: str = "sadtalker") -> None:
        self.command = command

    def generate(self, config: GenerationConfig) -> LipSyncResult:
        output_path = config.output_video_path()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd: List[str] = [
            self.command,
            "--driven_audio",
            str(config.output_audio_path()),
            "--source_image",
            str(config.image_path),
            "--result_dir",
            str(config.output_dir),
            "--output",
            output_path.name,
            "--fps",
            str(config.fps),
        ]
        cmd.extend(config.lipsync_extra_args)

        subprocess.run(cmd, check=True)
        return LipSyncResult(video_path=output_path)


class Wav2LipEngine(LipSyncEngine):
    """Integración con Wav2Lip ejecutado vía script python."""

    def __init__(self, script_path: Path, checkpoint_path: Path) -> None:
        self.script_path = script_path
        self.checkpoint_path = checkpoint_path

    def generate(self, config: GenerationConfig) -> LipSyncResult:
        output_path = config.output_video_path()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "python",
            str(self.script_path),
            "--checkpoint_path",
            str(self.checkpoint_path),
            "--face",
            str(config.image_path),
            "--audio",
            str(config.output_audio_path()),
            "--outfile",
            str(output_path),
        ]
        cmd.extend(config.lipsync_extra_args)
        subprocess.run(cmd, check=True)
        return LipSyncResult(video_path=output_path)


def build_lipsync_engine(config: GenerationConfig) -> LipSyncEngine:
    engine = config.lipsync_engine.lower()
    if engine == "sadtalker":
        return SadTalkerEngine()
    raise ValueError(f"Motor de lip-sync no soportado: {config.lipsync_engine}")


def run_lipsync(config: GenerationConfig) -> LipSyncResult:
    engine = build_lipsync_engine(config)
    return engine.generate(config)
