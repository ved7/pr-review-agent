from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import json
import re
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel

from app.config import settings
from app.schemas import AnalysisIssue, AnalysisResult
from app.services.github import PRData

# Global thread pool for CPU-intensive operations
_thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ai_agent")


try:
    import ollama 
except Exception:  
    ollama = None  

try:
    from openai import OpenAI  
except Exception:  
    OpenAI = None  


JSON_SCHEMA_INSTRUCTIONS = (
    "Return a strict JSON object with keys: summary (string), issues (array of issue objects). "
    "Each issue object must have: file_path (string), line (number or null), severity (info|warning|error), "
    "category (style|bug|performance|best_practice), message (string), suggestion (string or null). "
    "Do not include any extra commentary, only JSON."
)


def _build_prompt_threaded(pr: PRData) -> List[Dict[str, str]]:
    """CPU-intensive prompt building in a separate thread"""
    user = f"""
You're a senior software developer with high years of experience in writing code analysing and reviewing it, doing a code review. Look at this PR and tell us:

. Analyse the code changes in depth , review them check if they are good to merge or not
. If they are good to merge, recommend the best possible way to do it , consider the test cases, code coverage, performance, security, and best practices
. If they are not good to merge, recommend the best possible way to fix them
. What's good about the changes
. Any issues (bugs, style, performance, best practices)
. Overall assessment

PR Details:
- Repository: {pr.owner}/{pr.repo}
- PR #{pr.number}: {pr.title}
- Files changed: {len(pr.files)}
- Total changes: +{sum(f.additions for f in pr.files)} -{sum(f.deletions for f in pr.files)}

Files and Changes:
"""
    
    for file_info in pr.files:
        user += f"\nFile: {file_info.filename}\n"
        user += f"Status: {file_info.status}\n"
        user += f"Changes: +{file_info.additions} -{file_info.deletions}\n"
        if file_info.patch:
            user += f"Diff:\n{file_info.patch}\n"
        user += "-" * 50 + "\n"

    user += "\nPlease provide a detailed code review with specific issues and suggestions."

    return [
        {"role": "system", "content": "You are an expert code reviewer. Provide detailed, actionable feedback."},
        {"role": "user", "content": user}
    ]


def _parse_json_threaded(content: str) -> Dict[str, Any]:
    """CPU-intensive JSON parsing in a separate thread"""
    try:
        # Try to extract JSON from markdown if present
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        
        # Clean up common LLM response artifacts
        content = content.strip()
        if content.startswith('```') and content.endswith('```'):
            content = content[3:-3].strip()
        
        return json.loads(content)
    except json.JSONDecodeError:
        # Fallback: try to extract key-value pairs
        result = {"summary": content, "issues": []}
        
        # Look for issue patterns
        issues = []
        lines = content.split('\n')
        current_issue = {}
        
        for line in lines:
            line = line.strip()
            if 'file:' in line.lower() or 'filename:' in line.lower():
                if current_issue:
                    issues.append(current_issue)
                current_issue = {'file_path': line.split(':')[-1].strip()}
            elif 'line:' in line.lower():
                try:
                    current_issue['line'] = int(line.split(':')[-1].strip())
                except ValueError:
                    current_issue['line'] = None
            elif 'severity:' in line.lower():
                severity = line.split(':')[-1].strip().lower()
                current_issue['severity'] = severity if severity in ['info', 'warning', 'error'] else 'info'
            elif 'message:' in line.lower():
                current_issue['message'] = line.split(':')[-1].strip()
        
        if current_issue:
            issues.append(current_issue)
        
        result['issues'] = issues
        return result


async def _build_prompt(pr: PRData) -> List[Dict[str, str]]:
    """Async wrapper for threaded prompt building"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_thread_pool, _build_prompt_threaded, pr)


async def _safe_parse_json(content: str) -> Dict[str, Any]:
    """Async wrapper for threaded JSON parsing"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_thread_pool, _parse_json_threaded, content)


