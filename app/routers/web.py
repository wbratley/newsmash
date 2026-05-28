from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.digest import get_or_generate

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    data = await get_or_generate()
    return templates.TemplateResponse(
        request, "index.html", {"data": data, "generated_at": data["generated_at"][:10]}
    )


@router.get("/story/{cluster_id}", response_class=HTMLResponse)
async def story(request: Request, cluster_id: str):
    data = await get_or_generate()
    cluster = next((c for c in data["clusters"] if c["id"] == cluster_id), None)
    return templates.TemplateResponse(
        request, "story.html", {"cluster": cluster, "generated_at": data["generated_at"][:10]}
    )
