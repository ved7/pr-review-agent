from __future__ import annotations

import json
from typing import Any, Dict

from loguru import logger

from app.celery_app import celery_app
from app.schemas import AnalysisResult
from app.services.cache import build_cache_key, get_redis
from app.services.github import PRData, fetch_pr_data
from app.agent.reviewer import analyze_pr_with_agent
from app.config import settings

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial


@celery_app.task(bind=True, name="analyze_pr_task")
def analyze_pr_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    repo_url = str(payload["repo_url"])
    pr_number = int(payload["pr_number"])
    github_token = payload.get("github_token")
    skip_cache = bool(payload.get("force", False))

    logger.info(f"Starting PR analysis for {repo_url} PR #{pr_number}")
    self.update_state(state="PROCESSING", meta={"stage": "fetching_pr_data"})

    try:
        pr_data = asyncio.run(fetch_pr_data(repo_url, pr_number, github_token))
        logger.info(f"Got PR data for {repo_url}#{pr_number}")
    except Exception as e:
        logger.error(f"Failed to fetch PR data: {e}")
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise

    cache_key = build_cache_key(repo_url, pr_number, pr_data.head_sha)
    redis_client = get_redis()

    if not skip_cache:
        cached_result = redis_client.get(cache_key)
        if cached_result:
            logger.info("Found cached result, using that")
            return json.loads(cached_result)
        logger.info("No cache found, doing fresh analysis")

    self.update_state(state="PROCESSING", meta={"stage": "ai_code_review"})
    logger.info("Starting AI code analysis...")

    try:
        analysis_result = asyncio.run(analyze_pr_with_agent(pr_data))
        result_dict = analysis_result.model_dump()
        logger.info("AI analysis done")
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        
        result_dict = {
            "repo_url": repo_url,
            "pr_number": pr_number,
            "head_sha": pr_data.head_sha,
            "issues": [],
            "summary": f"Analysis failed: {str(e)}. Try again or check logs.",
            "model_info": {"provider": "fallback", "error": str(e)}
        }
        logger.info("Using fallback result")

    try:
        redis_client.setex(cache_key, settings.cache_ttl_seconds, json.dumps(result_dict))
        logger.info("Results cached")
    except Exception as e:
        logger.warning(f"Couldn't cache results: {e}")

    logger.info(f"PR analysis finished for {repo_url}#{pr_number}")
    return result_dict
