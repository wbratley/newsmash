import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import settings
from app.schemas import NewsResponse
from app.services.cache import load_today, save_today
from app.services.clustering import cluster_stories
from app.services.rss import fetch_all_feeds
from app.services.synthesis import synthesise_cluster

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/news", tags=["news"])

_CACHE_KEY = "news"


@router.get("/today", response_model=NewsResponse, summary="Get today's news synthesised from all sources")
async def get_today() -> NewsResponse:
    cached = load_today(_CACHE_KEY)
    if cached:
        logger.info("Serving today's news from cache")
        return NewsResponse.model_validate(cached)

    stories = await fetch_all_feeds()
    clusters = cluster_stories(stories)[: settings.max_clusters]

    synthesised = await asyncio.gather(
        *[synthesise_cluster(f"cluster-{i}", cluster) for i, cluster in enumerate(clusters)]
    )

    result = NewsResponse(
        generated_at=datetime.now(timezone.utc),
        cluster_count=len(synthesised),
        clusters=list(synthesised),
    )
    save_today(_CACHE_KEY, result.model_dump(mode="json"))
    return result
