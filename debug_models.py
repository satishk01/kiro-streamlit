#!/usr/bin/env python3
"""Debug script to list all available Bedrock models."""
import boto3
import json
from botocore.exceptions import ClientError

def list_all_bedrock_models(region='us-east-1'):
    """List all available Bedrock models in the specified region."""
    try:
        print(f"🔍 Discovering Bedrock models in {region}...")
        
        bedrock_client = boto3.client('bedrock', region_name=region)
        response = bedrock_client.list_foundation_models()
        
        models = response.get('modelSummaries', [])
        print(f"\n📊 Found {len(models)} total models:")
        
        nova_models = []
        claude_models = []
        other_models = []
        
        for model in models:
            model_id = model['modelId']
            model_name = model.get('modelName', 'Unknown')
            provider = model.get('providerName', 'Unknown')
            
            model_info = {
                'id': model_id,
                'name': model_name,
                'provider': provider
            }
            
            if 'nova' in model_id.lower():
                nova_models.append(model_info)
            elif 'claude' in model_id.lower():
                claude_models.append(model_info)
            else:
                other_models.append(model_info)
        
        # Print Nova models
        if nova_models:
            print("\n🚀 Amazon Nova Models:")
            for model in nova_models:
                print(f"  - {model['name']}")
                print(f"    ID: {model['id']}")
                print(f"    Provider: {model['provider']}")
                print()
        
        # Print Claude models
        if claude_models:
            print("🧠 Anthropic Claude Models:")
            for model in claude_models:
                print(f"  - {model['name']}")
                print(f"    ID: {model['id']}")
                print(f"    Provider: {model['provider']}")
                print()
        
        # Print other models (first 5)
        if other_models:
            print("🔧 Other Available Models (first 5):")
            for model in other_models[:5]:
                print(f"  - {model['name']}")
                print(f"    ID: {model['id']}")
                print(f"    Provider: {model['provider']}")
                print()
        
        # Generate suggested configuration
        print("💡 Suggested Configuration:")
        config = {}
        
        # Find best Nova model
        for model in nova_models:
            if 'pro' in model['id'].lower():
                config['Amazon Nova Pro'] = model['id']
                break
        
        # Find best Claude model
        for model in claude_models:
            if '3-5' in model['id'] or '3.5' in model['id']:
                config['Anthropic Claude Sonnet 3.7'] = model['id']
                break
        
        if config:
            print("BEDROCK_MODELS = {")
            for name, model_id in config.items():
                print(f'    "{name}": "{model_id}",')
            print("}")
        else:
            print("❌ No suitable Nova Pro or Claude 3.5 models found")
        
        return True
        
    except ClientError as e:
        print(f"❌ AWS Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    list_all_bedrock_models()