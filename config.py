"""Configuration management for Kiro Streamlit application."""
import os
import boto3
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

# AWS Configuration
DEFAULT_AWS_REGION = "us-east-1"
BEDROCK_MODELS = {
    "Amazon Nova Pro": "amazon.nova-pro-v1:0",
    "Amazon Nova Pro (24k context)": "amazon.nova-pro-v1:0:24k",
    "Amazon Nova Pro (300k context)": "amazon.nova-pro-v1:0:300k",
    "Anthropic Claude Sonnet 3.7": "anthropic.claude-3-7-sonnet-20250219-v1:0",
    "Anthropic Claude 3.5 Sonnet v2": "anthropic.claude-3-5-sonnet-20241022-v2:0"
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
    
    def discover_available_models(self) -> Tuple[bool, Dict[str, str], str]:
        """Discover available models from AWS Bedrock."""
        try:
            bedrock_client = boto3.client('bedrock', region_name=self.aws_region)
            models_response = bedrock_client.list_foundation_models()
            
            available_models = {}
            all_models = []
            
            for model in models_response.get('modelSummaries', []):
                model_id = model['modelId']
                model_name = model.get('modelName', model_id)
                all_models.append(f"{model_name} ({model_id})")
                
                # Look for Nova models (prefer standard version without context limits)
                if 'nova' in model_id.lower() and 'pro' in model_id.lower():
                    # Prefer the standard version without context suffix
                    if model_id == "amazon.nova-pro-v1:0":
                        available_models['Amazon Nova Pro'] = model_id
                    elif 'Amazon Nova Pro' not in available_models:
                        # Fallback to any Nova Pro variant
                        available_models['Amazon Nova Pro'] = model_id
                
                # Look for Claude models (prefer 3.7, then 3.5)
                if 'claude' in model_id.lower():
                    if '3-7' in model_id or '3.7' in model_id:
                        available_models['Anthropic Claude Sonnet 3.7'] = model_id
                    elif ('3-5' in model_id or '3.5' in model_id) and 'Anthropic Claude Sonnet 3.7' not in available_models:
                        available_models['Anthropic Claude Sonnet 3.7'] = model_id
            
            models_list = "\n".join(all_models[:10])  # Show first 10 models
            if len(all_models) > 10:
                models_list += f"\n... and {len(all_models) - 10} more models"
            
            return True, available_models, f"Found {len(all_models)} total models:\n{models_list}"
            
        except Exception as e:
            return False, {}, f"Failed to discover models: {str(e)}"
    
    def test_aws_connectivity(self) -> Tuple[bool, str]:
        """Test AWS Bedrock service connectivity."""
        try:
            # First check if we can get AWS identity
            try:
                sts_client = boto3.client('sts', region_name=self.aws_region)
                identity = sts_client.get_caller_identity()
                print(f"AWS Identity: {identity.get('Arn', 'Unknown')}")
            except Exception as sts_error:
                if "NoCredentialsError" in str(type(sts_error)):
                    return False, "No AWS credentials found. Ensure EC2 instance has IAM role attached."
                return False, f"AWS authentication failed: {str(sts_error)}"
            
            # Discover available models
            success, discovered_models, models_info = self.discover_available_models()
            if not success:
                return False, models_info
            
            # Update global BEDROCK_MODELS with discovered models
            global BEDROCK_MODELS
            if discovered_models:
                BEDROCK_MODELS.update(discovered_models)
            
            # Check if our target models are available
            available_model_ids = list(discovered_models.values())
            target_models = list(BEDROCK_MODELS.values())
            
            missing_models = [model for model in target_models if model not in available_model_ids]
            
            if not discovered_models:
                return False, f"No Nova Pro or Claude 3.5 models found in {self.aws_region}. Available models:\n{models_info}"
            
            # Test bedrock-runtime client
            runtime_client = boto3.client('bedrock-runtime', region_name=self.aws_region)
            
            found_models = ", ".join([f"{name} ({model_id})" for name, model_id in discovered_models.items()])
            return True, f"Connection successful! Found models: {found_models}"
            
        except Exception as e:
            error_msg = str(e)
            error_type = str(type(e))
            
            if "AccessDenied" in error_msg or "AccessDeniedException" in error_msg:
                return False, "Access denied to Bedrock service. Check IAM role permissions for 'bedrock:*' actions."
            elif "UnauthorizedOperation" in error_msg:
                return False, "Unauthorized operation. Ensure IAM role has Bedrock permissions."
            elif "NoCredentialsError" in error_type:
                return False, "No AWS credentials found. Ensure EC2 instance has proper IAM role attached."
            elif "EndpointConnectionError" in error_msg:
                return False, f"Cannot connect to Bedrock service in region {self.aws_region}. Check if Bedrock is available in this region."
            elif "InvalidRegion" in error_msg:
                return False, f"Invalid AWS region: {self.aws_region}. Bedrock may not be available in this region."
            else:
                return False, f"Connection failed: {error_msg} (Type: {error_type})"
    
    def get_bedrock_endpoint(self) -> str:
        """Get Bedrock service endpoint URL."""
        return f"https://bedrock.{self.aws_region}.amazonaws.com"
    
    def get_setup_instructions(self) -> str:
        """Get setup instructions for AWS Bedrock."""
        return """
**AWS Bedrock Setup Instructions:**

1. **EC2 IAM Role**: Ensure your EC2 instance has an IAM role with these permissions:
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "bedrock:InvokeModel",
                   "bedrock:ListFoundationModels"
               ],
               "Resource": "*"
           }
       ]
   }
   ```

2. **Model Access**: Request access to models in AWS Bedrock console:
   - Amazon Nova Pro
   - Anthropic Claude 3.5 Sonnet

3. **Region**: Ensure Bedrock is available in your selected region (us-east-1 recommended)

4. **Service Quotas**: Check that you have sufficient quotas for Bedrock usage
        """