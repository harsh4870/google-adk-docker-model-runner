from google.adk.agents import LlmAgent, Agent
from google.adk.tools import google_search

GEMINI_MODEL="gemini-2.0-flash"

instruction_prompt = """
    You are a research-savvy news assistant tasked with delivering concise updates on any topic the user provides.
    Use Google Search to gather the latest and most relevant information. Based on the results, generate a brief overview (1–2 paragraphs) that accurately summarizes the current state of the topic.
    Focus on clarity, relevance, and recency to ensure the user gets a quick, reliable snapshot of what is happening.
"""

root_agent = Agent(
    name="news_agent",
    model=GEMINI_MODEL,
    description="Google search and provide a summary on topic",
    instruction=instruction_prompt,
    tools=[google_search]
)