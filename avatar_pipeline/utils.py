"""Funciones utilitarias para el pipeline."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional


def load_environment_file(env_path: Optional[Path]) -> None:
    """Carga variables de entorno desde un archivo .env si existe."""

    if env_path is None:
        return
    env_path = env_path.expanduser().resolve()
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def ensure_paths_exist(paths: Iterable[Path]) -> None:
    """Garantiza que las carpetas padre de las rutas existan."""

    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    """Obtiene una variable de entorno con fallback."""

    return os.environ.get(name, default)
