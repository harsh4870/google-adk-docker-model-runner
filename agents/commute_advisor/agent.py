"""
Commute Advisor — Multi-Agent Intelligence System
==================================================

Architecture:

  CommutePipeline  (SequentialAgent)
  ├── DataGatheringLoop  (LoopAgent, max 3 iterations)
  │   ├── ParallelDataFetcher  (ParallelAgent — all 4 run concurrently)
  │   │   ├── WeatherFetcher   (BaseAgent — calls Python directly, no LLM)
  │   │   ├── TrainFetcher     (BaseAgent — calls Python directly, no LLM)
  │   │   ├── BusFetcher       (BaseAgent — calls Python directly, no LLM)
  │   │   └── TrafficFetcher   (BaseAgent — calls Python directly, no LLM)
  │   └── DataCompletenessChecker  (BaseAgent — escalates loop when all data present)
  ├── HistoryFetcher   (BaseAgent — personalization data)
  ├── CommuteAnalyzer  (LlmAgent — structured Pydantic output via output_schema)
  └── RecommendationPresenter  (LlmAgent — human-readable briefing)

Data fetching uses BaseAgent subclasses (no LLM tool calls) so the pipeline
works with any model size, including small local models via Docker Model Runner.
LlmAgents are used only for analysis and synthesis where reasoning is needed.
"""

import asyncio
import json
import os
import sys
from typing import AsyncGenerator

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))
sys.path.append(os.path.dirname(__file__))

from config import get_model_config, create_session, setup_logging
from models import CommuteRecommendation
from tools import (
    get_bus_status,
    get_historical_commute_patterns,
    get_traffic_conditions,
    get_train_status,
    get_weather_data,
)

from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.loop_agent import LoopAgent
from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.events import Event, EventActions
from google.adk.runners import Runner
from google.genai import types

logger = setup_logging()

# --------------------------------------------------------------------------- #
# Commute parameters — override via environment variables
# --------------------------------------------------------------------------- #

ORIGIN = os.getenv("COMMUTE_ORIGIN", "London Bridge")
DESTINATION = os.getenv("COMMUTE_DESTINATION", "Canary Wharf")
BUS_ROUTE = os.getenv("COMMUTE_BUS_ROUTE", "188")
USER_ID = os.getenv("COMMUTE_USER_ID", "commuter_001")
APP_NAME = "commute_advisor"

# --------------------------------------------------------------------------- #
# BaseAgent data fetchers
# Calling Python functions directly avoids LLM tool calls, which require
# models that support function calling. These work with any model size.
# --------------------------------------------------------------------------- #


class WeatherFetcher(BaseAgent):
    """Fetches weather data and stores raw JSON in session state."""

    async def _run_async_impl(self, ctx) -> AsyncGenerator[Event, None]:
        try:
            data = get_weather_data(ORIGIN)
            ctx.session.state["weather_raw"] = json.dumps(data, indent=2)
            logger.info("[WeatherFetcher] OK")
        except Exception as e:
            logger.error(f"[WeatherFetcher] Failed: {e}")
        yield Event(author=self.name, actions=EventActions(escalate=False))


class TrainFetcher(BaseAgent):
    """Fetches train status and stores raw JSON in session state."""

    async def _run_async_impl(self, ctx) -> AsyncGenerator[Event, None]:
        try:
            data = get_train_status(ORIGIN, DESTINATION)
            ctx.session.state["train_raw"] = json.dumps(data, indent=2)
            logger.info("[TrainFetcher] OK")
        except Exception as e:
            logger.error(f"[TrainFetcher] Failed: {e}")
        yield Event(author=self.name, actions=EventActions(escalate=False))


class BusFetcher(BaseAgent):
    """Fetches bus status and stores raw JSON in session state."""

    async def _run_async_impl(self, ctx) -> AsyncGenerator[Event, None]:
        try:
            data = get_bus_status(BUS_ROUTE)
            ctx.session.state["bus_raw"] = json.dumps(data, indent=2)
            logger.info("[BusFetcher] OK")
        except Exception as e:
            logger.error(f"[BusFetcher] Failed: {e}")
        yield Event(author=self.name, actions=EventActions(escalate=False))


class TrafficFetcher(BaseAgent):
    """Fetches traffic conditions and stores raw JSON in session state."""

    async def _run_async_impl(self, ctx) -> AsyncGenerator[Event, None]:
        try:
            data = get_traffic_conditions(ORIGIN, DESTINATION)
            ctx.session.state["traffic_raw"] = json.dumps(data, indent=2)
            logger.info("[TrafficFetcher] OK")
        except Exception as e:
            logger.error(f"[TrafficFetcher] Failed: {e}")
        yield Event(author=self.name, actions=EventActions(escalate=False))


