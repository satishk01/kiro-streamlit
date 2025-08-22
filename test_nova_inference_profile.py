#!/usr/bin/env python3
"""Test Nova Pro with inference profile."""

import boto3
import json
from ai_client import AIClient
from config import ConfigManager

def test_nova_inference_profile():
    """Test Nova Pro with the correct inference profile."""
    print("🧪 Testing Nova Pro with inference profile...")
    
    # Test with inference profile
    try:
        config_manager = ConfigManager()
        
        # Test direct inference profile
        inference_profile_id = "us.amazon.nova-pro-v1:0"
        print(f"Testing inference profile: {inference_profile_id}")
        
        bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": "Hello, can you respond with just 'Success!'?"}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 50,
                "temperature": 0.1
            }
        }
        
        print(f"Request: {json.dumps(request_body, indent=2)}")
        
        response = bedrock_client.invoke_model(
            modelId=inference_profile_id,
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        print(f"✅ Success! Response: {json.dumps(response_body, indent=2)}")
        
        # Test with AIClient
        print("\n🤖 Testing with AIClient...")
        ai_client = AIClient("Amazon Nova Pro", "us-east-1")
        result = ai_client.generate_content("Say hello in one word")
        print(f"AIClient result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_nova_inference_profile()