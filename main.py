import uvicorn

from app.models.settings import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
