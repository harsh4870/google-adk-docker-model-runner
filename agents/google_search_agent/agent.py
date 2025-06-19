"""
Fixed Google Search Agent with container-aware configuration.
Performs live Google searches and provides summarized reports.
"""

import asyncio
import sys
import os

# Add the shared module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import get_gemini_model, create_session, setup_logging
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.tools import google_search
from google.genai import types

# Setup logging
logger = setup_logging()

# Configuration
APP_NAME = "google_search_agent"
USER_ID = "researcher"

# FIXED: Using centralized configuration instead of hardcoded endpoints
# Now supports both local LLM and Gemini based on environment variables

def get_search_model():
    """Get the appropriate model for search agent"""
    google_api_key = os.getenv("GOOGLE_API_KEY")

    if google_api_key:
        logger.info("✅ Using Gemini model for Google Search agent")
        return get_gemini_model()
    else:
        logger.info("⚠️ No GOOGLE_API_KEY found, using local model")
        from config import get_model_config
        return get_model_config(temperature=0.2)

# Google Search Agent
search_agent = LlmAgent(
    name="GoogleSearchAgent",
    model=get_search_model(),
    instruction="""You are a professional research analyst specializing in web search and information synthesis.

    When given a search query:
    1. Use the Google Search tool to find the most relevant and recent information
    2. Analyze multiple search results to get comprehensive coverage
    3. Synthesize findings into a clear, well-structured report
    4. Include key facts, trends, and insights
    5. Cite sources when mentioning specific information
    6. Highlight the most important findings at the beginning

    Structure your response as:
    - Executive Summary (key findings)
    - Detailed Analysis (organized by topic/theme)
    - Key Statistics (if relevant)
    - Recent Developments
    - Sources and References

    Be objective, accurate, and provide actionable insights.
    """,
    description="Performs Google searches and creates comprehensive research reports.",
    tools=[google_search]
)

# Create the root agent
root_agent = search_agent


async def perform_research(search_query: str):
    """Perform Google search research on a topic"""
    try:
        logger.info(f"🔍 Researching: {search_query[:50]}...")

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
            parts=[types.Part(text=f"Research and provide a comprehensive report on: {search_query}")]
        )

        logger.info("🌐 Performing Google search...")
        logger.info("📊 Analyzing results...")
        logger.info("📝 Generating research report...")

        # Execute search and analysis
        events = runner.run_async(
            user_id=USER_ID,
            session_id=session.id,
            new_message=content
        )

        # Collect response
        async for event in events:
            if event.is_final_response():
                return event.content.parts[0].text

        return None

    except Exception as e:
        logger.error(f"❌ Research failed: {e}")
        return f"Error performing research: {str(e)}"


async def main():
    """Main execution function"""
    try:
        logger.info("🚀 Starting Google Search Research Agent...")

        # Check if Google API key is available
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            logger.warning("⚠️ GOOGLE_API_KEY not found. Google Search may not work properly.")
            logger.info("💡 Set GOOGLE_API_KEY environment variable to enable Google Search.")

        # Test research queries
        test_queries = [
            os.getenv("TEST_QUERY", "Docker Model Runner features and recent updates"),
            "Latest trends in AI agent development frameworks 2025",
            "Google ADK Agent Development Kit capabilities and use cases",
            "Container orchestration platforms comparison 2025"
        ]

        for i, query in enumerate(test_queries[:1], 1):  # Run first query only by default
            print(f"\n{'='*80}")
            print(f"🧪 Research Task {i}")
            print(f"📋 Query: {query}")
            print('='*80)

            result = await perform_research(query)

            if result:
                print(f"\n📊 Research Report:")
                print("-" * 50)
                # Display the research report
                if len(result) > 2000:
                    print(result[:2000] + "\n... [report continues] ...")
                else:
                    print(result)
            else:
                print("❌ No results returned")

        logger.info("✅ Google search research completed!")

    except Exception as e:
        logger.error(f"❌ Main execution failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())