import requests
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

api_base_url="http://localhost:12434/engines/llama.cpp/v1"
model_name_at_endpoint="hosted_vllm/ai/llama3.2:1B-Q8_0"

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

root_agent = LlmAgent(
    model=LiteLlm(
        model=model_name_at_endpoint,
        api_base=api_base_url
    ),
    name="job_agent",
    description=(
        "Agent to answer on job findings"
    ),
    instruction=instruction_prompt,
    tools=[job] 
)