import sys
import os
import requests

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import get_model_config, setup_logging
from google.adk.agents.llm_agent import LlmAgent

# Setup logging
logger = setup_logging()

# Configuration
APP_NAME = "job_search_agent"
USER_ID = "job_seeker"

def job(skill: str):
    url = f"https://jobicy.com/api/v2/remote-jobs?tag={skill}&count=10"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        print("Response :", data)
        return data
    except requests.exceptions.HTTPError as err:
        print("HTTP error occurred :", err)
        return None
    except Exception as err:
        print("Other error occurred :", err)
        return None

instruction_prompt = """
    You're an intelligent job-matching assistant designed to help users find relevant job listings based on the skills they provide.
    Use the job tool to fetch job data — it returns JSON format with job listings inside the "jobs" array.
    For each relevant job found, extract and present key details such as:
    Job Title
    Company Name
    Location
    Salary (if available)
    Short Description
    Make sure to match the user's input with job titles, keywords, or descriptions. Return a concise summary of the top relevant jobs, formatting the output clearly so the user can easily compare options.
"""

# Job analyzer
root_agent = LlmAgent(
    name="JobAnalyzer",
    model=get_model_config(),
    instruction=instruction_prompt,
    description=(
        "Agent to answer on job findings"
    ),
    tools=[job]
)