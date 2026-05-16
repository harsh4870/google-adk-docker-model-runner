# Commute Advisor Agent

A multi-agent AI system built with **Google ADK** and **Docker Model Runner** that analyzes your commute across weather, train, bus, and traffic data simultaneously — then delivers a clear, personalized briefing.

---

## Table of Contents

- [What It Does](#what-it-does)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Running the Agent](#running-the-agent)
  - [Option 1 — Local Python + Docker Model Runner](#option-1--local-python--docker-model-runner)
  - [Option 2 — Docker Container + Docker Model Runner](#option-2--docker-container--docker-model-runner)
  - [Option 3 — Gemma Model](#option-3--gemma-model)
- [What to Ask](#what-to-ask)
- [Configuration](#configuration)
- [Sample Output](#sample-output)
- [Troubleshooting](#troubleshooting)

---

## What It Does

The Commute Advisor fetches real-time (mock) data from four sources **at the same time**, validates completeness, personalizes the result with your history, and produces a structured briefing telling you exactly how to get to work today.

**Default route:** London Bridge → Canary Wharf (configurable via environment variables)

> **Note:** All data is simulated with realistic random scenarios. Each run produces a different result — this is intentional so you can see all possible commute conditions without needing real APIs.

---

## Architecture

The pipeline runs five stages in sequence. Stages 1–2 repeat up to 3 times if any data source fails.

```
CommutePipeline (SequentialAgent)
├── DataGatheringLoop (LoopAgent — retries up to 3×)
│   ├── ParallelDataFetcher (ParallelAgent — all 4 run at the same time)
│   │   ├── WeatherAgent     → fetches weather + impact level
│   │   ├── TrainAgent       → fetches train status + delays
│   │   ├── BusAgent         → fetches bus status + capacity
│   │   └── TrafficAgent     → fetches road congestion + incidents
│   └── DataCompletenessChecker → validates all 4 sources; retries if any missing
├── HistoryAgent        → loads your historical commute patterns
├── CommuteAnalyzer     → synthesizes everything into a typed Pydantic recommendation
└── RecommendationPresenter → formats the final human-readable briefing
```

**ADK patterns demonstrated:**
- `ParallelAgent` — concurrent multi-source data fetching
- `LoopAgent` — retry logic until data is complete
- `BaseAgent` subclass — custom escalation with `EventActions(escalate=True)`
- `SequentialAgent` — ordered pipeline orchestration
- Pydantic `output_schema` — typed structured output from an LLM
- `output_key` — sharing state across agents via session

---

## Prerequisites

Before you start, make sure you have:

| Requirement | Version | Check |
|-------------|---------|-------|
| Docker Desktop | 4.40+ | `docker --version` |
| Docker Model Runner | Enabled | `docker desktop enable model-runner --tcp 12434` |
| Python | 3.9+ | `python --version` |

### Enable Docker Model Runner

```bash
# Enable Model Runner with TCP access on port 12434
docker desktop enable model-runner --tcp 12434

# Verify it is running
curl http://localhost:12434/engines/llama.cpp/v1/models
```

You should see a JSON response listing available models. If you get a connection error, open Docker Desktop → Settings → Features → enable Model Runner.

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/dockersamples/google-adk-docker-model-runner.git
cd google-adk-docker-model-runner
```

### 2. Pull a model into Docker Model Runner

You need at least one model pulled before running the agent. Pick one:

```bash
# Option A — Llama 3.2 (smallest, fastest, good for testing)
docker model pull ai/llama3.2:1B-Q8_0

# Option B — Gemma 3 4B (better quality, needs ~4GB RAM)
docker model pull ai/gemma3:4B-Q4_0

# Option C — Gemma 3 12B (highest quality, needs ~8GB RAM)
docker model pull ai/gemma3:12B-Q4_0
```

Verify the model is available:

```bash
curl http://localhost:12434/engines/llama.cpp/v1/models
```

### 3. Create your environment file

```bash
cd agents
cp .env.example .env
```

Open `.env` and set the model you pulled:

```env
# Set this to the model you pulled in step 2
MODEL_NAME=ai/llama3.2:1B-Q8_0

# Leave this blank — it auto-detects localhost:12434
DOCKER_MODEL_RUNNER=

# Required only for Google Search agents (not needed for Commute Advisor)
GOOGLE_API_KEY=
```

### 4. Install Python dependencies

```bash
# From the project root
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

pip install -r requirements.txt
```

---

## Running the Agent

### Option 1 — Local Python + Docker Model Runner

This runs the agent on your machine, connecting to Docker Model Runner on localhost.

```bash
# Make sure you are in the agents directory with venv active
cd agents
source ../venv/bin/activate

# Start the ADK web interface
adk web
```

Open your browser: **http://localhost:8000**

1. Select **commute_advisor** from the agent list
2. Type your query in the chat box (see [What to Ask](#what-to-ask))
3. Watch the pipeline execute — you will see each agent complete in the logs

### Option 2 — Docker Container + Docker Model Runner

This builds the agent into a Docker image and runs it as a container.

```bash
# Build the image (from the project root)
docker build -t docker-adk-agents:v1 .

# Run with Llama 3.2 (default)
docker run -p 8000:8000 \
  -e DOCKER_MODEL_RUNNER=http://host.docker.internal:12434/engines/llama.cpp/v1 \
  -e MODEL_NAME=ai/llama3.2:1B-Q8_0 \
  docker-adk-agents:v1
```

Open your browser: **http://localhost:8000**

> **Why `host.docker.internal`?**  
> When running inside a container, `localhost` refers to the container itself, not your Mac/Windows host. Docker automatically resolves `host.docker.internal` to your host machine where Docker Model Runner is listening on port 12434.

### Option 3 — Gemma Model

Gemma runs through the exact same path as any other model — just change `MODEL_NAME`.

**Local Python:**

```bash
# Edit .env
MODEL_NAME=ai/gemma3:4B-Q4_0

# Then run as normal
cd agents && adk web
```

**Docker container:**

```bash
docker run -p 8000:8000 \
  -e DOCKER_MODEL_RUNNER=http://host.docker.internal:12434/engines/llama.cpp/v1 \
  -e MODEL_NAME=ai/gemma3:4B-Q4_0 \
  docker-adk-agents:v1
```

**Direct Python script (no web UI):**

```bash
cd agents
MODEL_NAME=ai/gemma3:4B-Q4_0 python commute_advisor/agent.py
```

---

## What to Ask

The agent always runs the full pipeline regardless of how you phrase the query. These prompts all work:

```
What is my commute looking like today from London Bridge to Canary Wharf?
I normally take the train but want to know all my options.
```

```
Should I drive or take the train today?
```

```
Give me a full commute briefing.
```

```
Is there any major disruption on my route today?
```

```
What is the weather impact on my commute?
```

```
What is my best option to get to work today?
```

> **Tip:** The data is randomized on every run, so you will see different conditions each time — clear days, heavy rain, suspended trains, standstill traffic, etc.

---

## Configuration

Customize your route and commuter profile with environment variables. Add these to your `.env` file or pass them as `-e` flags to `docker run`.

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_NAME` | `ai/llama3.2:1B-Q8_0` | Model to use from Docker Model Runner |
| `DOCKER_MODEL_RUNNER` | Auto-detected | Override the Model Runner endpoint |
| `COMMUTE_ORIGIN` | `London Bridge` | Your departure station or address |
| `COMMUTE_DESTINATION` | `Canary Wharf` | Your destination station or address |
| `COMMUTE_BUS_ROUTE` | `188` | Bus route number to monitor |
| `COMMUTE_USER_ID` | `commuter_001` | User ID for personalization history |
| `COMMUTE_QUERY` | (see agent.py) | Override the default startup query |

**Example — change the commute route:**

```bash
docker run -p 8000:8000 \
  -e DOCKER_MODEL_RUNNER=http://host.docker.internal:12434/engines/llama.cpp/v1 \
  -e MODEL_NAME=ai/gemma3:4B-Q4_0 \
  -e COMMUTE_ORIGIN="Kings Cross" \
  -e COMMUTE_DESTINATION="Liverpool Street" \
  -e COMMUTE_BUS_ROUTE="205" \
  docker-adk-agents:v1
```

---

## Sample Output

After running a query you will see output like this from the `RecommendationPresenter` agent:

```
════════════════════════════════════════════════════════════
COMMUTE ADVISOR — London Bridge → Canary Wharf
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STATUS: SIGNIFICANT DISRUPTION

RECOMMENDATION
  Mode:       Bus
  Duration:   ~52 minutes
  Confidence: 80%

CONDITION SUMMARY
  Weather  Heavy rain, 9°C — high impact on walking/cycling
  Train    LON Metro Line — major delay, 38 min behind schedule
  Bus      Route 188 — on time, 42% capacity
  Traffic  Moderate congestion — 60 min vs 38 min normal

ALERTS
  - Points failure between stations, engineers on site
  - Storm warning: significant delays expected across all transport modes

ADVICE
  Train is severely delayed — take the 188 bus which is running on time
  and well below capacity. Allow extra 10 minutes for rain delays.

BACKUP PLAN
  If bus fills up, nearest tube station is 8 minutes walk and
  serves your destination with one change.

Data freshness: 2025-05-15T08:42:11.234561
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Troubleshooting

### "Connection refused" on port 12434

Docker Model Runner is not running. Fix:

```bash
docker desktop enable model-runner --tcp 12434

# Verify
curl http://localhost:12434/engines/llama.cpp/v1/models
```

### "Model not found" error

You have not pulled the model yet, or `MODEL_NAME` does not match what you pulled:

```bash
# See what models are available
curl http://localhost:12434/engines/llama.cpp/v1/models | python -m json.tool

# Pull the model matching your MODEL_NAME
docker model pull ai/gemma3:4B-Q4_0
```

### Container cannot reach Model Runner

Inside a container, `localhost` is the container — not your host. Always use:

```bash
-e DOCKER_MODEL_RUNNER=http://host.docker.internal:12434/engines/llama.cpp/v1
```

On Linux (Docker Engine, not Docker Desktop), `host.docker.internal` may not resolve. Use the Docker bridge IP instead:

```bash
-e DOCKER_MODEL_RUNNER=http://172.17.0.1:12434/engines/llama.cpp/v1
```

### Agent produces empty or very short responses

The model may be too small for the structured output requirements. Switch to a larger model:

```bash
docker model pull ai/gemma3:4B-Q4_0
# Then set MODEL_NAME=ai/gemma3:4B-Q4_0
```

### `adk web` command not found

ADK is not installed or the virtual environment is not active:

```bash
source venv/bin/activate
pip install -r requirements.txt
adk web
```

### DataCompletenessChecker keeps retrying

This is normal if a model returns very short/empty responses. The checker retries up to 3 times. If it always fails after 3 retries, the model is likely too small — use a 4B+ parameter model.

---

## How the Code Is Organized

```
commute_advisor/
├── agent.py      # Pipeline definition — all agents wired together
├── models.py     # Pydantic schemas for typed structured output
├── tools.py      # Mock API tools for weather, train, bus, traffic, history
└── README.md     # This file
```

The shared configuration (model endpoint detection, LiteLLM setup) lives in:

```
shared/
└── config.py     # Auto-detects Docker Model Runner endpoint
```
