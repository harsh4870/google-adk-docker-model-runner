"""
Centralized configuration module for all ADK agents.
Handles Docker Model Runner endpoint detection and environment variables.
"""

import os
import socket
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ModelRunnerConfig:
    """Container-aware configuration for Docker Model Runner endpoints"""
    
    def __init__(self):
        self.api_base = self._detect_model_runner_endpoint()
        self.model_name = self._get_model_name()
        self.api_key = os.getenv("OPENAI_API_KEY", "anything")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cloud_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        
        # Set environment variables for LiteLLM compatibility
        os.environ["OPENAI_API_KEY"] = self.api_key
        os.environ["OPENAI_API_BASE"] = self.api_base
        
        logger.info(f"🔧 Model Runner Configuration:")
        logger.info(f"   API Base: {self.api_base}")
        logger.info(f"   Model: {self.model_name}")
        logger.info(f"   Running in container: {self._running_in_container()}")
        
    def _detect_model_runner_endpoint(self) -> str:
        """Auto-detect the correct Docker Model Runner endpoint"""
        
        # 1. Check explicit environment variable (Docker run -e)
        docker_model_runner = os.getenv("DOCKER_MODEL_RUNNER")
        if docker_model_runner:
            logger.info(f"✅ Using DOCKER_MODEL_RUNNER: {docker_model_runner}")
            return docker_model_runner
            
        # 2. Check if we're running in a container
        if self._running_in_container():
            # Try common container networking patterns
            container_endpoints = [
                "http://host.docker.internal:12434/engines/llama.cpp/v1",  # Docker Desktop
                "http://model-runner.docker.internal:12434/engines/llama.cpp/v1",  # Docker internal
                "http://172.17.0.1:12434/engines/llama.cpp/v1",  # Default Docker bridge
                "http://model-runner:12434/engines/llama.cpp/v1",  # Docker Compose service
            ]
            
            for endpoint in container_endpoints:
                if self._test_endpoint_connectivity(endpoint):
                    logger.info(f"✅ Auto-detected container endpoint: {endpoint}")
                    return endpoint
                    
            logger.warning("⚠️ No container endpoints reachable, falling back to localhost")
            
        # 3. Fallback to localhost (development/direct host execution)
        localhost_endpoint = "http://localhost:12434/engines/llama.cpp/v1"
        logger.info(f"🏠 Using localhost endpoint: {localhost_endpoint}")
        return localhost_endpoint
        
    def _get_model_name(self) -> str:
        """Get model name with proper OpenAI prefix"""
        model = os.getenv("MODEL_NAME", "ai/llama3.2:1B-Q8_0")
        
        # Ensure openai/ prefix for Docker Model Runner
        if not model.startswith("openai/"):
            model = f"openai/{model}"
            
        return model
        
    def _running_in_container(self) -> bool:
        """Detect if code is running inside a container"""
        indicators = [
            os.path.exists("/.dockerenv"),  # Docker creates this file
            os.path.exists("/run/.containerenv"),  # Podman creates this
            os.getenv("KUBERNETES_SERVICE_HOST") is not None,  # Kubernetes
            os.getenv("CONTAINER") == "docker",  # Some images set this
        ]
        
        return any(indicators)
        
    def _test_endpoint_connectivity(self, endpoint: str) -> bool:
        """Test if an endpoint is reachable"""
        try:
            parsed = urlparse(endpoint)
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            
            # Quick socket test
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            
            return result == 0
            
        except Exception as e:
            logger.debug(f"Connectivity test failed for {endpoint}: {e}")
            return False
    
    def get_litellm_config(self, **kwargs) -> Dict[str, Any]:
        """Get LiteLLM configuration dictionary"""
        config = {
            "model": self.model_name,
            "api_base": self.api_base,
            "api_key": self.api_key,
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 2048),
        }
        
        # Add any additional kwargs
        config.update(kwargs)
        return config
    
    def get_gemini_config(self) -> Dict[str, Any]:
        """Get Gemini configuration for Google Search agents"""
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini agents")
            
        return {
            "api_key": self.google_api_key,
            "location": self.google_cloud_location,
        }


# Global configuration instance
config = ModelRunnerConfig()


def get_model_config(**kwargs):
    """Convenience function to get LiteLLM model configuration"""
    from google.adk.models.lite_llm import LiteLlm
    return LiteLlm(**config.get_litellm_config(**kwargs))


def get_gemini_model():
    """Convenience function to get Gemini model configuration"""
    from google.adk.models.genai import Genai
    gemini_config = config.get_gemini_config()
    return Genai(
        model="gemini-2.0-flash",
        api_key=gemini_config["api_key"],
        location=gemini_config["location"]
    )


# Session management utilities
async def create_session(app_name: str, user_id: str = "default_user"):
    """Create a session with proper async handling"""
    from google.adk.sessions import InMemorySessionService
    
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=app_name,
        user_id=user_id
    )
    return session_service, session


def setup_logging():
    """Setup consistent logging across all agents"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)
