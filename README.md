
# Google ADK + Docker Model Runner Agents 

AI agents built using Google ADK and Docker Model Runner. 


## Available Agents

| Agent | Description | Key Features |
|-------|-------------|-------------|
| **Sequential Agent** | Code development pipeline | Write → Review → Refactor |
| **Parallel Agent** | Market intelligence analysis | Concurrent competitive/trend/sentiment analysis |
| **Loop Agent** | Iterative recipe development | Recipe creation with dietician feedback loops |
| **Human-in-Loop** | Travel planning with feedback | Human decision points in AI workflows |
| **Google Search** | Web research and synthesis | Live search with comprehensive reports |
| **Find Job** | Job market analysis | Career guidance and opportunity analysis |

## Quick Start

### Prerequisites

- **Docker Desktop 4.40+** with Model Runner enabled
- **Python 3.9+** (for local development)
- **Google API Key** (optional, for Google Search agents)

### 1. Pull and Run a Model

```bash
# Enable Docker Model Runner
docker desktop enable model-runner --tcp 12434

# Pull a model
docker model pull ai/llama3.2:1B-Q8_0

# Verify Model Runner is working
curl http://localhost:12434/engines/llama.cpp/v1/models
```

### 2. Clone and Setup

```bash
git clone https://github.com/dockersamples/google-adk-docker-model-runner.git
cd google-adk-docker-model-runner

# Copy environment template
cp agents/.env.example agents/.env

# Edit .env file with your configuration
nano agents/.env
```

### 3. Run Locally

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run specific agent
python agents/sequential_agent/agent.py
python agents/parallel_agent/agent.py
python agents/loop_agent/agent.py
```

### 4. Run with Docker

```bash
# Build the image
docker build -t adk-agents .

# Run sequential agent (default)
docker run --rm \
  -e DOCKER_MODEL_RUNNER=http://host.docker.internal:12434/engines/llama.cpp/v1 \
  -e TEST_QUERY="Create a modern dashboard with charts" \
  adk-agents

# Run different agents
docker run --rm \
  -e AGENT_TYPE=parallel \
  -e TEST_QUERY="Analyze the AI development tools market" \
  -e DOCKER_MODEL_RUNNER=http://host.docker.internal:12434/engines/llama.cpp/v1 \
  adk-agents

docker run --rm \
  -e AGENT_TYPE=loop \
  -e TEST_QUERY="Healthy breakfast recipe with quinoa" \
  -e DOCKER_MODEL_RUNNER=http://host.docker.internal:12434/engines/llama.cpp/v1 \
  adk-agents
```


## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DOCKER_MODEL_RUNNER` | Model Runner endpoint | Auto-detected | No |
| `MODEL_NAME` | Model to use | `ai/llama3.2:1B-Q8_0` | No |
| `OPENAI_API_KEY` | API key for local runner | `anything` | No |
| `GOOGLE_API_KEY` | Google API key | None | Yes (for search agents) |
| `AGENT_TYPE` | Which agent to run | `sequential` | No |
| `TEST_QUERY` | Query to process | Agent-specific default | No |

### Automatic Endpoint Detection

The system automatically detects the correct Docker Model Runner endpoint:

1. **Explicit Override**: `DOCKER_MODEL_RUNNER` environment variable
2. **Container Auto-Detection**: Tests common container networking patterns
3. **Localhost Fallback**: Uses `http://localhost:12434` for development

### Supported Endpoints

- **Host/Development**: `http://localhost:12434/engines/llama.cpp/v1`
- **Docker Desktop**: `http://host.docker.internal:12434/engines/llama.cpp/v1`
- **Docker Internal**: `http://model-runner.docker.internal:12434/engines/llama.cpp/v1`
- **Docker Bridge**: `http://172.17.0.1:12434/engines/llama.cpp/v1`
- **Docker Compose**: `http://model-runner:12434/engines/llama.cpp/v1`

## 📋 Detailed Agent Examples

### Sequential Agent: Code Development Pipeline

```bash
# Creates: HTML → Review → Refactored Code
python agents/sequential_agent/agent.py

# Example with custom query
TEST_QUERY="Create a login form with validation" python agents/sequential_agent/agent.py
```

### Parallel Agent: Market Intelligence

```bash
# Runs 3 agents in parallel: Competitor + Trend + Sentiment Analysis
python agents/parallel_agent/agent.py

# Example with specific market
TEST_QUERY="Cloud storage market landscape 2025" python agents/parallel_agent/agent.py
```

### Loop Agent: Iterative Recipe Development

```bash
# Creates recipe → Dietician review → Improvement (loops until approved)
python agents/loop_agent/agent.py

# Example with dietary requirements
TEST_QUERY="Vegan protein-rich dinner for athletes" python agents/loop_agent/agent.py
```

