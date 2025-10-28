import os
from typing import Any, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for Azure OpenAI and system settings."""
    
    def __init__(self):
        """Initialize configuration and create necessary directories."""
        # Set base directory
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load environment variables
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "").strip()
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip().rstrip("/")
        
        # Default model - this is the primary fallback
        self.default_model = os.getenv("AZURE_OPENAI_MODEL", "gpt-4").strip()
        
        # Removed the problematic subdirs line that was causing AttributeError

    def validate(self) -> tuple[bool, str]:
        missing = [k for k, v in {
            "AZURE_OPENAI_API_KEY": self.api_key,
            "AZURE_OPENAI_API_VERSION": self.api_version,
            "AZURE_OPENAI_ENDPOINT": self.endpoint,
        }.items() if not v]
        if missing:
            return False, f"Missing environment variables: {', '.join(missing)}"
        return True, "Configuration valid"
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration for autogen agents."""
        return {
            "config_list": [
                {
                    "model": self.default_model,
                    "api_key": self.api_key,
                    "base_url": self.endpoint,  # Use endpoint directly as it's already a full URL
                    "api_type": "azure",
                    "api_version": self.api_version,
                }
            ],
            "timeout": 180,
            "seed": 42,
        }

_env = Config()
llm_config = _env.get_llm_config()
