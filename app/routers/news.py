from fastapi import APIRouter

from app.schemas import NewsResponse
from app.services.digest import get_or_generate

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/today", response_model=NewsResponse, summary="Get today's news synthesised from all sources")
async def get_today() -> NewsResponse:
    return NewsResponse.model_validate(await get_or_generate())
