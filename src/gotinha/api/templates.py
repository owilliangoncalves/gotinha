"""Configuração do Jinja2."""

from datetime import datetime
from pathlib import Path

from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(directory=BASE_DIR / 'templates')


def strftime(value: str, fmt: str | None = None) -> str:
    """Formata o instante atual; aceita `'%H:%M' | strftime` e `'%s' | strftime('%Y')`."""
    return datetime.now().strftime(fmt or value)


templates.env.filters['strftime'] = strftime
