from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools import FunctionTool
from typing import Optional
import os
import asyncio

APP_NAME = "travel_planner"
USER_ID = "user_01"
SESSION_ID = "session_travel_01"

def get_docker_model_runner_endpoint():
    """Get Docker Model Runner endpoint with environment detection."""
    explicit_endpoint = os.environ.get('DOCKER_MODEL_RUNNER')
    if explicit_endpoint:
        print(f"Using explicit DOCKER_MODEL_RUNNER: {explicit_endpoint}")
        return explicit_endpoint

    if _is_running_in_container():
        endpoint = "http://model-runner.docker.internal/engines/llama.cpp/v1"
        print("Detected container environment - using docker.internal endpoint")
    else:
        endpoint = "http://localhost:12434/engines/llama.cpp/v1"
        print("Detected host environment - using localhost endpoint")

    return endpoint

def _is_running_in_container():
    """Detect if we're running inside a Docker container."""
    try:
        return (
            os.path.exists('/.dockerenv') or
            (os.path.exists('/proc/self/cgroup') and 'docker' in open('/proc/self/cgroup', 'r').read())
        )
    except:
        return False

# Configuration
api_base_url = get_docker_model_runner_endpoint()
model_name_at_endpoint = "openai/ai/llama3.2:1B-Q8_0"

# Set environment variables
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "anything")
os.environ["OPENAI_API_BASE"] = api_base_url

print(f"Configuration:")
print(f"  API Base URL: {api_base_url}")
print(f"  Model: {model_name_at_endpoint}")

def ask_for_human_approval(planned_activities: str, user_input: Optional[str] = None) -> str:
    if user_input is None:
        return "pending"

    user_input = user_input.lower().strip()
    if user_input in ["yes", "y"]:
        return "yes"
    elif user_input in ["no", "n"]:
        return "no"
    else:
        return "pending"

approval_tool = FunctionTool(func=ask_for_human_approval)


destination_agent = LlmAgent(
    name="DestinationSuggester",
    model=LiteLlm(
        model=model_name_at_endpoint,
        api_base=api_base_url,
        api_key="anything"
    ),
    instruction="""
    Suggest a relaxing travel destination for a 3-day solo trip.
    Just name the destination with 1 short sentence explaining why.
    Output only the destination and reasoning.
    """,
    output_key="suggested_destination"
)

activity_agent = LlmAgent(
    name="ActivityPlanner",
    model=LiteLlm(
        model=model_name_at_endpoint,
        api_base=api_base_url,
        api_key="anything"
    ),
    instruction="""
    Based on the destination in state key 'suggested_destination', suggest 2-3 unique things to do there.
    Summarize in 2-3 bullet points.
    Output only the activities.
    """,
    output_key="planned_activities"
)

human_approval_agent = LlmAgent(
    name="RequestHumanApproval",
    model=LiteLlm(
        model=model_name_at_endpoint,
        api_base=api_base_url,
        api_key="anything"
    ),
    instruction="""
    Use the ask_for_human_approval tool with planned_activities from state.
    The tool will prompt for approval or for choices after rejection.
    Save the approval status or next action in state key 'user_approval' or 'user_next_action'.
    """,
    tools=[approval_tool],
    output_key="user_approval"
)

final_agent = LlmAgent(
    name="FinalConfirmer",
    model=LiteLlm(
        model=model_name_at_endpoint,
        api_base=api_base_url,
        api_key="anything"
    ),
    instruction="""
    If state 'user_approval' is 'yes', confirm the travel plan by combining the destination and activities.

    If state 'user_approval' is 'no',
    check 'user_next_action':
      - If 'change_destination', delete 'suggested_destination' from state.
      - If 'change_days', ask user for new number of days and update 'trip_duration'.
    Then reply with "Okay! Restarting with your updated preferences."

    Otherwise, say "Plan rejected by user."
    """,
    output_key="final_confirmation"
)

root_agent = SequentialAgent(
    name="CoordinatorAgent",
    sub_agents=[
        destination_agent,
        activity_agent,
        human_approval_agent,
        final_agent
    ]
)

session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

async def setup_and_run_agent():
    """Set up session and run the agent properly."""

    session = await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    print("Session created successfully!")

    query = "Plan a short relaxing trip for me."
    content = types.Content(role='user', parts=[types.Part(text=query)])

    print(f"\nSending query: {query}")
    print("Processing...")

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content
    ):
        if event.is_final_response():
            print("\n✅ Final Response:")
            print(event.content.parts[0].text)
            break

if __name__ == "__main__":
    asyncio.run(setup_and_run_agent())