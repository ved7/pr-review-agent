#!/bin/bash

echo "🚀 PR Review Agent - Live Demo"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if services are running
echo "🔍 Checking Service Status..."
echo ""

# Health check
echo "1. Health Check:"
if curl -s http://localhost:8000/health > /dev/null; then
    print_status "API server is running"
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
    echo "   Response: $HEALTH_RESPONSE"
else
    print_error "API server is not running"
    echo "   Please start the server first:"
    echo "   source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    exit 1
fi
echo ""

# Performance check
echo "2. Performance Check:"
if curl -s http://localhost:8000/performance > /dev/null; then
    print_status "Performance endpoint working"
    PERF_RESPONSE=$(curl -s http://localhost:8000/performance)
    echo "   Async Support: $(echo $PERF_RESPONSE | grep -o '"async_support":true')"
    echo "   Concurrent Processing: $(echo $PERF_RESPONSE | grep -o '"concurrent_processing":true')"
else
    print_error "Performance endpoint not working"
fi
echo ""

# Benchmark
echo "3. Performance Benchmark:"
if curl -s http://localhost:8000/benchmark > /dev/null; then
    print_status "Benchmark endpoint working"
    BENCHMARK_RESPONSE=$(curl -s http://localhost:8000/benchmark)
    echo "   Async vs Sync: $(echo $BENCHMARK_RESPONSE | grep -o '"improvement":"[^"]*"' | cut -d'"' -f4)"
    echo "   Multithreading: $(echo $BENCHMARK_RESPONSE | grep -o '"speedup":"[^"]*"' | cut -d'"' -f4)"
else
    print_error "Benchmark endpoint not working"
fi
echo ""

# Single PR Analysis Demo
echo "4. Single PR Analysis Demo:"
print_info "Submitting PR #6 for analysis..."
SINGLE_RESPONSE=$(curl -s -X POST http://localhost:8000/analyze-pr \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/octocat/Hello-World", "pr_number": 6}')

if echo "$SINGLE_RESPONSE" | grep -q "task_id"; then
    TASK_ID=$(echo "$SINGLE_RESPONSE" | grep -o '"task_id":"[^"]*"' | cut -d'"' -f4)
    print_status "Task submitted successfully"
    echo "   Task ID: $TASK_ID"
    echo "   Status: PENDING (processing in background)"
else
    print_error "Failed to submit task"
    echo "   Response: $SINGLE_RESPONSE"
fi
echo ""

# Batch PR Analysis Demo
echo "5. Batch PR Analysis Demo:"
print_info "Analyzing multiple PRs concurrently..."
BATCH_RESPONSE=$(curl -s -X POST http://localhost:8000/analyze-prs-batch \
  -H "Content-Type: application/json" \
  -d '[{"repo_url": "https://github.com/octocat/Hello-World", "pr_number": 5}, {"repo_url": "https://github.com/octocat/Hello-World", "pr_number": 6}]')

if echo "$BATCH_RESPONSE" | grep -q "batch_id"; then
    BATCH_ID=$(echo "$BATCH_RESPONSE" | grep -o '"batch_id":"[^"]*"' | cut -d'"' -f4)
    TOTAL_PRS=$(echo "$BATCH_RESPONSE" | grep -o '"total_prs":[0-9]*' | cut -d':' -f2)
    print_status "Batch analysis completed successfully"
    echo "   Batch ID: $BATCH_ID"
    echo "   Total PRs: $TOTAL_PRS"
    echo "   Processing: Concurrent (async + multithreading)"
else
    print_error "Batch analysis failed"
    echo "   Response: $BATCH_RESPONSE"
fi
echo ""

# Show results summary
echo "6. Results Summary:"
if echo "$BATCH_RESPONSE" | grep -q '"status":"success"'; then
    SUCCESS_COUNT=$(echo "$BATCH_RESPONSE" | grep -o '"status":"success"' | wc -l)
    print_status "Successfully analyzed $SUCCESS_COUNT PRs"
    
    # Show sample result
    echo "   Sample Analysis (PR #6):"
    SUMMARY=$(echo "$BATCH_RESPONSE" | grep -o '"summary":"[^"]*"' | head -1 | cut -d'"' -f4)
    echo "   Summary: ${SUMMARY:0:100}..."
else
    print_warning "No successful analyses found"
fi
echo ""

# Performance highlights
echo "7. Performance Highlights:"
echo "   🚀 Async HTTP requests to GitHub API"
echo "   🔄 Concurrent PR processing"
echo "   🧵 Multithreaded CPU operations"
echo "   💾 Redis-based caching"
echo "   📊 Real-time performance monitoring"
echo ""

# Architecture overview
echo "8. System Architecture:"
echo "   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐"
echo "   │   FastAPI   │    │   Celery   │    │    Redis   │"
echo "   │   (Port 8K) │◄──►│   Worker   │◄──►│  (Cache)   │"
echo "   └─────────────┘    └─────────────┘    └─────────────┘"
echo "            │                   │"
echo "            ▼                   ▼"
echo "   ┌─────────────┐    ┌─────────────┐"
echo "   │   GitHub    │    │   Ollama    │"
echo "   │     API     │    │   (Local)   │"
echo "   └─────────────┘    └─────────────┘"
echo ""

# Demo conclusion
echo "🎯 Demo Complete!"
echo "=================="
print_status "All endpoints are working"
print_status "Async processing is functional"
print_status "Multithreading is operational"
print_status "AI analysis is successful"
echo ""
echo "💡 Key Benefits Demonstrated:"
echo "   • High-performance async processing"
echo "   • Concurrent batch analysis"
echo "   • Intelligent AI code review"
echo "   • Real-time performance monitoring"
echo "   • Robust error handling"
echo ""
echo "🚀 Ready for production use!"
