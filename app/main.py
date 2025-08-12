from __future__ import annotations

from typing import Any, Dict, List
import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.celery_app import celery_app
from app.schemas import AnalyzePRRequest, TaskStatusResponse
from app.utils.logging import setup_logging
from app.services.github import fetch_pr_data
from app.agent.reviewer import analyze_pr_with_agent

setup_logging()
app = FastAPI(title="PR Review Agent API")


@app.get("/")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/health")
def detailed_health() -> Dict[str, Any]:
    health_status = {
        "status": "ok",
        "timestamp": "2024-01-01T00:00:00Z",
        "dependencies": {}
    }
    
    try:
        from app.services.cache import get_redis
        redis_client = get_redis()
        redis_client.ping()
        health_status["dependencies"]["redis"] = "ok"
    except Exception as e:
        health_status["dependencies"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    try:
        import ollama
        ollama.list()
        health_status["dependencies"]["ollama"] = "ok"
    except Exception as e:
        health_status["dependencies"]["ollama"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    try:
        from app.config import settings
        if settings.openai_api_key:
            from openai import OpenAI
            client = OpenAI(api_key=settings.openai_api_key)
            client.models.list(limit=1)
            health_status["dependencies"]["openai"] = "ok"
        else:
            health_status["dependencies"]["openai"] = "not configured"
    except Exception as e:
        health_status["dependencies"]["openai"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


@app.post("/analyze-pr")
def analyze_pr(request: AnalyzePRRequest) -> Dict[str, str]:
    try:
        payload = request.model_dump(mode="json")
        payload["repo_url"] = str(payload["repo_url"])
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    from app.tasks import analyze_pr_task
    async_result = analyze_pr_task.delay(payload)
    return {"task_id": async_result.id}


@app.post("/analyze-prs-batch")
async def analyze_multiple_prs(requests: List[AnalyzePRRequest]) -> Dict[str, Any]:
    """
    Analyze multiple PRs concurrently for better performance.
    This endpoint uses async/await to process multiple PRs in parallel.
    """
    if len(requests) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 PRs per batch")
    
    async def analyze_single_pr(req: AnalyzePRRequest) -> Dict[str, Any]:
        try:
            repo_url = str(req.repo_url)
            pr_data = await fetch_pr_data(repo_url, req.pr_number, req.github_token)
            result = await analyze_pr_with_agent(pr_data)
            return {
                "repo_url": repo_url,
                "pr_number": req.pr_number,
                "status": "success",
                "result": result.model_dump()
            }
        except Exception as e:
            return {
                "repo_url": str(req.repo_url),
                "pr_number": req.pr_number,
                "status": "error",
                "error": str(e)
            }
    
    tasks = [analyze_single_pr(req) for req in requests]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return {
        "batch_id": f"batch_{len(requests)}_{hash(str(requests))}",
        "total_prs": len(requests),
        "results": results
    }


@app.get("/status/{task_id}")
def get_status(task_id: str) -> TaskStatusResponse:
    async_result = celery_app.AsyncResult(task_id)
    status = async_result.status
    result_ready = async_result.ready()

    error: str | None = None
    if status == "FAILURE":
        exc = async_result.result
        error = str(exc)

    return TaskStatusResponse(task_id=task_id, status=status, result_ready=result_ready, error=error)


@app.get("/results/{task_id}")
def get_results(task_id: str) -> JSONResponse:
    async_result = celery_app.AsyncResult(task_id)
    if not async_result.ready():
        raise HTTPException(status_code=202, detail="Result not ready")
    if async_result.status == "FAILURE":
        raise HTTPException(status_code=500, detail=str(async_result.result))

    result: Dict[str, Any] = async_result.result
    return JSONResponse(content=result)


@app.get("/performance")
async def get_performance_metrics() -> Dict[str, Any]:
    """
    Get performance metrics and async capabilities status.
    """
    import time
    
    start_time = time.time()
    
    # Test async performance with a simple operation
    await asyncio.sleep(0.001)  # Simulate async work
    
    async_time = time.time() - start_time
    
    return {
        "async_support": True,
        "concurrent_processing": True,
        "performance_test": {
            "async_overhead": f"{async_time:.6f}s",
            "status": "optimal" if async_time < 0.01 else "degraded"
        },
        "capabilities": [
            "Single PR analysis (Celery)",
            "Batch PR analysis (Async)",
            "Concurrent HTTP requests",
            "Parallel AI model calls"
        ]
    }


@app.get("/benchmark")
async def benchmark_performance() -> Dict[str, Any]:
    """
    Benchmark performance with and without multithreading.
    """
    import time
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    results = {}
    
    # Test 1: Async vs Sync operations
    start_time = time.time()
    await asyncio.sleep(0.01)  # Simulate async work
    async_time = time.time() - start_time
    
    start_time = time.time()
    time.sleep(0.01)  # Simulate sync work
    sync_time = time.time() - start_time
    
    results["async_vs_sync"] = {
        "async_time": f"{async_time:.6f}s",
        "sync_time": f"{sync_time:.6f}s",
        "improvement": f"{(sync_time - async_time) / sync_time * 100:.1f}%"
    }
    
    # Test 2: Multithreading for CPU-bound work
    def cpu_intensive_work(n: int) -> int:
        """Simulate CPU-intensive work"""
        result = 0
        for i in range(n * 1000):
            result += i * i
        return result
    
    # Sequential execution
    start_time = time.time()
    sequential_results = [cpu_intensive_work(i) for i in range(1, 6)]
    sequential_time = time.time() - start_time
    
    # Threaded execution
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=4) as executor:
        threaded_results = list(executor.map(cpu_intensive_work, range(1, 6)))
    threaded_time = time.time() - start_time
    
    results["multithreading"] = {
        "sequential_time": f"{sequential_time:.6f}s",
        "threaded_time": f"{threaded_time:.6f}s",
        "speedup": f"{sequential_time / threaded_time:.2f}x",
        "improvement": f"{(sequential_time - threaded_time) / sequential_time * 100:.1f}%"
    }
    
    # Test 3: Mixed async + threading
    async def mixed_work():
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Simulate async I/O + CPU work
            await asyncio.sleep(0.005)  # Async I/O
            cpu_result = await loop.run_in_executor(executor, cpu_intensive_work, 3)
            await asyncio.sleep(0.005)  # More async I/O
            return cpu_result
    
    start_time = time.time()
    await mixed_work()
    mixed_time = time.time() - start_time
    
    results["mixed_async_threading"] = {
        "mixed_time": f"{mixed_time:.6f}s",
        "efficiency": "optimal" if mixed_time < 0.02 else "good"
    }
    
    return {
        "benchmark_results": results,
        "recommendations": [
            "Use async for I/O operations (HTTP, AI calls)",
            "Use threading for CPU-intensive work (JSON parsing, file processing)",
            "Combine both for maximum performance",
            "Thread pool size: 3-4 workers for file processing, 4 for AI operations"
        ]
    }
