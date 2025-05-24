from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.parallel_agent import ParallelAgent
from google.genai import types
from google.adk.tools import google_search
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

GEMINI_MODEL="gemini-2.0-flash"

APP_NAME = "market_intel_app"
USER_ID = "biz_user_01"
SESSION_ID = "market_session"

competitor_agent = LlmAgent(
    name="CompetitorAnalyst",
    model=GEMINI_MODEL,
    instruction="""You are a Market Analyst AI.
    Analyze recent strategies of top competitors in the SaaS space.
    Use Google Search if needed.
    Summarize findings in 1-2 sentences.
    """,
    tools=[google_search],
    output_key="competitor_analysis"
)

trend_agent = LlmAgent(
    name="TrendDetector",
    model=GEMINI_MODEL,
    instruction="""You are a Business Trends AI.
    Identify emerging SaaS business trends from recent news and blogs.
    Use Google Search if needed.
    Provide a 1-2 sentence trend summary.
    """,
    tools=[google_search],
    output_key="trend_insights"
)

sentiment_agent = LlmAgent(
    name="SentimentAnalyzer",
    model=GEMINI_MODEL,
    instruction="""You are a Customer Sentiment AI.
    Analyze recent online sentiment (e.g. Twitter, Reddit, forums) about popular SaaS tools.
    Use Google Search.
    Summarize public sentiment in 1-2 sentences.
    """,
    tools=[google_search],
    output_key="sentiment_summary"
)

root_agent = ParallelAgent(
    name="MarketIntelAgent",
    sub_agents=[competitor_agent, trend_agent, sentiment_agent]
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

call_agent("Review market")