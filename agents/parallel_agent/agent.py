"""
Fixed Parallel Agent with container-aware configuration.
Executes multiple market analysis agents in parallel.
"""

import asyncio
import sys
import os

# Add the shared module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import get_gemini_model, get_model_config, create_session, setup_logging
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.runners import Runner
from google.adk.tools import google_search
from google.genai import types

# Setup logging
logger = setup_logging()

# Configuration
APP_NAME = "parallel_market_intelligence"
USER_ID = "analyst"


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

# Define parallel analysis agents
competitor_analyst = LlmAgent(
    name="CompetitorAnalyst",
    model=get_search_model(),
    instruction="""You are a competitive intelligence analyst.
    Analyze competitor strategies, market positioning, and recent developments.
    Focus on actionable insights about competitive landscape.
    Provide a structured analysis with key findings and recommendations.
    """,
    description="Analyzes competitor strategies and market positioning.",
    tools=[google_search],
    output_key="competitor_analysis"
)

trend_detector = LlmAgent(
    name="TrendDetector",
    model=get_search_model(),
    instruction="""You are a trend analysis specialist.
    Identify emerging market trends, technology developments, and industry shifts.
    Focus on forward-looking insights and potential impact on business.
    Provide trend analysis with supporting evidence and implications.
    """,
    description="Identifies emerging market trends and developments.",
    tools=[google_search],
    output_key="trend_analysis"
)

sentiment_analyzer = LlmAgent(
    name="SentimentAnalyzer",
    model=get_search_model(),
    instruction="""You are a customer sentiment analysis expert.
    Analyze customer feedback, reviews, and market sentiment indicators.
    Focus on customer perception, satisfaction levels, and pain points.
    Provide sentiment summary with key themes and actionable insights.
    """,
    description="Analyzes customer sentiment and feedback patterns.",
    tools=[google_search],
    output_key="sentiment_analysis"
)

# Create parallel execution group
parallel_research_agent = ParallelAgent(
    name="ParallelMarketResearch",
    sub_agents=[competitor_analyst, trend_detector, sentiment_analyzer],
    description="Executes market research tasks in parallel for comprehensive analysis."
)

# Create summary agent to synthesize parallel results
summary_agent = LlmAgent(
    name="MarketIntelligenceSynthesizer",
    model=get_model_config(temperature=0.1),
    instruction="""You are a senior market intelligence director.

    Synthesize findings from the parallel research agents:
    - Competitor Analysis from state['competitor_analysis']
    - Trend Analysis from state['trend_analysis']
    - Sentiment Analysis from state['sentiment_analysis']

    Create a comprehensive market intelligence report with:
    1. Executive Summary (key insights)
    2. Competitive Landscape Overview
    3. Emerging Trends & Opportunities
    4. Customer Sentiment Insights
    5. Strategic Recommendations

    Present findings in a clear, actionable format for decision-makers.
    """,
    description="Synthesizes parallel research into comprehensive market intelligence.",
    output_key="market_intelligence_report"
)

# Create the sequential pipeline (parallel research → synthesis)
root_agent = ParallelAgent(
    name="MarketIntelligenceAgent",
    sub_agents=[parallel_research_agent, summary_agent],
    description="Parallel market research followed by intelligent synthesis."
)


async def process_market_query(query: str):
    """Process a market intelligence query"""
    try:
        logger.info(f"🚀 Processing market query: {query[:50]}...")

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

        logger.info("🔄 Starting parallel market research...")
        logger.info("   📊 CompetitorAnalyst - analyzing competitive landscape")
        logger.info("   📈 TrendDetector - identifying emerging trends")
        logger.info("   💭 SentimentAnalyzer - analyzing customer sentiment")

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
        logger.error(f"❌ Parallel execution failed: {e}")
        return [{'agent': 'error', 'response': f"Error: {str(e)}"}]


async def main():
    """Main execution function"""
    try:
        logger.info("🚀 Starting Parallel Market Intelligence Agent...")

        # Test queries focused on market analysis
        test_queries = [
            os.getenv("TEST_QUERY", "Analyze the current Docker and containerization market landscape including competitors, trends, and customer sentiment"),
            "Research the SaaS productivity tools market including competitive analysis and emerging trends",
            "Investigate the AI/ML development tools market with focus on developer sentiment and competitive positioning"
        ]

        for i, query in enumerate(test_queries[:1], 1):  # Run first query only by default
            print(f"\n{'='*80}")
            print(f"🧪 Market Intelligence Analysis {i}")
            print(f"📋 Query: {query}")
            print('='*80)

            responses = await process_market_query(query)

            for response in responses:
                print(f"\n🤖 {response['agent']}:")
                print("-" * 50)
                # Show a meaningful preview of each response
                response_text = response['response']
                if response['agent'] == 'MarketIntelligenceSynthesizer':
                    # Show more of the final synthesized report
                    if len(response_text) > 2000:
                        print(response_text[:2000] + "\n... [report continues] ...")
                    else:
                        print(response_text)
                else:
                    # Show preview of individual agent responses
                    if len(response_text) > 500:
                        print(response_text[:500] + "\n... [analysis continues] ...")
                    else:
                        print(response_text)

        logger.info("✅ Parallel market intelligence analysis completed!")

    except Exception as e:
        logger.error(f"❌ Main execution failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())