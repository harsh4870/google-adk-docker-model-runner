from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

api_base_url="http://localhost:12434/engines/llama.cpp/v1"
model_name_at_endpoint="hosted_vllm/ai/llama3.2:1B-Q8_0"

APP_NAME = "code_app"
USER_ID = "user_01"
SESSION_ID = "session_01"

code_writer_agent = LlmAgent(
    name="CodeWriterAgent",
    model=LiteLlm(
        model=model_name_at_endpoint,
        api_base=api_base_url
    ),
    instruction="""You are a Code Writer AI.
    Based on the user's request, write the initial HTML code.
    Output *only* the raw code block.
    """,
    description="Writes initial code based on a specification.",
    output_key="generated_code"
)

code_reviewer_agent = LlmAgent(
    name="CodeReviewerAgent",
    model=LiteLlm(
        model=model_name_at_endpoint,
        api_base=api_base_url
    ),
    instruction="""You are a Code Reviewer AI.
    Review the HTML code provided in the session state under the key 'generated_code'.
    Provide constructive feedback on potential errors, style issues, or improvements.
    Focus on clarity and correctness.
    Output only the review comments.
    """,
    description="Reviews code and provides feedback.",
    output_key="review_comments"
)

code_refactor_agent = LlmAgent(
    name="CodeRefactorerAgent",
    model=LiteLlm(
        model=model_name_at_endpoint,
        api_base=api_base_url
    ),
    instruction="""You are a Code Refactorer AI.
    Take the original HTML code provided in the session state key 'generated_code'
    and the review comments found in the session state key 'review_comments'.
    Refactor the original code to address the feedback and improve its quality.
    Output *only* the final, refactored code block.
    """,
    description="Refactors code based on review comments.",
    output_key="refactored_code"
)

root_agent = SequentialAgent(
    name="CodePipelineAgent",
    sub_agents=[code_writer_agent, code_reviewer_agent, code_refactor_agent]
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

call_agent("Review code")