from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from gotinha.api import health
from gotinha.api.templates import BASE_DIR, templates

app = FastAPI(title='Gotinha')
app.mount('/static', StaticFiles(directory=BASE_DIR / 'static'), name='static')
app.include_router(health.router)


@app.get('/', response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, 'home.html')
