from __future__ import annotations

from typing import Optional

from redis import Redis

from app.config import settings


def get_redis() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


def build_cache_key(repo_url: str, pr_number: int, head_sha: Optional[str]) -> str:
    suffix = head_sha or "no-sha"
    return f"prreview:{repo_url}:{pr_number}:{suffix}"
