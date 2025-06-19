import asyncio
import sys
import os

# Add the shared module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import get_model_config, create_session, setup_logging, get_gemini_model
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.runners import Runner
from google.adk.tools import google_search
from google.genai import types

# Setup logging
logger = setup_logging()

# Configuration
APP_NAME = "loop_travel_planner"
USER_ID = "traveler"

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

# Travel research agent
travel_researcher = LlmAgent(
    name="TravelResearcher",
    model=get_search_model(),
    instruction="""You are a travel research specialist.
    Research the destination including:
    - Best time to visit and weather
    - Top attractions and activities
    - Local culture and customs
    - Transportation options
    - Budget considerations

    Provide comprehensive research findings for trip planning.
    """,
    description="Researches travel destinations and provides detailed information.",
    tools=[google_search],
    output_key="travel_research"
)

# Initial itinerary generator
itinerary_generator = LlmAgent(
    name="ItineraryGenerator",
    model=get_model_config(temperature=0.4),
    instruction="""You are a professional travel planner.
    Based on the travel research from state['travel_research'] and user preferences,
    create a detailed travel itinerary including:

    - Day-by-day schedule
    - Recommended accommodations
    - Must-see attractions and activities
    - Restaurant recommendations
    - Transportation suggestions
    - Budget estimates
    - Practical tips and warnings

    Present as a well-organized, actionable travel plan.
    Include multiple options where appropriate.
    """,
    description="Creates detailed travel itineraries based on research.",
    output_key="initial_itinerary"
)

# Itinerary optimizer (after human feedback)
itinerary_optimizer = LlmAgent(
    name="ItineraryOptimizer",
    model=get_model_config(temperature=0.2),
    instruction="""You are a travel optimization expert.

    Take the initial itinerary from state['initial_itinerary'] and
    human feedback from state['human_feedback'].

    Optimize the itinerary based on the human preferences:
    - Adjust activities based on interests
    - Modify budget recommendations
    - Change pace and schedule if requested
    - Add or remove activities as suggested
    - Improve logistics and timing

    Create an optimized itinerary that incorporates all human feedback
    while maintaining practical feasibility.
    """,
    description="Optimizes itineraries based on human feedback and preferences.",
    output_key="optimized_itinerary"
)


class HumanInLoopTravelPlanner:
    """Travel planner with human decision points"""

    def __init__(self):
        self.session_service = None
        self.session = None
        self.runner = None

    async def initialize(self):
        """Initialize the planning system"""
        self.session_service, self.session = await create_session(APP_NAME, USER_ID)

        # Create research and initial planning pipeline
        root_agent = SequentialAgent(
            name="ResearchAndInitialPlanning",
            sub_agents=[travel_researcher, itinerary_generator],
            description="Research destination and create initial itinerary."
        )

        self.runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=self.session_service
        )

    async def research_and_plan(self, travel_request: str):
        """Research destination and create initial itinerary"""
        logger.info(f"🔍 Researching and planning: {travel_request[:50]}...")

        content = types.Content(
            role='user',
            parts=[types.Part(text=travel_request)]
        )

        events = self.runner.run_async(
            user_id=USER_ID,
            session_id=self.session.id,
            new_message=content
        )

        research_result = None
        initial_itinerary = None

        async for event in events:
            if event.is_final_response():
                if event.author == "TravelResearcher":
                    research_result = event.content.parts[0].text
                elif event.author == "ItineraryGenerator":
                    initial_itinerary = event.content.parts[0].text

        return research_result, initial_itinerary

    def get_human_feedback(self, initial_itinerary: str) -> str:
        """Simulate human feedback (in production, this would be actual human input)"""
        logger.info("👤 Requesting human feedback on initial itinerary...")

        # In a real implementation, this would:
        # 1. Display the itinerary to the human user
        # 2. Collect their feedback through UI/CLI
        # 3. Return their preferences and modifications

        # Simulated human feedback scenarios
        feedback_scenarios = [
            "I prefer a more relaxed pace with fewer activities per day. Also, I'm interested in local food experiences and would like more restaurant recommendations. Budget is not a major concern.",
            "I'm very interested in cultural and historical sites. Please add more museums and historical tours. I prefer mid-range accommodations and am comfortable with public transportation.",
            "I'm traveling with children, so please include family-friendly activities and restaurants. Safety is very important. I prefer hotels with pools and kid-friendly amenities.",
            "I'm interested in adventure activities and outdoor experiences. Please include hiking, water sports, or adventure tours. I prefer unique accommodations like eco-lodges."
        ]

        # For demonstration, we'll cycle through scenarios or use an environment variable
        scenario_index = int(os.getenv("HUMAN_FEEDBACK_SCENARIO", "0")) % len(feedback_scenarios)
        simulated_feedback = feedback_scenarios[scenario_index]

        logger.info(f"👤 Human feedback received: {simulated_feedback[:50]}...")

        print(f"\n{'='*60}")
        print("👤 HUMAN FEEDBACK POINT")
        print('='*60)
        print("Initial Itinerary Preview:")
        print(initial_itinerary[:500] + "..." if len(initial_itinerary) > 500 else initial_itinerary)
        print(f"\n👤 Human Feedback: {simulated_feedback}")
        print('='*60)

        return simulated_feedback

    async def optimize_itinerary(self, human_feedback: str):
        """Optimize itinerary based on human feedback"""
        logger.info("🔧 Optimizing itinerary based on human feedback...")

        # Update runner to use optimizer agent
        optimizer_runner = Runner(
            agent=itinerary_optimizer,
            app_name=APP_NAME,
            session_service=self.session_service
        )

        # Add human feedback to session state
        # Note: In a real implementation, this would be handled more elegantly
        content = types.Content(
            role='user',
            parts=[types.Part(text=f"Human feedback: {human_feedback}")]
        )

        events = optimizer_runner.run_async(
            user_id=USER_ID,
            session_id=self.session.id,
            new_message=content
        )

        async for event in events:
            if event.is_final_response():
                return event.content.parts[0].text

        return None


