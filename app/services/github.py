from __future__ import annotations

import base64
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx
from loguru import logger

from app.config import settings

# Thread pool for CPU-intensive operations
_file_processing_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="github_file_processor")


def _process_file_info_threaded(file_data: Dict[str, Any]) -> 'PRFile':
    """Process file information in a separate thread for better performance"""
    from app.services.github import PRFile
    
    return PRFile(
        filename=file_data.get("filename"),
        status=file_data.get("status"),
        additions=file_data.get("additions", 0),
        deletions=file_data.get("deletions", 0),
        changes=file_data.get("changes", 0),
        patch=file_data.get("patch"),
        raw_url=file_data.get("raw_url"),
    )


async def _process_files_concurrently(files_data: List[Dict[str, Any]]) -> List['PRFile']:
    """Process multiple files concurrently using thread pool"""
    import asyncio
    
    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(_file_processing_pool, _process_file_info_threaded, file_data)
        for file_data in files_data
    ]
    
    return await asyncio.gather(*tasks)


@dataclass
class PRFile:
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: Optional[str]
    raw_url: Optional[str]


@dataclass
class PRData:
    owner: str
    repo: str
    number: int
    title: str
    body: Optional[str]
    head_sha: str
    base_sha: str
    files: List[PRFile]
    diff: str


def _headers(token: Optional[str]) -> dict[str, str]:
    hdrs = {"Accept": "application/vnd.github+json"}
    auth_token = token or settings.github_token_default
    if auth_token:
        hdrs["Authorization"] = f"Bearer {auth_token}"
    return hdrs


def _parse_repo_url(repo_url: str) -> Tuple[str, str]:
    parsed = urlparse(repo_url)
    path = parsed.path.strip("/")
    if not path or len(path.split("/")) < 2:
        raise ValueError("Invalid repo_url; expected https://github.com/<owner>/<repo>")
    owner, repo = path.split("/")[:2]
    repo = re.sub(r"\.git$", "", repo)
    return owner, repo


async def fetch_pr_data(repo_url: str, pr_number: int, github_token: Optional[str]) -> PRData:
    owner, repo_name = _parse_repo_url(repo_url)
    api_base = f"https://api.github.com/repos/{owner}/{repo_name}"
    
    logger.info(f"Fetching PR #{pr_number} from {owner}/{repo_name}")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            pr_response = await client.get(f"{api_base}/pulls/{pr_number}", headers=_headers(github_token))
            
            if pr_response.status_code == 404:
                raise ValueError(f"PR #{pr_number} doesn't exist in {owner}/{repo_name}")
            elif pr_response.status_code == 401:
                raise ValueError("GitHub auth failed, check your token")
            elif pr_response.status_code == 403:
                raise ValueError("Access denied or rate limited, try using a token")
            elif pr_response.status_code != 200:
                raise ValueError(f"GitHub API error {pr_response.status_code}: {pr_response.text}")
                
            pr_response.raise_for_status()
            pr_data = pr_response.json()
            
            head_sha = pr_data["head"]["sha"]
            base_sha = pr_data["base"]["sha"]
            title = pr_data.get("title", "")
            body = pr_data.get("body")

            files_response = await client.get(f"{api_base}/pulls/{pr_number}/files", headers=_headers(github_token))
            if files_response.status_code != 200:
                raise ValueError(f"Couldn't get PR files: {files_response.status_code}")
            files_response.raise_for_status()
            
            files_json = files_response.json()
            pr_files = await _process_files_concurrently(files_json)

            diff_headers = _headers(github_token)
            diff_headers["Accept"] = "application/vnd.github.v3.diff"
            
            diff_response = await client.get(f"{api_base}/pulls/{pr_number}", headers=diff_headers)
            if diff_response.status_code != 200:
                raise ValueError(f"Couldn't get PR diff: {diff_response.status_code}")
            diff_response.raise_for_status()
            
            diff_text = diff_response.text

        logger.info(f"Got PR data: {len(pr_files)} files changed")
        
        return PRData(
            owner=owner,
            repo=repo_name,
            number=pr_number,
            title=title,
            body=body,
            head_sha=head_sha,
            base_sha=base_sha,
            files=pr_files,
            diff=diff_text,
        )
        
    except httpx.TimeoutException:
        raise ValueError("GitHub API timed out, try again later")
    except httpx.RequestError as e:
        raise ValueError(f"Network error: {e}")
    except Exception as e:
        error_text = str(e).lower()
        if "rate limit" in error_text:
            raise ValueError("GitHub rate limited, wait a bit or use a token")
        elif "not found" in error_text:
            raise ValueError(f"Repo {owner}/{repo_name} not found or no access")
        else:
            raise


def fetch_file_content(repo_url: str, ref: str, path: str, github_token: Optional[str]) -> Optional[str]:
    owner, repo = _parse_repo_url(repo_url)
    base_api = f"https://api.github.com/repos/{owner}/{repo}"
    with httpx.Client(timeout=30) as client:
        resp = client.get(
            f"{base_api}/contents/{path}",
            params={"ref": ref},
            headers=_headers(github_token),
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and data.get("encoding") == "base64":
            import base64 as _b64
            return _b64.b64decode(data.get("content", "")).decode("utf-8", errors="ignore")
        return None
