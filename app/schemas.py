from __future__ import annotations

from typing import Any, Literal

from pydantic import AnyUrl, BaseModel, Field


class AnalyzePRRequest(BaseModel):
    repo_url: AnyUrl = Field(..., description="GitHub repository URL")
    pr_number: int = Field(..., ge=1)
    github_token: str | None = Field(default=None, description="Optional token to increase rate limits")
    force: bool = Field(default=False, description="Force re-analysis ignoring cache")


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result_ready: bool = False
    error: str | None = None


class AnalysisIssue(BaseModel):
    file_path: str
    line: int | None = None
    severity: Literal["info", "warning", "error"]
    category: Literal["style", "bug", "performance", "best_practice"]
    message: str
    suggestion: str | None = None


class AnalysisResult(BaseModel):
    repo_url: str  # Changed from AnyUrl to str for Celery compatibility
    pr_number: int
    head_sha: str | None = None
    issues: list[AnalysisIssue]
    summary: str
    model_info: dict[str, Any] = {}
