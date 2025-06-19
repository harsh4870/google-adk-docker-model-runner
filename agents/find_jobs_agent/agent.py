"""
Fixed Find Job Agent with container-aware configuration.
Searches for job listings and provides contextual summaries.
"""

import asyncio
import sys
import os

# Add the shared module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import get_model_config, create_session, setup_logging
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.runners import Runner
from google.adk.tools import google_search
from google.genai import types

# Setup logging
logger = setup_logging()

# Configuration
APP_NAME = "job_search_agent"
USER_ID = "job_seeker"

# FIXED: Using centralized configuration instead of hardcoded endpoints

# Job search agent
job_searcher = LlmAgent(
    name="JobSearcher",
    model=get_model_config(temperature=0.2),
    instruction="""You are a professional job search specialist.

    Search for job opportunities based on the user's criteria using Google Search.
    Focus on finding:
    - Current job openings
    - Relevant job boards and company career pages
    - Salary ranges and compensation information
    - Required skills and qualifications
    - Remote work opportunities
    - Industry-specific job sites

    Gather comprehensive job market information for the specified role/field.
    """,
    description="Searches for job opportunities and market information.",
    tools=[google_search],
    output_key="job_search_results"
)

# Job analyzer
job_analyzer = LlmAgent(
    name="JobAnalyzer",
    model=get_model_config(temperature=0.1),
    instruction="""You are a career advisor and job market analyst.

    Analyze the job search results from state['job_search_results'] and provide:

    1. **Job Market Overview**
       - Current demand for the role
       - Average salary ranges
       - Most common requirements
       - Growth trends

    2. **Top Job Opportunities**
       - Best specific job listings found
       - Company information and reputation
       - Role requirements and responsibilities
       - Application process and deadlines

    3. **Skills Analysis**
       - Most in-demand skills for this role
       - Skills gaps to address
       - Certification or training recommendations

    4. **Career Advice**
       - Application strategy recommendations
       - Interview preparation tips
       - Networking suggestions
       - Portfolio/resume optimization tips

    5. **Next Steps**
       - Immediate action items
       - Long-term career development
       - Resources for skill development

    Present findings in a clear, actionable format that helps with job search strategy.
    """,
    description="Analyzes job market data and provides career guidance.",
    output_key="job_analysis"
)

# Create the sequential pipeline
root_agent = SequentialAgent(
    name="JobSearchAnalyzer",
    sub_agents=[job_searcher, job_analyzer],
    description="Searches for jobs and provides comprehensive career analysis."
)


async def find_jobs(job_query: str):
    """Find and analyze job opportunities"""
    try:
        logger.info(f"💼 Searching for jobs: {job_query[:50]}...")

        # Create session
        session_service, session = await create_session(APP_NAME, USER_ID)

        # Create runner
        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service
        )

        # Enhance query with job search context
        enhanced_query = f"""
        Find current job opportunities related to: {job_query}

        Please search for:
        - Current job openings and listings
        - Salary information and compensation
        - Required skills and qualifications
        - Remote work opportunities
        - Career growth prospects
        - Industry demand and trends

        Focus on actionable job search information.
        """

        # Prepare content
        content = types.Content(
            role='user',
            parts=[types.Part(text=enhanced_query)]
        )

        logger.info("🔍 Searching job boards and career sites...")
        logger.info("📊 Analyzing job market trends...")
        logger.info("💡 Generating career recommendations...")

        # Execute pipeline
        events = runner.run_async(
            user_id=USER_ID,
            session_id=session.id,
            new_message=content
        )

        # Collect responses
        search_results = None
        analysis = None

        async for event in events:
            if event.is_final_response():
                if event.author == "JobSearcher":
                    search_results = event.content.parts[0].text
                elif event.author == "JobAnalyzer":
                    analysis = event.content.parts[0].text

                logger.info(f"📝 {event.author}: {len(event.content.parts[0].text)} characters")

        return {
            'search_results': search_results,
            'analysis': analysis
        }

    except Exception as e:
        logger.error(f"❌ Job search failed: {e}")
        return {'error': str(e)}


async def main():
    """Main execution function"""
    try:
        logger.info("🚀 Starting Job Search Agent...")

        # Test job search queries
        test_queries = [
            os.getenv("TEST_QUERY", "Python developer jobs remote"),
            "Data scientist positions in technology companies",
            "DevOps engineer roles with Kubernetes experience",
            "Frontend developer jobs with React and TypeScript"
        ]

        for i, query in enumerate(test_queries[:1], 1):  # Run first query only by default
            print(f"\n{'='*80}")
            print(f"💼 Job Search {i}")
            print(f"📋 Query: {query}")
            print('='*80)

            result = await find_jobs(query)

            if 'error' in result:
                print(f"❌ Error: {result['error']}")
                continue

            # Display search results
            if result.get('search_results'):
                print(f"\n🔍 Job Search Results:")
                print("-" * 50)
                search_preview = result['search_results'][:800] + "..." if len(result['search_results']) > 800 else result['search_results']
                print(search_preview)

            # Display analysis
            if result.get('analysis'):
                print(f"\n📊 Job Market Analysis & Career Advice:")
                print("-" * 50)
                # Show the full analysis as it's the most valuable output
                if len(result['analysis']) > 1500:
                    print(result['analysis'][:1500] + "\n... [analysis continues] ...")
                else:
                    print(result['analysis'])

        logger.info("✅ Job search analysis completed!")

    except Exception as e:
        logger.error(f"❌ Main execution failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())