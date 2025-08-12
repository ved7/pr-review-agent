#!/usr/bin/env python3
"""
Setup script for PR Review Agent
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, check=True):
    """Run a shell command"""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        if check:
            print(f"Error: {e}")
            if e.stderr:
                print(f"stderr: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True


def check_dependencies():
    """Check if required packages are installed"""
    required = [
        "fastapi", "uvicorn", "celery", "redis", "httpx", 
        "pydantic", "loguru", "ollama", "openai"
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    return True


def check_ollama():
    """Check if Ollama is available"""
    try:
        import ollama
        models = ollama.list()
        if hasattr(models, 'models') and models.models:
            print(f"✅ Ollama available with models: {[m.model for m in models.models]}")
        else:
            print("✅ Ollama available (no models downloaded yet)")
        return True
    except Exception as e:
        print(f"❌ Ollama not available: {e}")
        print("Install with: brew install ollama")
        return False


def check_redis():
    """Check if Redis is accessible"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis accessible")
        return True
    except Exception as e:
        print(f"❌ Redis not accessible: {e}")
        print("Start Redis with: redis-server")
        print("Or use Docker: docker run -d -p 6379:6379 redis:7-alpine")
        return False


def main():
    print("🔍 PR Review Agent Setup Check")
    print("=" * 40)
    
    checks = [
        check_python_version(),
        check_dependencies(),
        check_ollama(),
        check_redis(),
    ]
    
    print("\n" + "=" * 40)
    if all(checks):
        print("🎉 All checks passed! You can now run the application.")
        print("\nTo start:")
        print("1. Start Redis: redis-server")
        print("2. Start API: uvicorn app.main:app --reload")
        print("3. Start Worker: celery -A app.celery_app.celery_app worker")
        print("\nOr use Docker: docker-compose up -d")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
