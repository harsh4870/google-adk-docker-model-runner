# ADK Docker Agent Suite

AI agents built using Google ADK and Docker model runners. This repository demonstrates scalable, modular agent architectures for various applications, combining lightweight LLMs with containerized execution for enhanced flexibility and integration.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Agents](#agents)
- [Contributing](#contributing)
- [License](#license)

## Overview

This project showcases different types of AI agents created using the Google Application Development Kit (ADK) integrated with Docker model runners. The architecture is designed to support multiple agents handling various tasks, such as travel planning, chatbots, or other AI-driven workflows. The use of Docker & Docker model runner ensures that model environments are consistent, portable, and easy to deploy.

## Prerequisites

Before running the agents, ensure you have the following installed on your machine:

- [Python 3.9+](https://www.python.org/downloads/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- `pip` package manager

## Agent Examples:

1. **[Find job agent](#sentiment-analysis):** Summarizes relevant job listings based on user input using contextual understanding

2. **[Google search agent](#named-entity-recognition):** Performs a live Google search and returns a summarized report of the top results

3. **[Human in loop agent](#text-classification):** Integrates human decisions into the agent workflow for critical checkpoints

4. **[Loop agent](#text-summarization):** Repeats a task or decision flow until a certain condition is met, enabling iterative refinement

5. **[Parallel agent](#text-translation):** Executes tasks in parallel flow to optimize performance and control
  
6. **[Sequential agent](#text-translation):** Executes tasks in sequential flow to optimize performance and control

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/harsh4870/google-adk-docker-model-runner.git
   cd google-adk-docker-model-runner

2. **Virtual Env & Install dependencies**

   ```bash
   python -m venv venv && source venv/bin/activate && pip install -r requirements.txt

3. **Run Examples:**
   
   Choose the specific agent you want to run:

     ```bash
     cd agents && adk web

4. **Open browser:**
   
   Visit url:

     ```bash
     http://localhost:8000/dev-ui

5. **Output**

<img width="1438" alt="Screenshot 2025-05-28 at 12 55 04 PM" src="https://github.com/user-attachments/assets/714862bb-75db-4b81-a8a4-82711c5792cc" />

6. **.env values**
   
   Google search agent uses the Google API & Gemini model, need to set the values in `agents/.env` file to use it

   ```bash
   GOOGLE_GENAI_USE_VERTEXAI=FALSE
   GOOGLE_API_KEY=add-your-key
   GOOGLE_CLOUD_LOCATION=us-central1
   
8. **Sample prompts**

    1. **[Find job agent](#find-job-agent):** `Share job related to python`
    
    2. **[Google search agent](#google-search):** `Share details about docker model runner features release`
    
    3. **[Human in loop agent](#human-in-loop):** `Plan a trip to dubai`
    
    4. **[Loop agent](#loop-agent):** `Suggest some healthy recipe with paneer`
    
    5. **[Parallel agent](#parralel-agent):** `Customer sentiment and feedback trends on Docker Model Runner and Docker AI`
      
    6. **[Sequential agent](#sequential-agent):** `Write a HTML code with title and description for front main website page`
  
## Running with Docker:

Set environment variable
  - GOOGLE_API_KEY
  - GOOGLE_CLOUD_LOCATION
  - DOCKER_MODEL_RUNNER

### **Pull image**  

   ```sh
   docker run -p 8000:8000 -e GOOGLE_API_KEY=add-gemini-api-key \
      -e GOOGLE_CLOUD_LOCATION=us-central1 \
      -e DOCKER_MODEL_RUNNER=http://model-runner.docker.internal/engines/llama.cpp/v1 \
   harshmanvar/google-adk-docker-model-runner:v1
   ```

  Open browser [http://localhost:8000](http://localhost:8000)

## Agents

- [find_jobs_agent](https://github.com/harsh4870/google-adk-docker-model-runner/tree/main/agents/find_jobs_agent)
- [google_search_agent](https://github.com/harsh4870/google-adk-docker-model-runner/tree/main/agents/google_search_agent)
- [human_in_loop_agent](https://github.com/harsh4870/google-adk-docker-model-runner/tree/main/agents/human_in_loop_agent)
- [loop_agent](https://github.com/harsh4870/google-adk-docker-model-runner/tree/main/agents/loop_agent)
- [parallel_agent](https://github.com/harsh4870/google-adk-docker-model-runner/tree/main/agents/parallel_agent)
- [sequential_agent](https://github.com/harsh4870/google-adk-docker-model-runner/tree/main/agents/sequential_agent)

