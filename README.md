# PR Review Agent

An AI-powered code review system that analyzes GitHub Pull Requests using local (Ollama) or cloud (OpenAI) language models. Built with FastAPI, Celery, and Redis for high-performance async processing.

## Features

- AI-powered code reviews using Ollama (local) or OpenAI (cloud)
- Async processing with multithreading for optimal performance
- Background task processing with Celery
- Batch PR analysis for concurrent processing
- Redis-based caching to avoid re-analyzing unchanged code
- Comprehensive code analysis (bugs, style, performance, best practices)
- Built-in performance monitoring and benchmarks

## Quick Start

### Prerequisites

- Python 3.8+
- Redis server
- Ollama (for local AI models)
- GitHub token (optional, for higher rate limits)

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd pr-review-agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

Create `.env` file:

```bash
# GitHub (optional)
GITHUB_TOKEN=your_github_token_here

# OpenAI (optional, alternative to Ollama)
OPENAI_API_KEY=your_openai_key_here

# Redis
REDIS_URL=redis://localhost:6379

# Ollama (default)
OLLAMA_MODEL=llama3
MODEL_PROVIDER=ollama  # or "openai"

# Cache settings
CACHE_TTL_SECONDS=3600
```

### Start Services

```bash
# Start Redis
brew services start redis  # macOS
# OR
docker run -d -p 6379:6379 redis:7-alpine  # Docker

# Start Ollama
brew services start ollama  # macOS
ollama pull llama3

# Start API server
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start Celery worker (in another terminal)
source .venv/bin/activate
celery -A app.celery_app.celery_app worker --loglevel=INFO
```

## Usage

### Single PR Analysis

```bash
curl -X POST http://localhost:8000/analyze-pr \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/user/repo",
    "pr_number": 123,
    "github_token": "optional_token",
    "force": false
  }'
```

### Batch PR Analysis

```bash
curl -X POST http://localhost:8000/analyze-prs-batch \
  -H "Content-Type: application/json" \
  -d '[
    {"repo_url": "https://github.com/user/repo", "pr_number": 123},
    {"repo_url": "https://github.com/user/repo", "pr_number": 124}
  ]'
```

### Check Status and Results

```bash
# Check task status
curl http://localhost:8000/status/{task_id}

# Get results
curl http://localhost:8000/results/{task_id}

# Health check
curl http://localhost:8000/health

# Performance metrics
curl http://localhost:8000/performance
```

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   FastAPI   │    │   Celery    │    │    Redis   │
│   (Port 8K) │◄──►│   Worker    │◄──►│  (Cache)   │
└─────────────┘    └─────────────┘    └─────────────┘
         │                   │
         ▼                   ▼
┌─────────────┐    ┌─────────────┐
│   GitHub    │    │   Ollama    │
│     API     │    │   (Local)   │
└─────────────┘    └─────────────┘
```

## Performance Features

- **Async Processing**: Non-blocking HTTP requests and AI calls
- **Multithreading**: CPU-intensive operations run in parallel
- **Concurrent Analysis**: Multiple PRs processed simultaneously
- **Smart Caching**: Redis-based result caching with SHA invalidation
- **Real-time Monitoring**: Built-in performance metrics and benchmarks

## Development

### Project Structure

```
pr-review-agent/
├── app/
│   ├── agent/          # AI agent logic
│   ├── services/       # External service integrations
│   ├── schemas.py      # Data models
│   ├── main.py         # FastAPI application
│   ├── tasks.py        # Celery tasks
│   └── config.py       # Configuration
├── tests/              # Unit tests
├── docker-compose.yml  # Docker services
├── Makefile           # Development shortcuts
└── requirements.txt   # Dependencies
```

### Available Commands

```bash
make install          # Install dependencies
make run             # Start all services
make test            # Run tests
make setup-check     # Verify environment
make docker-up       # Start Docker services
make docker-down     # Stop Docker services
```

### Testing

```bash
# Run all tests
make test

# Run specific test file
python -m pytest tests/test_api.py -v

# Run with coverage
python -m pytest --cov=app tests/
```

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   ```bash
   brew services start redis
   redis-cli ping
   ```

2. **Ollama Not Found**
   ```bash
   brew install ollama
   brew services start ollama
   ollama pull llama3
   ```

3. **Import Errors**
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

4. **Performance Issues**
   ```bash
   curl http://localhost:8000/performance
   ```

## Security

- GitHub tokens stored as environment variables
- API keys never committed to version control
- Built-in GitHub API rate limit handling
- Pydantic-based input validation

## Scaling

- Multiple Celery workers for increased throughput
- Load balancing with multiple API instances
- Redis clustering for high-availability
- Configurable thread pool sizes and cache TTL

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request
