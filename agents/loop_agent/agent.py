import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import get_model_config, create_session, setup_logging
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.loop_agent import LoopAgent
from google.genai import types
from google.adk.runners import Runner

# Setup logging
logger = setup_logging()

APP_NAME = "chef_app"
USER_ID = "user_01"
SESSION_ID = "session_01"

STATE_RECIPE = "generated_recipe"
STATE_DIET_FEEDBACK = "diet_feedback"
STATE_MEAL_TYPE = "meal_type"

recipe_generator = LlmAgent(
    name="RecipeAgent",
    model=get_model_config(temperature=0.1),
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
    model=get_model_config(temperature=0.1),
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

async def call_agent(query):
    try:
        logger.info(f"🚀 Processing query: {query[:50]}...")
        
        # Create session
        session_service, session = await create_session(APP_NAME, USER_ID)
        
        # Create runner
        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service
        )
        
        # Prepare content
        content = types.Content(
            role='user',
            parts=[types.Part(text=query)]
        )
        
        # Execute pipeline
        events = runner.run_async(
            user_id=USER_ID,
            session_id=session.id,
            new_message=content
        )
        
        # Collect responses
        responses = []
        async for event in events:
            if event.is_final_response():
                response_text = event.content.parts[0].text
                responses.append({
                    'agent': event.author,
                    'response': response_text
                })
                logger.info(f"📝 {event.author}: {len(response_text)} characters")
        
        return responses
        
    except Exception as e:
        logger.error(f"❌ Pipeline execution failed: {e}")
        return [{'agent': 'error', 'response': f"Error: {str(e)}"}]

call_agent("Review Recipe")