class HistoryFetcher(BaseAgent):
    """Fetches historical commute patterns and stores raw JSON in session state."""

    async def _run_async_impl(self, ctx) -> AsyncGenerator[Event, None]:
        try:
            data = get_historical_commute_patterns(USER_ID, ORIGIN, DESTINATION)
            ctx.session.state["history_raw"] = json.dumps(data, indent=2)
            logger.info("[HistoryFetcher] OK")
        except Exception as e:
            logger.error(f"[HistoryFetcher] Failed: {e}")
        yield Event(author=self.name, actions=EventActions(escalate=False))


# --------------------------------------------------------------------------- #
# DataCompletenessChecker (BaseAgent subclass)
# Validates that all four data sources returned non-empty content.
# Yields Event(escalate=True) when complete → LoopAgent stops.
# Yields Event() with no escalation when data missing → LoopAgent retries.
# --------------------------------------------------------------------------- #

REQUIRED_DATA_KEYS = ["weather_raw", "train_raw", "bus_raw", "traffic_raw"]


class DataCompletenessChecker(BaseAgent):
    """
    Validates all four data sources returned non-empty content.
    Escalates the LoopAgent when complete; signals retry when any source is missing.
    """

    async def _run_async_impl(self, ctx) -> AsyncGenerator[Event, None]:
        missing = [k for k in REQUIRED_DATA_KEYS if not ctx.session.state.get(k)]

        if missing:
            logger.warning(f"[DataCompletenessChecker] Missing: {missing} — retrying")
            yield Event(author=self.name, actions=EventActions(escalate=False))
        else:
            logger.info("[DataCompletenessChecker] All data sources complete — escalating")
            yield Event(author=self.name, actions=EventActions(escalate=True))


# --------------------------------------------------------------------------- #
# ParallelAgent: fires all 4 fetchers concurrently
# --------------------------------------------------------------------------- #

parallel_data_fetcher = ParallelAgent(
    name="ParallelDataFetcher",
    sub_agents=[
        WeatherFetcher(name="WeatherFetcher", description="Fetches weather data."),
        TrainFetcher(name="TrainFetcher", description="Fetches train status."),
        BusFetcher(name="BusFetcher", description="Fetches bus status."),
        TrafficFetcher(name="TrafficFetcher", description="Fetches traffic conditions."),
    ],
    description="Concurrently fetches weather, train, bus, and traffic data.",
)

data_completeness_checker = DataCompletenessChecker(
    name="DataCompletenessChecker",
    description="Validates all commute data sources returned complete data.",
)

# --------------------------------------------------------------------------- #
# LoopAgent: wraps parallel fetch + completeness check
# --------------------------------------------------------------------------- #

data_gathering_loop = LoopAgent(
    name="DataGatheringLoop",
    sub_agents=[parallel_data_fetcher, data_completeness_checker],
    max_iterations=3,
    description="Fetches all commute data in parallel, retrying up to 3 times if any source fails.",
)

# --------------------------------------------------------------------------- #
# HistoryAgent: personalization (runs after data gathering)
# --------------------------------------------------------------------------- #

history_fetcher = HistoryFetcher(
    name="HistoryFetcher",
    description="Fetches user's historical commute patterns for personalization.",
)

# --------------------------------------------------------------------------- #
# CommuteAnalyzer: synthesizes all raw data → structured Pydantic output
# Reads pre-fetched JSON from session state — no tool calls needed.
# --------------------------------------------------------------------------- #

commute_analyzer = LlmAgent(
    name="CommuteAnalyzer",
    model=get_model_config(temperature=0.1),
    instruction=f"""You are an expert commute intelligence analyst.

Route: {ORIGIN} → {DESTINATION}

The following raw JSON data is available in session state. Read and analyze ALL of it:

  state['weather_raw']  — weather conditions and impact
  state['train_raw']    — train service status and delays
  state['bus_raw']      — bus service status and capacity
  state['traffic_raw']  — road conditions and congestion
  state['history_raw']  — user's historical patterns and preferences

ANALYSIS METHODOLOGY:
1. Identify corroborating signals (e.g., bad weather + road flooding → avoid driving)
2. Identify conflicts (e.g., train delayed but bus on time → recommend bus)
3. Calculate realistic journey time per mode:
   - Train: delay_minutes from train_raw + 5 min buffer if crowding is 'high'
   - Bus: delay_minutes from bus_raw + contingency if capacity_percent > 85
   - Drive: travel_time_current_minutes from traffic_raw
4. Weight against user's historical preference from history_raw
5. Escalate severity if multiple modes are simultaneously disrupted

SEVERITY MAPPING:
  all_clear             → all modes functioning normally
  minor_disruption      → 1 mode has minor delays (< 15 min)
  significant_disruption → 1 mode major delay OR 2 modes minor delays
  severe_disruption     → 2+ modes major delays or 1 suspended
  do_not_commute        → all modes severely affected OR critical weather advisory

CONFIDENCE SCORING:
  1.0 → all 4 data sources complete and consistent
  0.8 → 3 of 4 sources complete
  0.6 → 2 of 4 sources complete or signals conflict
  0.4 → data quality poor or sources contradicting

Output a valid CommuteRecommendation JSON with ALL fields populated.
Be decisive — the commuter needs a clear, unambiguous recommendation.""",
    description="Synthesizes all commute data into a structured typed recommendation.",
    output_schema=CommuteRecommendation,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    output_key="commute_recommendation",
)