### Human-in-Loop: Travel Planning

```bash
# Research → Initial plan → Human feedback → Optimized plan
python agents/human_in_loop_agent/agent.py

# Different feedback scenarios
HUMAN_FEEDBACK_SCENARIO=2 python agents/human_in_loop_agent/agent.py
```

### Google Search Agent

```bash
# Requires GOOGLE_API_KEY in .env file
GOOGLE_API_KEY=your-key python agents/google_search_agent/agent.py

# Example research topic
TEST_QUERY="Kubernetes security best practices 2025" python agents/google_search_agent/agent.py
```

### Find Job Agent

```bash
# Job search and career analysis
python agents/find_job_agent/agent.py

# Example job search
TEST_QUERY="Senior DevOps engineer remote positions" python agents/find_job_agent/agent.py
```





## 🧪 Testing and Validation

### Test Container Networking

```bash
# Test endpoint connectivity
docker run --rm curlimages/curl:latest \
  curl -f http://host.docker.internal:12434/engines/llama.cpp/v1/models

# Test agent configuration
docker run --rm \
  -e DOCKER_MODEL_RUNNER=http://host.docker.internal:12434/engines/llama.cpp/v1 \
  adk-agents \
  python -c "
from agents.shared.config import ModelRunnerConfig
config = ModelRunnerConfig()
print(f'Endpoint: {config.api_base}')
print(f'Model: {config.model_name}')
"
```

### Performance Testing

```bash
# Test all agents sequentially
for agent in sequential parallel loop human_in_loop; do
  echo "Testing $agent agent..."
  docker run --rm \
    -e AGENT_TYPE=$agent \
    -e DOCKER_MODEL_RUNNER=http://host.docker.internal:12434/engines/llama.cpp/v1 \
    adk-agents
done
```

## 🔍 Troubleshooting

### Common Issues

#### Issue: "Session not found"
```bash
# Check if using async/await properly
grep -r "create_session" agents/
```

#### Issue: "Connection refused"
```bash
# Verify Model Runner is accessible
curl http://localhost:12434/engines/llama.cpp/v1/models

# Check Docker networking
docker run --rm curlimages/curl:latest \
  curl -f http://host.docker.internal:12434/engines/llama.cpp/v1/models
```

#### Issue: "Model not found"
```bash
# Pull the model first
docker model pull ai/llama3.2:1B-Q8_0
docker model ls
```

#### Issue: Container networking problems
```bash
# Test different endpoints
for endpoint in \
  "http://host.docker.internal:12434" \
  "http://172.17.0.1:12434" \
  "http://localhost:12434"; do
  echo "Testing $endpoint..."
  docker run --rm curlimages/curl:latest \
    curl -f "$endpoint/engines/llama.cpp/v1/models" || echo "Failed"
done
```

### Debug Mode

```bash
# Enable detailed logging
docker run --rm \
  -e LOG_LEVEL=DEBUG \
  -e DEV_MODE=true \
  -e DOCKER_MODEL_RUNNER=http://host.docker.internal:12434/engines/llama.cpp/v1 \
  adk-agents
```

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────┐
│        Application Layer            │ ← Your Agent Logic
├─────────────────────────────────────┤
│      🤖 Google ADK Framework       │ ← Agent Orchestration
│   • Multi-agent workflows          │
│   • State management               │
│   • Tool integration               │
├─────────────────────────────────────┤
│    📡 Centralized Configuration    │ ← Environment Detection
│   • Auto endpoint detection        │
│   • Container networking           │
│   • Model configuration            │
├─────────────────────────────────────┤
│      🔌 LiteLLM Abstraction        │ ← Model API Layer
├─────────────────────────────────────┤
│    🚢 Docker Model Runner          │ ← Local Inference
│   • llama.cpp engine               │
│   • OpenAI-compatible API          │
├─────────────────────────────────────┤
│      🧠 AI Model (Llama 3.2)       │ ← The Actual Model
└─────────────────────────────────────┘
```

### Key Design Decisions

1. **Centralized Configuration**: All agents use `agents/shared/config.py`
2. **Environment Awareness**: Automatic detection of container vs host execution
3. **Graceful Fallbacks**: Multiple endpoint detection strategies
4. **Async-First**: Proper async/await patterns throughout
5. **Error Handling**: Comprehensive error handling and logging

## 📚 Additional Resources

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Docker Model Runner Guide](https://docs.docker.com/ai/model-runner/)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [Container Networking](https://docs.docker.com/network/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with proper error handling
4. Test in both local and container environments
5. Submit a pull request




