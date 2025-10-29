# Cebrameta Avatar Pipeline

Este proyecto implementa un flujo reproducible para generar avatares hablantes a partir de una imagen fija y un guion de texto, inspirado en la experiencia de Hagen. El código está diseñado para ser extensible y permitir el intercambio de motores de síntesis de voz y lip-sync.

## Características

- 🎤 **Síntesis de voz** usando Microsoft Edge TTS con voces mexicanas graves y tono institucional.
- 🧠 **Orquestación completa** del pipeline: generación de audio, animación facial y render final.
- 🧩 **Componentes modulares** para reemplazar fácilmente motores de TTS o lip-sync.
- 📄 **Manifiesto JSON** con metadatos de cada ejecución y subtítulos opcionales en formato SRT.
- 🛠️ **CLI basada en Typer** para ejecutar el flujo desde la terminal.

## Requisitos

- Python 3.9 o superior.
- Dependencias del sistema para los motores elegidos (GPU recomendada para SadTalker o Wav2Lip).
- `ffmpeg` disponible en el sistema para tareas de combinación de audio/video (dependiendo del motor seleccionado).
- Acceso a Internet para el motor Edge TTS.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Uso rápido

1. Prepara una imagen frontal limpia (`imagen.jpg`).
2. Crea un archivo de guion (`guion.txt`) con el texto que el avatar debe decir.
3. Ejecuta el pipeline:

```bash
cebrameta-avatar run imagen.jpg guion.txt \
  --voice institucional_grave_1 \
  --output ./outputs \
  --project demo_hagen \
  --lipsync sadtalker
```

Al finalizar, encontrarás el audio, el video generado y el manifiesto en la carpeta `outputs/`.

## Voces mexicanas incluidas

Consulta las voces configuradas ejecutando:

```bash
cebrameta-avatar list-voices
```

Esto mostrará perfiles basados en Microsoft Edge TTS ajustados con entonación grave e institucional.

## Integración con SadTalker

El motor por defecto es SadTalker. Debes tener disponible el comando `sadtalker` en tu entorno. Una instalación típica se realiza clonando el repositorio oficial y ejecutando sus scripts de instalación. Luego puedes añadir parámetros adicionales con `--lipsync-extra-arg` (puedes repetir la opción varias veces) o extendiendo el CLI.

## Extender el proyecto

- **Nuevos motores TTS:** Implementa una subclase de `TTSEngine` en `avatar_pipeline/audio.py` y actualiza `build_tts_engine`.
- **Otros motores de lip-sync:** Añade una subclase de `LipSyncEngine` en `avatar_pipeline/lipsync.py` y extiende `build_lipsync_engine`.
- **Interfaces web o colas de procesamiento:** Usa el pipeline programáticamente desde `AvatarGenerationPipeline` para integrarlo en servicios mayores.

## Advertencias éticas

Asegúrate de contar con permisos sobre la imagen y el audio generados. Respeta las regulaciones de privacidad y los derechos de autor, y comunica a los usuarios cuando interactúan con contenido sintético.
