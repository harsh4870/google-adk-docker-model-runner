"""
Fixed Sequential Agent with container-aware configuration.
Creates a pipeline: Code Writer → Code Reviewer → Code Refactorer
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
from google.genai import types

# Setup logging
logger = setup_logging()

# Configuration
APP_NAME = "sequential_code_pipeline"
USER_ID = "developer"

# Define agents with improved instructions
code_writer_agent = LlmAgent(
    name="CodeWriterAgent",
    model=get_model_config(temperature=0.1),
    instruction="""You are an expert HTML/CSS developer.
    Create clean, semantic HTML code based on user requirements.
    Include proper structure, accessibility attributes, and basic CSS styling.
    Output ONLY the complete HTML code - no explanations or markdown formatting.
    """,
    description="Generates initial HTML code from specifications.",
    output_key="generated_code"
)

code_reviewer_agent = LlmAgent(
    name="CodeReviewerAgent", 
    model=get_model_config(temperature=0.1),
    instruction="""You are a senior code reviewer specializing in web development.
    Review the HTML code from state['generated_code'].
    
    Check for:
    - HTML semantic structure
    - Accessibility issues  
    - CSS best practices
    - Cross-browser compatibility
    - Performance considerations
    
    Provide specific, actionable feedback in bullet points.
    Focus on the most important improvements only.
    """,
    description="Reviews code and provides constructive feedback.",
    output_key="review_comments"
)

code_refactor_agent = LlmAgent(
    name="CodeRefactorerAgent",
    model=get_model_config(temperature=0.1), 
    instruction="""You are an expert code refactoring specialist.
    
    Take the original code from state['generated_code'] and 
    the review feedback from state['review_comments'].
    
    Apply the suggested improvements to create better code.
    Ensure the refactored code:
    - Addresses all valid review points
    - Maintains original functionality
    - Follows modern web standards
    - Is well-structured and readable
    
    Output ONLY the final refactored HTML code - no explanations.
    """,
    description="Refactors code based on review feedback.",
    output_key="refactored_code"
)

# Create the sequential pipeline
root_agent = SequentialAgent(
    name="CodePipelineAgent",
    sub_agents=[code_writer_agent, code_reviewer_agent, code_refactor_agent],
    description="A 3-stage code development pipeline: Write → Review → Refactor"
)


async def process_query(query: str):
    """Process a single query through the sequential pipeline"""
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


async def main():
    """Main execution function"""
    try:
        logger.info("🚀 Starting Sequential Code Pipeline Agent...")
        
        # Test queries
        test_queries = [
            os.getenv("TEST_QUERY", "Create a responsive HTML landing page with navigation"),
            "Build a contact form with validation styling",
            "Create a card component with image, title, and description"
        ]
        
        for i, query in enumerate(test_queries[:1], 1):  # Run first query only by default
            print(f"\n{'='*80}")
            print(f"🧪 Test {i}: {query}")
            print('='*80)
            
            responses = await process_query(query)
            
            for response in responses:
                print(f"\n🤖 {response['agent']}:")
                print("-" * 50)
                # Truncate very long responses for readability
                response_text = response['response']
                if len(response_text) > 1000:
                    print(response_text[:1000] + "\n... [truncated] ...")
                else:
                    print(response_text)
                    
        logger.info("✅ Sequential agent completed successfully!")
                
    except Exception as e:
        logger.error(f"❌ Main execution failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
