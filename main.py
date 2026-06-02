from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api.routes import router as api_router
from core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include API routes
app.include_router(api_router)

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)