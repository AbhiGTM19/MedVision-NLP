from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api.routes import router as api_router
from core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, docs_url=None)

# Paths to the frontend directory
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

# Mount static files
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")

# Templates
templates = Jinja2Templates(directory=str(FRONTEND_DIR / "templates"))

# Include API routes
app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/metrics", response_class=HTMLResponse)
def metrics(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="metrics.html")

@app.get("/chat-ui", response_class=HTMLResponse)
def chat_ui(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="chat.html")

@app.get("/monitoring", response_class=HTMLResponse)
def monitoring(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="monitoring.html")

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html(request: Request):
    return templates.TemplateResponse(request=request, name="docs.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)