from datetime import datetime
from pydantic import BaseModel


class Source(BaseModel):
    outlet: str
    lean: str
    headline: str
    url: str
    published: str | None = None


class Sentiment(BaseModel):
    left: float
    centre: float
    right: float


class Cluster(BaseModel):
    id: str
    neutral_headline: str
    narrative: str
    sentiment: Sentiment
    sources: list[Source]


class NewsResponse(BaseModel):
    generated_at: datetime
    cluster_count: int
    clusters: list[Cluster]
