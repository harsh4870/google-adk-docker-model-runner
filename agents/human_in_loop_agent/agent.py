from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools import FunctionTool
from typing import Optional

APP_NAME = "travel_planner"
USER_ID = "user_01"
SESSION_ID = "session_travel_01"

api_base_url = "http://localhost:12434/engines/llama.cpp/v1"
model_name_at_endpoint = "hosted_vllm/ai/llama3.2:1B-Q8_0"


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
    model=LiteLlm(model=model_name_at_endpoint, api_base=api_base_url),
    instruction="""
    Suggest a relaxing travel destination for a 3-day solo trip.
    Just name the destination with 1 short sentence explaining why.
    Output only the destination and reasoning.
    """,
    output_key="suggested_destination"
)

activity_agent = LlmAgent(
    name="ActivityPlanner",
    model=LiteLlm(model=model_name_at_endpoint, api_base=api_base_url),
    instruction="""
    Based on the destination in state key 'suggested_destination', suggest 2-3 unique things to do there.
    Summarize in 2-3 bullet points.
    Output only the activities.
    """,
    output_key="planned_activities"
)

human_approval_agent = LlmAgent(
    name="RequestHumanApproval",
    model=LiteLlm(model=model_name_at_endpoint, api_base=api_base_url),
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
    model=LiteLlm(model=model_name_at_endpoint, api_base=api_base_url),
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
session = session_service.create_session(
    app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
)
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

def call_agent(query, user_input=None):
    """
    query: initial user message
    user_input: input for approval or change step (yes/no/destination/days)
    """
    content = types.Content(role='user', parts=[types.Part(text=query)])
    events = runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    for event in events:
        if event.is_final_response():
            print("\n Final Response:")

call_agent("Plan a short relaxing trip for me.")
