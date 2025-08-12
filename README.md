# 🚀 PR Review Agent

An intelligent AI-powered code review system that analyzes GitHub Pull Requests using local (Ollama) or cloud (OpenAI) language models. Built with FastAPI, Celery, and Redis for high-performance async processing.

## ✨ Features

- **🤖 AI-Powered Reviews**: Uses Ollama (local) or OpenAI (cloud) for intelligent code analysis
- **⚡ High Performance**: Async/await + multithreading for optimal performance
- **🔄 Background Processing**: Celery-based task queue for non-blocking operations
- **📊 Batch Processing**: Analyze multiple PRs concurrently
- **💾 Smart Caching**: Redis-based caching to avoid re-analyzing unchanged code
- **🔍 Comprehensive Analysis**: Identifies bugs, style issues, performance problems, and best practices
- **📈 Performance Monitoring**: Built-in benchmarks and metrics

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App  │    │   Celery Worker │    │     Redis      │
│   (Port 8000)  │◄──►│   (Background)  │◄──►│   (Cache/Queue) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   GitHub API    │    │  Ollama/OpenAI  │
│   (PR Data)    │    │   (AI Models)   │
└─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Docker** (optional, for Redis)
- **Ollama** (for local AI models)
- **GitHub Token** (optional, for higher rate limits)

### 1. Clone & Setup

```bash
git clone <your-repo-url>
cd pr-review-agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

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

### 3. Start Services

#### Option A: Using Makefile (Recommended)

```bash
# Check setup
make setup-check

# Start Redis (macOS)
make redis-up

# Start Ollama (macOS)
make ollama-up

# Start all services
make run
```

#### Option B: Manual Start

```bash
# Terminal 1: Start Redis
brew services start redis  # macOS
# OR
docker run -d -p 6379:6379 redis:7-alpine  # Docker

# Terminal 2: Start Ollama
brew services start ollama  # macOS
# OR
ollama serve  # Linux

# Pull AI model
ollama pull llama3

# Terminal 3: Start API server
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 4: Start Celery worker
source .venv/bin/activate
celery -A app.celery_app.celery_app worker --loglevel=INFO
```

### 4. Verify Setup

```bash
# Health check
curl http://localhost:8000/health

# Performance check
curl http://localhost:8000/performance

# Benchmark
curl http://localhost:8000/benchmark
```

## 📖 Usage

### Single PR Analysis (Background Processing)

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

**Response:**
```json
{
  "task_id": "abc123-def456-ghi789"
}
```

**Check Status:**
```bash
curl http://localhost:8000/status/abc123-def456-ghi789
```

**Get Results:**
```bash
curl http://localhost:8000/results/abc123-def456-ghi789
```

### Batch PR Analysis (Concurrent Processing)

```bash
curl -X POST http://localhost:8000/analyze-prs-batch \
  -H "Content-Type: application/json" \
  -d '[
    {"repo_url": "https://github.com/user/repo", "pr_number": 123},
    {"repo_url": "https://github.com/user/repo", "pr_number": 124},
    {"repo_url": "https://github.com/user/repo", "pr_number": 125}
  ]'
```

**Response:**
```json
{
  "batch_id": "batch_3_123456789",
  "total_prs": 3,
  "results": [
    {
      "repo_url": "https://github.com/user/repo",
      "pr_number": 123,
      "status": "success",
      "result": { ... }
    }
  ]
}
```

## 🔧 Performance Features

### Async Processing
- **HTTP Requests**: Non-blocking GitHub API calls
- **AI Model Calls**: Concurrent Ollama/OpenAI requests
- **Batch Operations**: Multiple PRs processed simultaneously

### Multithreading
- **CPU-Intensive Tasks**: JSON parsing, prompt building, file processing
- **Thread Pools**: Optimized worker counts for different operations
- **Mixed Approach**: Async I/O + threaded CPU work

### Caching
- **Redis Backend**: Fast in-memory storage
- **Smart Keys**: SHA-based cache invalidation
- **Configurable TTL**: Adjustable cache expiration

## 📊 Performance Metrics

### Benchmark Results
```bash
curl http://localhost:8000/benchmark
```

**Typical Results:**
- **Async vs Sync**: 10-15% improvement
- **Multithreading**: 2-4x speedup for CPU work
- **Mixed Processing**: Optimal efficiency

### Monitoring
- **Health Checks**: Service status monitoring
- **Performance Tests**: Real-time metrics
- **Error Tracking**: Comprehensive logging

## 🛠️ Development

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

### Available Make Commands

```bash
make install          # Install dependencies
make run             # Start all services
make test            # Run tests
make setup-check     # Verify environment
make docker-up       # Start Docker services
make docker-down     # Stop Docker services
make clean           # Clean up
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

## 🚨 Troubleshooting

### Common Issues

#### 1. Redis Connection Failed
```bash
# Check Redis status
brew services list | grep redis

# Start Redis
brew services start redis

# Test connection
redis-cli ping
```

#### 2. Ollama Not Found
```bash
# Install Ollama (macOS)
brew install ollama

# Start service
brew services start ollama

# Pull model
ollama pull llama3
```

#### 3. Import Errors
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### 4. Performance Issues
```bash
# Check thread pool sizes
curl http://localhost:8000/performance

# Monitor resource usage
top -p $(pgrep -f uvicorn)
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Start with debug
uvicorn app.main:app --reload --log-level debug
```

## 🔒 Security

- **GitHub Tokens**: Stored as environment variables
- **API Keys**: Never committed to version control
- **Rate Limiting**: Built-in GitHub API rate limit handling
- **Input Validation**: Pydantic-based request validation

## 📈 Scaling

### Horizontal Scaling
- **Multiple Workers**: Scale Celery workers
- **Load Balancing**: Multiple API instances
- **Redis Cluster**: For high-availability

### Performance Tuning
- **Thread Pool Sizes**: Adjust based on CPU cores
- **Cache TTL**: Optimize for your use case
- **Batch Sizes**: Balance memory vs performance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **FastAPI**: Modern web framework
- **Celery**: Distributed task queue
- **Ollama**: Local LLM inference
- **OpenAI**: Cloud LLM services
- **Redis**: In-memory data store

---

**Happy Code Reviewing! 🎉**
