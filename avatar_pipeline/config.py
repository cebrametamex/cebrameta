"""Definiciones de configuración para la generación de avatares."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class VoiceProfile:
    """Perfil de voz disponible para síntesis."""

    name: str
    display_name: str
    locale: str
    voice_id: str
    description: Optional[str] = None
    style: Optional[str] = None
    pitch: Optional[float] = None
    rate: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GenerationConfig:
    """Configuración completa para ejecutar el pipeline de generación."""

    image_path: Path
    script_text: str
    voice: VoiceProfile
    output_dir: Path = Path("outputs")
    project_name: str = "avatar"
    sample_rate: int = 48000
    tts_provider: str = "edge"
    lipsync_engine: str = "sadtalker"
    fps: int = 25
    keep_intermediate: bool = False
    subtitles: bool = True
    environment_file: Optional[Path] = None
    lipsync_extra_args: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.image_path = Path(self.image_path).expanduser().resolve()
        self.output_dir = Path(self.output_dir).expanduser().resolve()
        if self.environment_file is not None:
            self.environment_file = Path(self.environment_file).expanduser().resolve()

        script = self.script_text.strip()
        if not script:
            raise ValueError("El guion no puede estar vacío.")
        self.script_text = script

        if not (16000 <= self.sample_rate <= 96000):
            raise ValueError("La frecuencia de muestreo debe estar entre 16 kHz y 96 kHz.")
        if not (12 <= self.fps <= 60):
            raise ValueError("Los FPS deben estar entre 12 y 60.")

        self.lipsync_extra_args = list(self.lipsync_extra_args)

    def output_audio_path(self) -> Path:
        return self.output_dir / f"{self.project_name}_speech.wav"

    def output_video_path(self) -> Path:
        return self.output_dir / f"{self.project_name}_avatar.mp4"

    def subtitles_path(self) -> Path:
        return self.output_dir / f"{self.project_name}.srt"
