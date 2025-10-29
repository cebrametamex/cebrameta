"""CLI principal para ejecutar el pipeline de generación."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from .config import GenerationConfig, VoiceProfile
from .pipeline import AvatarGenerationPipeline

app = typer.Typer(help="Generador de avatares hablantes estilo Hagen.")


@app.command()
def list_voices() -> None:
    """Lista las voces mexicanas sugeridas para Edge TTS."""

    voices = _default_voice_catalog()
    typer.echo(json.dumps([voice.to_dict() for voice in voices], indent=2, ensure_ascii=False))


@app.command()
def run(
    image: Path = typer.Argument(..., help="Ruta a la imagen base del avatar."),
    text: Path = typer.Argument(..., help="Archivo de texto con el guion."),
    voice: str = typer.Option("institucional_grave_1", help="Identificador del perfil de voz."),
    output: Path = typer.Option(Path("outputs"), help="Carpeta de salida."),
    project: str = typer.Option("avatar", help="Nombre del proyecto."),
    lipsync: str = typer.Option("sadtalker", help="Motor de lip-sync a utilizar."),
    fps: int = typer.Option(25, help="FPS del video final."),
    env_file: Optional[Path] = typer.Option(None, help="Ruta opcional a archivo .env"),
    keep_intermediate: bool = typer.Option(False, help="Conservar archivos temporales."),
    lipsync_extra_arg: list[str] = typer.Option(  # type: ignore[assignment]
        [],
        "--lipsync-extra-arg",
        help="Argumentos adicionales para el motor de lip-sync (puede usarse varias veces).",
    ),
) -> None:
    """Ejecuta el pipeline completo de generación."""

    text_content = text.read_text(encoding="utf-8")
    voice_profile = _resolve_voice(voice)
    config = GenerationConfig(
        image_path=image,
        script_text=text_content,
        output_dir=output,
        project_name=project,
        voice=voice_profile,
        lipsync_engine=lipsync,
        fps=fps,
        environment_file=env_file,
        keep_intermediate=keep_intermediate,
        lipsync_extra_args=list(lipsync_extra_arg),
    )

    pipeline = AvatarGenerationPipeline(config)
    artifacts = pipeline.run()

    typer.echo("Pipeline finalizado exitosamente.")
    typer.echo(json.dumps({
        "audio": str(artifacts.audio),
        "video": str(artifacts.video),
        "subtitles": str(artifacts.subtitles) if artifacts.subtitles else None,
    }, indent=2, ensure_ascii=False))


def _default_voice_catalog() -> list[VoiceProfile]:
    """Catálogo mínimo de voces mexicanas institucionales en Edge TTS."""

    return [
        VoiceProfile(
            name="institucional_grave_1",
            display_name="Miguel (es-MX, grave, institucional)",
            locale="es-MX",
            voice_id="es-MX-RogelioNeural",
            description="Voz masculina grave con tono institucional.",
            style="newscast",
            rate=0.0,
            pitch=-2.0,
        ),
        VoiceProfile(
            name="institucional_grave_2",
            display_name="Sofía (es-MX, formal)",
            locale="es-MX",
            voice_id="es-MX-DaliaNeural",
            description="Voz femenina con registro serio y neutro.",
            style="customerservice",
            rate=-0.05,
            pitch=-1.0,
        ),
    ]


def _resolve_voice(name: str) -> VoiceProfile:
    voices = {voice.name: voice for voice in _default_voice_catalog()}
    if name not in voices:
        raise typer.BadParameter(f"Voz '{name}' no encontrada. Ejecuta 'cebrameta-avatar list-voices'.")
    return voices[name]
