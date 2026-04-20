from __future__ import annotations

import os
from pathlib import Path


def load_local_env(path: str = ".env") -> None:
    """Carrega .env local sem sobrescrever as variáveis ​​de ambiente existentes do processo."""

    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        normalized_key = key.strip()
        normalized_value = value.strip().strip('"').strip("'")
        if not normalized_key or normalized_key in os.environ:
            continue
        os.environ[normalized_key] = normalized_value
