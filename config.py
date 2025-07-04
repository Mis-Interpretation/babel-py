"""
Configuration module for loading environment variables and managing app settings.
This should be imported first to ensure environment variables are properly loaded.
"""

import os
from dotenv import load_dotenv
from typing import Optional

class Config:
    """Configuration class that manages environment variables and app settings."""
    
    def __init__(self):
        """Initialize configuration by loading environment variables."""
        self._load_environment()
        self._validate_config()
    
    def _load_environment(self):
        """Load environment variables from .env file with force override."""
        try:
            # Force override existing environment variables
            load_dotenv(override=True)
            print("✅ Environment variables loaded successfully from .env file")
        except Exception as e:
            print(f"⚠️  Warning: Could not load .env file: {e}")
            print("Using system environment variables or defaults")
    
    def _validate_config(self):
        """Validate that required configuration is present."""
        if not self.openai_api_key or self.openai_api_key == "sk-your-actual-openai-api-key-here":
            print("⚠️  WARNING: OpenAI API key not properly configured!")
            print("Please set OPENAI_API_KEY in your .env file or environment variables")
        else:
            print(f"✅ OpenAI API key configured (model: {self.openai_model})")
    
    @property
    def openai_api_key(self) -> str:
        """Get OpenAI API key from environment."""
        return os.getenv("OPENAI_API_KEY", "sk-your-actual-openai-api-key-here")
    
    @property
    def openai_model(self) -> str:
        """Get OpenAI model from environment."""
        return os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    @property
    def server_host(self) -> str:
        """Get server host from environment."""
        return os.getenv("SERVER_HOST", "127.0.0.1")
    
    @property
    def server_port(self) -> int:
        """Get server port from environment."""
        try:
            return int(os.getenv("SERVER_PORT", "8000"))
        except ValueError:
            return 8000
    
    @property
    def is_api_configured(self) -> bool:
        """Check if OpenAI API is properly configured."""
        return bool(
            self.openai_api_key and 
            self.openai_api_key != "sk-your-actual-openai-api-key-here"
        )
    
    def get_config_summary(self) -> dict:
        """Get a summary of current configuration (safe for logging)."""
        return {
            "openai_model": self.openai_model,
            "server_host": self.server_host,
            "server_port": self.server_port,
            "api_configured": self.is_api_configured,
            "api_key_preview": f"{self.openai_api_key[:10]}..." if self.is_api_configured else "Not configured"
        }
    
    def update_openai_config(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Dynamically update OpenAI configuration."""
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            print(f"✅ OpenAI API key updated")
        
        if model:
            os.environ["OPENAI_MODEL"] = model
            print(f"✅ OpenAI model updated to: {model}")

# Global configuration instance
# This will be initialized when the module is imported
config = Config()

def get_config() -> Config:
    """Get the global configuration instance."""
    return config

def reload_config():
    """Reload configuration from environment files."""
    global config
    config = Config()
    return config

# Convenience functions for backward compatibility
def get_openai_api_key() -> str:
    """Get OpenAI API key."""
    return config.openai_api_key

def get_openai_model() -> str:
    """Get OpenAI model."""
    return config.openai_model

if __name__ == "__main__":
    # Test the configuration loading
    print("🔧 Configuration Test")
    print("=" * 50)
    
    config_summary = config.get_config_summary()
    for key, value in config_summary.items():
        print(f"{key}: {value}")
    
    print("\n" + "=" * 50)
    if config.is_api_configured:
        print("✅ Configuration is ready for use!")
    else:
        print("❌ Please configure your OpenAI API key in .env file") 