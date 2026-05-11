import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.routers import news

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s – %(message)s",
)

app = FastAPI(
    title="Newsmash",
    description="Aggregates UK news RSS feeds across the political spectrum and synthesises balanced, unbiased story clusters using AI.",
    version="0.1.0",
)

app.include_router(news.router)


@app.get("/health", tags=["meta"])
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})
