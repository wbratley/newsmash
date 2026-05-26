from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.cache import load_today

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    data = load_today("news")
    generated_at = data["generated_at"][:10] if data else None
    return templates.TemplateResponse(request, "index.html", {"data": data, "generated_at": generated_at})


@router.get("/story/{cluster_id}", response_class=HTMLResponse)
async def story(request: Request, cluster_id: str):
    data = load_today("news")
    cluster = None
    if data:
        cluster = next((c for c in data["clusters"] if c["id"] == cluster_id), None)
    generated_at = data["generated_at"][:10] if data else None
    return templates.TemplateResponse(request, "story.html", {"cluster": cluster, "generated_at": generated_at})
