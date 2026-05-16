
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
| **Commute Advisor** | Multi-agent commute intelligence | Parallel data fetch → retry loop → Pydantic analysis → briefing |

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

# Run specific agents
cd agents && adk web
```
Now open - http://localhost:8000

### 4. Run with Docker

```bash
# Build the image
docker build -t docker-adk-agents:v1 .

# Run with local .env variables
docker run -p 8000:8000 --env-file agents/.env docker-adk-agents:v1
```
Now open - http://localhost:8000

## Sample prompts

| Agent | Prompts |
|-------|-------------|
| **Sequential Agent** | Write a HTML code with title and description for front main website page |
| **Parallel Agent** | Customer sentiment and feedback trends on Docker Model Runner and Docker AI |
| **Loop Agent** | Suggest some healthy recipe with paneer |
| **Human-in-Loop** | Plan a trip to dubai |
| **Google Search** | Share details about docker model runner features release |
| **Find Job** | Share job related to python |
| **Commute Advisor** | What is my commute looking like today from London Bridge to Canary Wharf? I normally take the train but want to know all my options. |

## Commute Advisor Agent

The Commute Advisor is the most advanced agent in this repo — it demonstrates six Google ADK patterns working together in a single pipeline.

### How it works

```
CommutePipeline (SequentialAgent)
├── DataGatheringLoop (LoopAgent — retries up to 3×)
│   ├── ParallelDataFetcher (ParallelAgent — all 4 run simultaneously)
│   │   ├── WeatherAgent     → weather conditions + commute impact
│   │   ├── TrainAgent       → train status, delays, platform, crowding
│   │   ├── BusAgent         → bus status, capacity, diversions
│   │   └── TrafficAgent     → road congestion, incidents, travel time
│   └── DataCompletenessChecker → escalates loop when all data present
├── HistoryAgent        → personalizes result with your commute history
├── CommuteAnalyzer     → structured Pydantic output (typed recommendation)
└── RecommendationPresenter → scannable human-readable briefing
```

**Default route:** London Bridge → Canary Wharf, Bus 188  
All data is simulated — each run produces a different scenario (clear day, storm, suspended train, standstill traffic, etc.)

### Run with Docker Model Runner

```bash
# Pull a model (Gemma recommended for better structured output)
docker model pull ai/gemma3:4B-Q4_0

# Local Python
cd agents
MODEL_NAME=ai/gemma3:4B-Q4_0 adk web

# Docker container
docker run -p 8000:8000 \
  -e DOCKER_MODEL_RUNNER=http://host.docker.internal:12434/engines/llama.cpp/v1 \
  -e MODEL_NAME=ai/gemma3:4B-Q4_0 \
  docker-adk-agents:v1
```

Open **http://localhost:8000**, select **commute_advisor**, and type your query.

### Supported models

| Model | Pull command | Notes |
|-------|-------------|-------|
| Llama 3.2 1B | `docker model pull ai/llama3.2:1B-Q8_0` | Smallest, fastest |
| Gemma 3 4B | `docker model pull ai/gemma3:4B-Q4_0` | Better quality, recommended |
| Gemma 3 12B | `docker model pull ai/gemma3:12B-Q4_0` | Best quality, needs 8GB+ RAM |

### Customize your route

Pass these as environment variables to change the default London route:

| Variable | Default | Example |
|----------|---------|---------|
| `COMMUTE_ORIGIN` | `London Bridge` | `Kings Cross` |
| `COMMUTE_DESTINATION` | `Canary Wharf` | `Liverpool Street` |
| `COMMUTE_BUS_ROUTE` | `188` | `205` |
| `COMMUTE_USER_ID` | `commuter_001` | `your_name` |

```bash
docker run -p 8000:8000 \
  -e DOCKER_MODEL_RUNNER=http://host.docker.internal:12434/engines/llama.cpp/v1 \
  -e MODEL_NAME=ai/gemma3:4B-Q4_0 \
  -e COMMUTE_ORIGIN="Kings Cross" \
  -e COMMUTE_DESTINATION="Liverpool Street" \
  -e COMMUTE_BUS_ROUTE="205" \
  docker-adk-agents:v1
```

### Sample output

```
COMMUTE ADVISOR — London Bridge → Canary Wharf
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STATUS: SIGNIFICANT DISRUPTION

RECOMMENDATION
  Mode:       Bus
  Duration:   ~52 minutes
  Confidence: 80%

CONDITION SUMMARY
  Weather  Heavy rain, 9°C — high impact
  Train    LON Metro Line — major delay, 38 min behind
  Bus      Route 188 — on time, 42% capacity
  Traffic  Moderate congestion — 60 min vs 38 min normal

ALERTS
  - Points failure between stations, engineers on site
  - Storm warning: delays expected across all transport modes

ADVICE
  Train severely delayed — take bus 188, on time and well below capacity.

BACKUP PLAN
  If bus fills up, nearest tube station 8 minutes walk away.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

> For detailed setup instructions, see [agents/commute_advisor/README.md](agents/commute_advisor/README.md).

---

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

## 🧪 Testing and Validation

### Test Container Networking

```bash
# Test endpoint connectivity
docker run --rm curlimages/curl:latest \
  curl -f http://host.docker.internal:12434/engines/llama.cpp/v1/models

# Test agent configuration
docker run --rm \
  -e DOCKER_MODEL_RUNNER=http://host.docker.internal:12434/engines/llama.cpp/v1 \
  docker-adk-agents \
  python -c "
from agents.shared.config import ModelRunnerConfig
config = ModelRunnerConfig()
print(f'Endpoint: {config.api_base}')
print(f'Model: {config.model_name}')
"
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
  docker-adk-agents
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