async def run_human_in_loop_planning(travel_request: str):
    """Execute the complete human-in-loop travel planning process"""
    try:
        planner = HumanInLoopTravelPlanner()
        await planner.initialize()

        # Step 1: Research and create initial itinerary
        logger.info("📋 Step 1: Research and Initial Planning")
        research_result, initial_itinerary = await planner.research_and_plan(travel_request)

        # Step 2: Human feedback (simulated)
        logger.info("👤 Step 2: Human Feedback Collection")
        # Store human feedback in session state for the optimizer
        human_feedback = planner.get_human_feedback(initial_itinerary)

        # Manually add feedback to session state (simplified approach)
        # In production, this would be handled more elegantly through the session service
        if hasattr(planner.session, 'state'):
            planner.session.state['human_feedback'] = human_feedback

        # Step 3: Optimize based on feedback
        logger.info("🎯 Step 3: Itinerary Optimization")
        optimized_itinerary = await planner.optimize_itinerary(human_feedback)

        return {
            'research': research_result,
            'initial_itinerary': initial_itinerary,
            'human_feedback': human_feedback,
            'optimized_itinerary': optimized_itinerary
        }

    except Exception as e:
        logger.error(f"❌ Human-in-loop planning failed: {e}")
        return {'error': str(e)}


async def main():
    """Main execution function"""
    try:
        logger.info("🚀 Starting Human-in-Loop Travel Planner...")

        # Test travel requests
        test_requests = [
            os.getenv("TEST_QUERY", "Plan a 7-day trip to Tokyo, Japan for two adults interested in culture and food"),
            "Plan a 5-day family vacation to Barcelona with two children (ages 8 and 12)",
            "Plan a 10-day adventure trip to New Zealand for outdoor enthusiasts"
        ]

        for i, request in enumerate(test_requests[:1], 1):  # Run first request only by default
            print(f"\n{'='*80}")
            print(f"🧪 Human-in-Loop Planning {i}")
            print(f"📋 Request: {request}")
            print('='*80)

            result = await run_human_in_loop_planning(request)

            if 'error' in result:
                print(f"❌ Error: {result['error']}")
                continue

            # Display results
            print(f"\n🔍 Research Results:")
            print("-" * 50)
            if result.get('research'):
                research_preview = result['research'][:600] + "..." if len(result['research']) > 600 else result['research']
                print(research_preview)

            print(f"\n📋 Initial Itinerary:")
            print("-" * 50)
            if result.get('initial_itinerary'):
                initial_preview = result['initial_itinerary'][:800] + "..." if len(result['initial_itinerary']) > 800 else result['initial_itinerary']
                print(initial_preview)

            print(f"\n🎯 Optimized Itinerary (After Human Feedback):")
            print("-" * 50)
            if result.get('optimized_itinerary'):
                optimized_preview = result['optimized_itinerary'][:1000] + "..." if len(result['optimized_itinerary']) > 1000 else result['optimized_itinerary']
                print(optimized_preview)

        logger.info("✅ Human-in-loop travel planning completed!")

    except Exception as e:
        logger.error(f"❌ Main execution failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())