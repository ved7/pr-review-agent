# 🚀 Demo Quick Reference Card

## 🎯 **Opening Line:**
> "I'm showcasing a PR Review Agent - an AI-powered system that automatically reviews GitHub Pull Requests using local AI models and high-performance async processing."

## 📋 **Demo Flow (5-6 minutes total):**

### **1. System Health (30s)**
```bash
curl http://localhost:8000/health
```
**Say:** "All services are healthy - Redis, Ollama, and our API are running perfectly."

### **2. Performance Capabilities (30s)**
```bash
curl http://localhost:8000/performance
```
**Say:** "The system supports async processing and concurrent operations for high performance."

### **3. Benchmark Results (1 min)**
```bash
curl http://localhost:8000/benchmark
```
**Say:** "Here's the performance data - async gives us 11.8% improvement, and we use multithreading for CPU tasks."

### **4. Single PR Analysis (1 min)**
```bash
curl -X POST http://localhost:8000/analyze-pr \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/octocat/Hello-World", "pr_number": 6}'
```
**Say:** "This creates a background task that gets processed by our Celery workers."

### **5. Batch Processing - THE HIGHLIGHT (2 min)**
```bash
curl -X POST http://localhost:8000/analyze-prs-batch \
  -H "Content-Type: application/json" \
  -d '[{"repo_url": "https://github.com/octocat/Hello-World", "pr_number": 5}, {"repo_url": "https://github.com/octocat/Hello-World", "pr_number": 6}]'
```
**Say:** "This is the star of the show - we're analyzing multiple PRs concurrently using async processing. Notice how both are processed simultaneously!"

## 💡 **Key Points to Emphasize:**

- **Performance**: "11.8% improvement with async, concurrent processing"
- **Architecture**: "Modern stack - FastAPI, Celery, Redis, Ollama"
- **Scalability**: "Can handle multiple teams and PRs simultaneously"
- **Cost**: "Local AI models vs expensive cloud APIs"
- **Quality**: "Consistent, thorough code reviews every time"

## 🎭 **If Asked Questions:**

**Q: "How does it compare to GitHub's built-in review?"**
A: "This provides deeper AI analysis, custom rules, and can be integrated into any workflow."

**Q: "What about security?"**
A: "All tokens are environment variables, never committed to code. We also validate all inputs."

**Q: "Can it scale?"**
A: "Absolutely - we can add more Celery workers, multiple API instances, and even Redis clusters."

## 🚨 **Emergency Commands:**

**If something breaks:**
```bash
# Restart API
pkill -f uvicorn && source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Restart Celery
pkill -f celery && source .venv/bin/activate && celery -A app.celery_app.celery_app worker --loglevel=INFO

# Check services
brew services list | grep -E "(redis|ollama)"
```

## 🎯 **Closing Statement:**
> "This demonstrates modern software architecture: async processing, microservices, intelligent caching, and AI integration. It's production-ready and can significantly improve development team productivity."

---

**Remember**: You've built a working system with real performance improvements. Be confident! 🚀
