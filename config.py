"""Configuration management for Kiro Streamlit application."""
import os
import boto3
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass

# AWS Configuration
DEFAULT_AWS_REGION = "us-east-1"
BEDROCK_MODELS = {
    "Amazon Nova Pro": "amazon.nova-pro-v1:0",
    "Anthropic Claude Sonnet 3.7": "anthropic.claude-3-5-sonnet-20241022-v2:0"
}

@dataclass
class AppConfig:
    """Application configuration state."""
    selected_model: str
    working_directory: str
    aws_region: str

class ConfigManager:
    """Manages application configuration and validation."""
    
    def __init__(self):
        self.aws_region = self.get_aws_region()
        
    def get_aws_region(self) -> str:
        """Get AWS region from environment or use default."""
        return os.getenv("AWS_DEFAULT_REGION", DEFAULT_AWS_REGION)
    
    def get_available_models(self) -> Dict[str, str]:
        """Get available Bedrock models."""
        return BEDROCK_MODELS.copy()
    
    def validate_model_selection(self, model_name: str) -> bool:
        """Validate if selected model is available."""
        return model_name in BEDROCK_MODELS
    
    def get_model_id(self, model_name: str) -> Optional[str]:
        """Get Bedrock model ID for given model name."""
        return BEDROCK_MODELS.get(model_name)
    
    def validate_directory(self, path: str) -> bool:
        """Validate if directory path exists and is accessible."""
        try:
            path_obj = Path(path)
            return path_obj.exists() and path_obj.is_dir()
        except Exception:
            return False
    
    def create_kiro_structure(self, base_path: str) -> bool:
        """Create .kiro/specs directory structure if it doesn't exist."""
        try:
            kiro_path = Path(base_path) / ".kiro" / "specs"
            kiro_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False
    
    def test_aws_connectivity(self) -> bool:
        """Test AWS Bedrock service connectivity."""
        try:
            client = boto3.client('bedrock', region_name=self.aws_region)
            # Simple operation to test connectivity
            client.list_foundation_models()
            return True
        except Exception:
            return False
    
    def get_bedrock_endpoint(self) -> str:
        """Get Bedrock service endpoint URL."""
        return f"https://bedrock.{self.aws_region}.amazonaws.com"