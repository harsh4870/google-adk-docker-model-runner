from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.loop_agent import LoopAgent
from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

api_base_url="http://localhost:12434/engines/llama.cpp/v1"
model_name_at_endpoint="hosted_vllm/ai/llama3.2:1B-Q8_0"

APP_NAME = "code_app"
USER_ID = "user_01"
SESSION_ID = "session_01"

STATE_RECIPE = "generated_recipe"
STATE_DIET_FEEDBACK = "diet_feedback"
STATE_MEAL_TYPE = "meal_type"

recipe_generator = LlmAgent(
    name="RecipeAgent",
    model=LiteLlm(
        model=model_name_at_endpoint,
        api_base=api_base_url
    ),
    instruction=f"""
    You're a Creative Chef AI.
    Use '{STATE_MEAL_TYPE}' from state to generate a healthy meal recipe.
    If feedback exists in '{STATE_DIET_FEEDBACK}', modify the recipe accordingly.
    Output only the recipe.
    """,
    description="Generates or improves a recipe.",
    output_key=STATE_RECIPE
)

dietician_agent = LlmAgent(
    name="DieticianAgent",
    model=LiteLlm(
        model=model_name_at_endpoint,
        api_base=api_base_url
    ),
    instruction=f"""
    You're a Dietician AI.
    Review the recipe in '{STATE_RECIPE}'.
    Suggest 1-2 brief improvements (e.g., reduce sugar, add protein).
    Output only the feedback.
    """,
    description="Gives nutritional feedback on the recipe.",
    output_key=STATE_DIET_FEEDBACK
)

root_agent = LoopAgent(
    name="RecipeDietLoop", sub_agents=[recipe_generator, dietician_agent], max_iterations=2
)

session_service = InMemorySessionService()
session = session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

def call_agent(query):
    content = types.Content(role='user', parts=[types.Part(text=query)])
    events = runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("Agent Response: ", final_response)

call_agent("Review Recipe")