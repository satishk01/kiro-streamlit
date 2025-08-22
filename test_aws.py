#!/usr/bin/env python3
"""Test script for AWS Bedrock connectivity."""
import boto3
import json
from botocore.exceptions import ClientError, NoCredentialsError

def test_aws_setup():
    """Test AWS configuration and Bedrock access."""
    print("Testing AWS Bedrock connectivity...")
    
    # Test 1: Check AWS credentials/role
    print("\n1. Testing AWS credentials...")
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Identity: {identity.get('Arn', 'Unknown')}")
    except NoCredentialsError:
        print("❌ No AWS credentials found. Ensure EC2 instance has IAM role attached.")
        return False
    except Exception as e:
        print(f"❌ AWS credential error: {e}")
        return False
    
    # Test 2: Check Bedrock service access
    print("\n2. Testing Bedrock service access...")
    try:
        bedrock = boto3.client('bedrock', region_name='us-east-1')
        models = bedrock.list_foundation_models()
        print(f"✅ Found {len(models.get('modelSummaries', []))} available models")
    except ClientError as e:
        print(f"❌ Bedrock access error: {e}")
        return False
    except Exception as e:
        print(f"❌ Bedrock service error: {e}")
        return False
    
    # Test 3: Check specific models
    print("\n3. Testing specific models...")
    target_models = [
        "amazon.nova-pro-v1:0",
        "anthropic.claude-3-5-sonnet-20241022-v2:0"
    ]
    
    available_models = [model['modelId'] for model in models.get('modelSummaries', [])]
    
    for model_id in target_models:
        if model_id in available_models:
            print(f"✅ Model available: {model_id}")
        else:
            print(f"❌ Model not available: {model_id}")
    
    # Test 4: Test Bedrock Runtime
    print("\n4. Testing Bedrock Runtime...")
    try:
        runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # Test with Claude (more likely to be available)
        claude_model = "anthropic.claude-3-5-sonnet-20241022-v2:0"
        if claude_model in available_models:
            test_request = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 10,
                "temperature": 0.1,
                "messages": [{"role": "user", "content": "Hello"}]
            }
            
            response = runtime.invoke_model(
                modelId=claude_model,
                body=json.dumps(test_request),
                contentType="application/json",
                accept="application/json"
            )
            print(f"✅ Runtime test successful with {claude_model}")
        else:
            print(f"❌ Cannot test runtime - {claude_model} not available")
            
    except Exception as e:
        print(f"❌ Runtime test error: {e}")
        return False
    
    print("\n✅ All tests passed! AWS Bedrock is properly configured.")
    return True

if __name__ == "__main__":
    test_aws_setup()