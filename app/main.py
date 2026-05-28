import logging
import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.routers import news, web

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s – %(message)s",
)

app = FastAPI(
    title="Newshash",
    description="Aggregates UK news RSS feeds across the political spectrum and synthesises balanced, unbiased story clusters using AI.",
    version="0.1.0",
)

app.include_router(web.router)
app.include_router(news.router)


@app.get("/health", tags=["meta"])
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


# Lambda handler — only wired up when running inside AWS Lambda.
if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