# --------------------------------------------------------------------------- #
# RecommendationPresenter: formats structured output for humans
# --------------------------------------------------------------------------- #

recommendation_presenter = LlmAgent(
    name="RecommendationPresenter",
    model=get_model_config(temperature=0.2),
    instruction=f"""You are a commute assistant delivering a morning briefing.

Read from session state:
  state['commute_recommendation'] — structured CommuteRecommendation JSON
  state['weather_raw']            — raw weather data
  state['train_raw']              — raw train data
  state['bus_raw']                — raw bus data
  state['traffic_raw']            — raw traffic data
  state['history_raw']            — user personalization

Format the final briefing exactly as shown below.
Replace all [PLACEHOLDER] values with real data from the state.

---
COMMUTE ADVISOR — {ORIGIN} → {DESTINATION}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STATUS: [ALL CLEAR | MINOR DISRUPTION | SIGNIFICANT DISRUPTION | SEVERE | DO NOT COMMUTE]

RECOMMENDATION
  Mode:       [recommended transport mode]
  Duration:   ~[X] minutes
  Confidence: [X%]

CONDITION SUMMARY
  Weather  [weather conditions + impact level]
  Train    [line, status, delay if any]
  Bus      [route, status, capacity if notable]
  Traffic  [congestion level + travel time vs normal]

ALERTS
  [bullet each primary_alert on its own line with a dash]

ADVICE
  [actionable_advice from CommuteRecommendation — 2-3 sentences max]

BACKUP PLAN
  [backup_plan or 'No backup needed — primary mode reliable']

Data freshness: [data_freshness timestamp]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
---

Keep it scannable. Commuters read this while rushing out the door.
No extra prose. Stick to the format above exactly.""",
    description="Formats the structured recommendation into a human-readable commute briefing.",
    output_key="final_briefing",
)

# --------------------------------------------------------------------------- #
# Root Agent — Full Pipeline
# --------------------------------------------------------------------------- #

root_agent = SequentialAgent(
    name="CommuteAdvisor",
    sub_agents=[
        data_gathering_loop,
        history_fetcher,
        commute_analyzer,
        recommendation_presenter,
    ],
    description=(
        "Full commute intelligence pipeline: "
        "parallel data gathering (with retry) → personalization → "
        "structured analysis → human briefing"
    ),
)


# --------------------------------------------------------------------------- #
# Runner utilities
# --------------------------------------------------------------------------- #


async def get_commute_briefing(query: str) -> list[dict]:
    """Execute the full commute advisor pipeline and return agent responses."""
    logger.info(f"Starting Commute Advisor: {ORIGIN} → {DESTINATION}")

    session_service, session = await create_session(APP_NAME, USER_ID)

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    content = types.Content(
        role="user",
        parts=[types.Part(text=query)],
    )

    responses = []
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session.id,
        new_message=content,
    ):
        if event.is_final_response():
            agent_name = event.author
            response_text = event.content.parts[0].text if event.content.parts else ""
            responses.append({"agent": agent_name, "response": response_text})
            logger.info(f"  [{agent_name}] completed ({len(response_text)} chars)")

    return responses


async def main():
    """Demo entry point — runs a sample commute query."""
    query = os.getenv(
        "COMMUTE_QUERY",
        f"What is my commute looking like today from {ORIGIN} to {DESTINATION}? "
        f"I normally take the train but want to know all my options.",
    )

    print(f"\n{'═' * 60}")
    print("  COMMUTE ADVISOR  — Multi-Agent Intelligence System")
    print(f"  Route: {ORIGIN} → {DESTINATION}")
    print(f"{'═' * 60}\n")
    print("Running agents:")
    print("  1. ParallelDataFetcher  (weather + train + bus + traffic)")
    print("  2. DataCompletenessChecker  (validate / retry)")
    print("  3. HistoryFetcher  (personalization)")
    print("  4. CommuteAnalyzer  (structured synthesis)")
    print("  5. RecommendationPresenter  (human briefing)")
    print()

    responses = await get_commute_briefing(query)

    for r in responses:
        if r["agent"] == "RecommendationPresenter":
            print("\n" + "═" * 60)
            print(r["response"])
            print("═" * 60)
        elif r["agent"] == "CommuteAnalyzer":
            print(f"\n[CommuteAnalyzer structured output]")
            try:
                parsed = json.loads(r["response"])
                print(json.dumps(parsed, indent=2))
            except json.JSONDecodeError:
                print(r["response"][:300])
        else:
            logger.debug(f"[{r['agent']}]: {r['response'][:80]}...")

    logger.info("Commute briefing complete.")


if __name__ == "__main__":
    asyncio.run(main())