def _heuristic_review(pr: PRData) -> Dict[str, Any]:
    issues = []
    
    for file in pr.files:
        if not file.patch:
            continue
            
        lines = file.patch.splitlines()
        for line_num, line in enumerate(lines, start=1):
            if line.startswith("+"):
                new_content = line[1:]
                
                if "print(" in new_content or "console.log(" in new_content:
                    issues.append(
                        AnalysisIssue(
                            file_path=file.filename,
                            line=line_num,
                            severity="warning",
                            category="best_practice",
                            message="Debug logging found in committed code",
                            suggestion="Remove debug prints or guard them behind log levels",
                        )
                    )
                    
                if len(new_content) > 120:
                    issues.append(
                        AnalysisIssue(
                            file_path=file.filename,
                            line=line_num,
                            severity="info",
                            category="style",
                            message="Very long line added (>120 chars)",
                            suggestion="Wrap long lines to improve readability",
                        )
                    )
                    
                if re.search(r"TODO|FIXME", new_content):
                    issues.append(
                        AnalysisIssue(
                            file_path=file.filename,
                            line=line_num,
                            severity="info",
                            category="best_practice",
                            message="Leftover TODO/FIXME in changes",
                            suggestion="Track in issue tracker or resolve before merge",
                        )
                    )
    
    summary = "Automatic scan completed. Consider running a full AI review for deeper insights."
    return {
        "summary": summary,
        "issues": [issue.model_dump() for issue in issues],
    }


async def _call_ollama(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    if ollama is None:
        raise RuntimeError("Ollama package not available")
    
    try:
        model_name = settings.ollama_model
        logger.info(f"Using Ollama model: {model_name}")
        
        try:
            response = ollama.chat(model=model_name, messages=messages)
            content = response["message"]["content"]
            return await _safe_parse_json(content)
        except Exception as e:
            if "model not found" in str(e).lower():
                raise RuntimeError(f"Ollama model '{model_name}' not found. run 'ollama pull {model_name}'")
            elif "connection refused" in str(e).lower():
                raise RuntimeError("Ollama service not running. Please start Ollama with 'ollama serve'")
            else:
                raise RuntimeError(f"Ollama API error: {e}")
    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
        raise


async def _call_openai(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    if OpenAI is None:
        raise RuntimeError("OpenAI client not available")
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")
    
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.2,
        )
        content = resp.choices[0].message.content or "{}"
        return await _safe_parse_json(content)
    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        if "quota" in str(e).lower() or "billing" in str(e).lower():
            raise RuntimeError("OpenAI API quota exceeded or billing issue")
        elif "authentication" in str(e).lower():
            raise RuntimeError("OpenAI API key is invalid or expired")
        else:
            raise RuntimeError(f"OpenAI API error: {e}")


async def analyze_pr_with_agent(pr: PRData) -> AnalysisResult:
    messages = await _build_prompt(pr)
    provider = (settings.model_provider or "ollama").lower()

    parsed = None
    try:
        if provider == "openai":
            parsed = await _call_openai(messages)
        else:
            parsed = await _call_ollama(messages)
    except Exception as e:
        logger.error(f"AI call failed: {e}")
        parsed = None

    if not parsed:
        parsed = _heuristic_review(pr)

    issues_payload = parsed.get("issues") or []
    issues = []
    
    for item in issues_payload:
        try:
            issues.append(AnalysisIssue(**item))
        except Exception:
            issues.append(
                AnalysisIssue(
                    file_path=str(item.get("file_path", "unknown")),
                    line=item.get("line"),
                    severity=str(item.get("severity", "info")),
                    category=str(item.get("category", "best_practice")),
                    message=str(item.get("message", "Unparsed issue")),
                    suggestion=item.get("suggestion"),
                )
            )

    summary = str(parsed.get("summary", "Code review completed"))
    model_info = {"provider": provider}

    return AnalysisResult(
        repo_url=f"https://github.com/{pr.owner}/{pr.repo}",
        pr_number=pr.number,
        head_sha=pr.head_sha,
        issues=issues,
        summary=summary,
        model_info=model_info,
    )


