import json
import logging

from anthropic import AsyncAnthropic

from app.config import settings
from app.schemas import Cluster, Sentiment, Source
from app.services.rss import RawStory

logger = logging.getLogger(__name__)

_client: AsyncAnthropic | None = None


def get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


def _build_prompt(cluster: list[RawStory]) -> str:
    lines = []
    for story in cluster:
        snippet = story["summary"][:200] if story["summary"] else "(no summary)"
        lines.append(f"[{story['lean'].upper()}] {story['outlet']}: {story['title']} — {snippet}")
    sources_block = "\n".join(lines)
    return f"""You are a neutral news analyst. Below are headlines and summaries for the same news story, reported by UK outlets with different political leanings.

{sources_block}

Return ONLY valid JSON with this exact shape — no markdown, no extra text:
{{
  "neutral_headline": "<bias-free headline under 30 words>",
  "narrative": "<balanced 100-150 word summary covering all angles>",
  "sentiment": {{"left": <float>, "centre": <float>, "right": <float>}}
}}

The three sentiment floats must sum to 1.0 and reflect the overall tilt of coverage in this cluster."""


def _fallback_cluster(cluster_id: str, stories: list[RawStory]) -> Cluster:
    """Return a minimal cluster when Claude synthesis fails."""
    return Cluster(
        id=cluster_id,
        neutral_headline=stories[0]["title"] if stories else "Unknown story",
        narrative="Synthesis unavailable.",
        sentiment=Sentiment(left=0.33, centre=0.34, right=0.33),
        sources=[
            Source(
                outlet=s["outlet"],
                lean=s["lean"],
                headline=s["title"],
                url=s["url"],
                published=s["published"],
            )
            for s in stories
        ],
    )


async def synthesise_cluster(cluster_id: str, stories: list[RawStory]) -> Cluster:
    sources = [
        Source(
            outlet=s["outlet"],
            lean=s["lean"],
            headline=s["title"],
            url=s["url"],
            published=s["published"],
        )
        for s in stories
    ]

    try:
        response = await get_client().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": _build_prompt(stories)}],
        )
        raw = response.content[0].text.strip()

        # Strip accidental markdown fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        data = json.loads(raw)
        sentiment_data = data.get("sentiment", {})

        # Normalise sentiment so it always sums to 1.0
        left = float(sentiment_data.get("left", 0.33))
        centre = float(sentiment_data.get("centre", 0.34))
        right = float(sentiment_data.get("right", 0.33))
        total = left + centre + right
        if total > 0:
            left, centre, right = left / total, centre / total, right / total

        return Cluster(
            id=cluster_id,
            neutral_headline=data.get("neutral_headline", stories[0]["title"]),
            narrative=data.get("narrative", ""),
            sentiment=Sentiment(left=round(left, 3), centre=round(centre, 3), right=round(right, 3)),
            sources=sources,
        )

    except Exception as exc:
        logger.warning("Synthesis failed for cluster %s: %s", cluster_id, exc)
        return _fallback_cluster(cluster_id, stories)
