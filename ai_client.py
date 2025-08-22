"""AWS Bedrock AI client integration for Kiro Streamlit application."""
import json
import boto3
from typing import Optional, Dict, Any, Tuple
from botocore.exceptions import ClientError, BotoCoreError
from config import ConfigManager
from kiro_prompt import PromptManager


class AIClient:
    """AWS Bedrock AI client for content generation."""
    
    def __init__(self, model_name: str, aws_region: str = None):
        self.config_manager = ConfigManager()
        self.prompt_manager = PromptManager()
        self.model_name = model_name
        self.model_id = self.config_manager.get_model_id(model_name)
        self.aws_region = aws_region or self.config_manager.get_aws_region()
        
        if not self.model_id:
            raise ValueError(f"Invalid model name: {model_name}")
        
        # Initialize Bedrock client with role-based authentication
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=self.aws_region
        )
    
    def _prepare_nova_request(self, user_input: str, context: str = "") -> Dict[str, Any]:
        """Prepare request payload for Amazon Nova Pro."""
        system_prompt = self.prompt_manager.get_combined_prompt()
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "text": f"{system_prompt}\n\nContext: {context}\n\nUser Input: {user_input}"
                    }
                ]
            }
        ]
        
        return {
            "messages": messages,
            "max_tokens": 4000,
            "temperature": 0.7,
            "top_p": 0.9
        }
    
    def _prepare_claude_request(self, user_input: str, context: str = "") -> Dict[str, Any]:
        """Prepare request payload for Anthropic Claude Sonnet 3.7."""
        system_prompt = self.prompt_manager.get_combined_prompt()
        
        messages = [
            {
                "role": "user",
                "content": f"Context: {context}\n\nUser Input: {user_input}"
            }
        ]
        
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "temperature": 0.7,
            "top_p": 0.9,
            "system": system_prompt,
            "messages": messages
        }
    
    def _extract_response_content(self, response: Dict[str, Any]) -> str:
        """Extract content from Bedrock response based on model type."""
        try:
            if "amazon.nova" in self.model_id:
                # Nova response format
                return response.get("output", {}).get("message", {}).get("content", [{}])[0].get("text", "")
            elif "anthropic.claude" in self.model_id:
                # Claude response format
                return response.get("content", [{}])[0].get("text", "")
            else:
                return "Unsupported model response format"
        except (KeyError, IndexError, TypeError):
            return "Error parsing response"
    
    def generate_content(self, user_input: str, context: str = "") -> str:
        """Generate content using the selected Bedrock model."""
        try:
            # Prepare request based on model type
            if "amazon.nova" in self.model_id:
                request_body = self._prepare_nova_request(user_input, context)
            elif "anthropic.claude" in self.model_id:
                request_body = self._prepare_claude_request(user_input, context)
            else:
                raise ValueError(f"Unsupported model: {self.model_id}")
            
            # Make request to Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            content = self._extract_response_content(response_body)
            
            return content
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDeniedException':
                return "Error: Access denied to Bedrock service. Please check IAM permissions."
            elif error_code == 'ThrottlingException':
                return "Error: Request throttled. Please try again in a moment."
            elif error_code == 'ValidationException':
                return "Error: Invalid request parameters."
            else:
                return f"AWS Error: {error_code} - {e.response['Error']['Message']}"
        
        except BotoCoreError as e:
            return f"Connection Error: {str(e)}"
        
        except Exception as e:
            return f"Unexpected Error: {str(e)}"
    
    def process_feedback(self, content: str, feedback: str) -> str:
        """Process user feedback and modify content accordingly."""
        feedback_prompt = f"""
        Please modify the following content based on the user feedback:
        
        Original Content:
        {content}
        
        User Feedback:
        {feedback}
        
        Please provide the updated content that addresses the feedback while maintaining the same format and structure.
        """
        
        return self.generate_content(feedback_prompt)
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test connection to Bedrock service."""
        try:
            print(f"Testing model: {self.model_id}")
            
            # Try different request formats for Nova models
            if "nova" in self.model_id.lower():
                # Try the standard Nova format first
                request_formats = [
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": [{"text": "Hello"}]
                            }
                        ],
                        "max_tokens": 10,
                        "temperature": 0.1
                    },
                    # Alternative format without content array
                    {
                        "messages": [
                            {
                                "role": "user", 
                                "content": "Hello"
                            }
                        ],
                        "max_tokens": 10,
                        "temperature": 0.1
                    },
                    # Another alternative with inferenceConfig
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": [{"text": "Hello"}]
                            }
                        ],
                        "inferenceConfig": {
                            "maxTokens": 10,
                            "temperature": 0.1
                        }
                    }
                ]
                
                for i, request_body in enumerate(request_formats):
                    try:
                        print(f"Trying Nova format {i+1}: {json.dumps(request_body, indent=2)}")
                        response = self.bedrock_client.invoke_model(
                            modelId=self.model_id,
                            body=json.dumps(request_body),
                            contentType="application/json",
                            accept="application/json"
                        )
                        
                        response_body = json.loads(response['body'].read())
                        print(f"? Nova format {i+1} worked! Response: {json.dumps(response_body, indent=2)}")
                        return True, f"Model connection successful (format {i+1})"
                        
                    except ClientError as format_error:
                        print(f"? Nova format {i+1} failed: {format_error.response['Error']['Code']} - {format_error.response['Error']['Message']}")
                        continue
                
                return False, f"All Nova request formats failed for {self.model_id}"
                
            elif "claude" in self.model_id.lower():
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 10,
                    "temperature": 0.1,
                    "messages": [
                        {
                            "role": "user",
                            "content": "Hello"
                        }
                    ]
                }
                
                print(f"Trying Claude format: {json.dumps(request_body, indent=2)}")
                response = self.bedrock_client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(request_body),
                    contentType="application/json",
                    accept="application/json"
                )
                
                response_body = json.loads(response['body'].read())
                print(f"? Claude format worked! Response: {json.dumps(response_body, indent=2)}")
                return True, "Model connection successful"
            else:
                return False, f"Unsupported model type: {self.model_id}"
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"? ClientError: {error_code} - {error_message}")
            
            if error_code == 'AccessDeniedException':
                return False, "Access denied to Bedrock service - check IAM permissions"
            elif error_code == 'ThrottlingException':
                return False, "Request throttled - try again later"
            elif error_code == 'ValidationException':
                return False, f"Model validation failed: {error_message}. Check if {self.model_name} ({self.model_id}) is available and accessible in {self.aws_region}"
            elif error_code == 'ResourceNotFoundException':
                return False, f"Model not found: {self.model_id}. Check if the model ID is correct and you have access."
            else:
                return False, f"AWS Error: {error_code} - {error_message}"
        
        except Exception as e:
            print(f"? Unexpected error: {str(e)}")
            return False, f"Connection error: {str(e)}"