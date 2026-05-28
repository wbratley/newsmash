import json
import logging
import os
from datetime import date, datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Auto-detect Lambda environment; can be overridden with CACHE_BACKEND=dynamo|filesystem
_CACHE_BACKEND = os.environ.get(
    "CACHE_BACKEND",
    "dynamo" if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") else "filesystem",
)

_CACHE_DIR = Path(".cache")
_dynamo_resource = None


def _dynamo():
    global _dynamo_resource
    if _dynamo_resource is None:
        import boto3
        _dynamo_resource = boto3.resource("dynamodb")
    return _dynamo_resource


def _table_name() -> str:
    from app.config import settings
    return settings.cache_table_name


def _pk(key: str) -> str:
    return f"{date.today().isoformat()}_{key}"


def _dynamo_load(key: str) -> dict | None:
    table = _dynamo().Table(_table_name())
    resp = table.get_item(Key={"pk": _pk(key)})
    item = resp.get("Item")
    if not item:
        return None
    return json.loads(item["data"])


def _dynamo_save(key: str, data: dict) -> None:
    table = _dynamo().Table(_table_name())
    ttl = int(datetime.now(timezone.utc).timestamp()) + 2 * 86400  # 2 days
    table.put_item(Item={"pk": _pk(key), "data": json.dumps(data), "ttl": ttl})


def _fs_path(key: str) -> Path:
    _CACHE_DIR.mkdir(exist_ok=True)
    return _CACHE_DIR / f"{date.today().isoformat()}_{key}.json"


def load_today(key: str) -> dict | None:
    try:
        if _CACHE_BACKEND == "dynamo":
            return _dynamo_load(key)
        path = _fs_path(key)
        return json.loads(path.read_text()) if path.exists() else None
    except Exception as exc:
        logger.warning("Cache read failed (%s): %s", key, exc)
        return None


def save_today(key: str, data: dict) -> None:
    try:
        if _CACHE_BACKEND == "dynamo":
            _dynamo_save(key, data)
        else:
            _fs_path(key).write_text(json.dumps(data))
        logger.info("Cached response under key '%s'", key)
    except Exception as exc:
        logger.warning("Cache write failed (%s): %s", key, exc)
