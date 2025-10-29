"""Paquete principal para la generación de avatares hablantes."""

from __future__ import annotations

from .config import GenerationConfig, VoiceProfile

__all__ = ["GenerationConfig", "VoiceProfile", "AvatarGenerationPipeline"]


def __getattr__(name: str):  # pragma: no cover - importación diferida
    if name == "AvatarGenerationPipeline":
        from .pipeline import AvatarGenerationPipeline

        return AvatarGenerationPipeline
    raise AttributeError(name)
