#!/usr/bin/env python3
"""Test script to actually invoke Bedrock models."""
import boto3
import json
from botocore.exceptions import ClientError

def test_model_invocation(model_id, region='us-east-1'):
    """Test actual model invocation."""
    try:
        print(f"🧪 Testing model invocation: {model_id}")
        
        runtime_client = boto3.client('bedrock-runtime', region_name=region)
        
        # Prepare request based on model type
        if 'nova' in model_id.lower():
            # Nova format with inferenceConfig
            request_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": "Hello, respond with just 'Hi'"}]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": 10,
                    "temperature": 0.1
                }
            }
        elif 'claude' in model_id.lower():
            # Claude format
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 10,
                "temperature": 0.1,
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, respond with just 'Hi'"
                    }
                ]
            }
        else:
            print(f"❓ Unknown model format for {model_id}")
            return False, "Unknown model format"
        
        # Make the request
        response = runtime_client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json"
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        print(f"✅ Model {model_id} responded successfully!")
        print(f"📝 Response: {json.dumps(response_body, indent=2)}")
        
        return True, "Success"
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"❌ AWS Error for {model_id}: {error_code} - {error_message}")
        return False, f"{error_code}: {error_message}"
    except Exception as e:
        print(f"❌ Unexpected error for {model_id}: {str(e)}")
        return False, str(e)

def main():
    """Test all Nova and Claude models."""
    print("🚀 Testing Bedrock model invocations...")
    
    try:
        # List available models
        bedrock_client = boto3.client('bedrock', region_name='us-east-1')
        models_response = bedrock_client.list_foundation_models()
        
        nova_models = []
        claude_models = []
        
        for model in models_response.get('modelSummaries', []):
            model_id = model['modelId']
            if 'nova' in model_id.lower():
                nova_models.append(model_id)
            elif 'claude' in model_id.lower():
                claude_models.append(model_id)
        
        print(f"\n🔍 Found {len(nova_models)} Nova models and {len(claude_models)} Claude models")
        
        # Test Nova models
        if nova_models:
            print("\n🚀 Testing Nova models:")
            for model_id in nova_models:
                success, message = test_model_invocation(model_id)
                if success:
                    print(f"✅ {model_id}: Working!")
                else:
                    print(f"❌ {model_id}: {message}")
                print()
        
        # Test Claude models (first 2 only)
        if claude_models:
            print("🧠 Testing Claude models (first 2):")
            for model_id in claude_models[:2]:
                success, message = test_model_invocation(model_id)
                if success:
                    print(f"✅ {model_id}: Working!")
                else:
                    print(f"❌ {model_id}: {message}")
                print()
        
    except Exception as e:
        print(f"❌ Failed to list models: {e}")

if __name__ == "__main__":
    main()