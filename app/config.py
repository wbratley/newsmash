import logging

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str = ""
    # On Lambda, set this to the Secrets Manager ARN; the key is fetched at startup.
    anthropic_api_key_secret_arn: str = ""
    cache_table_name: str = "newsmash-cache"
    max_clusters: int = 10
    cluster_similarity_threshold: float = 0.25
    feed_timeout_seconds: int = 10


def _resolve_settings() -> Settings:
    s = Settings()
    if not s.anthropic_api_key and s.anthropic_api_key_secret_arn:
        try:
            import boto3
            client = boto3.client("secretsmanager")
            resp = client.get_secret_value(SecretId=s.anthropic_api_key_secret_arn)
            s = s.model_copy(update={"anthropic_api_key": resp["SecretString"]})
            logger.info("Loaded API key from Secrets Manager")
        except Exception as exc:
            logger.warning("Could not fetch API key from Secrets Manager: %s", exc)
    return s


settings = _resolve_settings()

SOURCES: list[dict] = [
    {
        "outlet": "The Guardian",
        "lean": "left",
        "feed_url": "https://www.theguardian.com/uk/rss",
    },
    {
        "outlet": "BBC News",
        "lean": "centre-left",
        "feed_url": "http://feeds.bbci.co.uk/news/rss.xml",
    },
    {
        "outlet": "The Independent",
        "lean": "centre-left",
        "feed_url": "https://www.independent.co.uk/news/uk/rss",
    },
    {
        "outlet": "Reuters UK",
        "lean": "centre",
        "feed_url": "https://feeds.reuters.com/reuters/UKNews",
    },
    {
        "outlet": "i Paper",
        "lean": "centre",
        "feed_url": "https://inews.co.uk/feed",
    },
    {
        "outlet": "The Times",
        "lean": "centre-right",
        "feed_url": "https://www.thetimes.co.uk/feed/uk-news/",
    },
    {
        "outlet": "The Telegraph",
        "lean": "centre-right",
        "feed_url": "https://www.telegraph.co.uk/rss.xml",
    },
    {
        "outlet": "Daily Mail",
        "lean": "right",
        "feed_url": "https://www.dailymail.co.uk/articles.rss",
    },
    {
        "outlet": "Daily Express",
        "lean": "right",
        "feed_url": "https://www.express.co.uk/posts/rss/1/news",
    },
    {
        "outlet": "The Spectator",
        "lean": "right",
        "feed_url": "https://www.spectator.co.uk/feed",
    },
]
