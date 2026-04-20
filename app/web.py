from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(include_in_schema=False)

INDEX_FILE = Path(__file__).resolve().parent / "static" / "index.html"


@router.get("/")
def frontend() -> FileResponse:
    return FileResponse(INDEX_FILE)
