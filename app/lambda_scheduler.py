"""
Daily digest pre-generation handler, invoked by EventBridge cron.
Runs outside the 29-second API Gateway timeout window.
"""
import asyncio
import logging

logger = logging.getLogger(__name__)


def handler(event, context):
    from app.services.digest import get_or_generate
    logger.info("Scheduler: generating daily digest")
    result = asyncio.run(get_or_generate())
    count = result.get("cluster_count", 0)
    logger.info("Scheduler: cached %d clusters", count)
    return {"statusCode": 200, "cluster_count": count}
