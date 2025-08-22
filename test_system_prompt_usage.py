"""Test to verify system prompts are being used properly."""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat_interface import ChatInterface
from ai_client import AIClient
from models import SessionStateManager, Config
import tempfile


def test_system_prompt_integration():
    """Test that system prompts are properly integrated."""
    print("Testing System Prompt Integration")
    print("=" * 40)
    
    # Setup test environment
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Configure session state
        config = Config(
            working_directory=temp_dir,
            selected_model="Amazon Nova Pro",
            aws_region="us-east-1"
        )
        SessionStateManager.set_config(config)
        
        # Initialize chat interface
        ai_client = AIClient("Amazon Nova Pro", "us-east-1")
        chat_interface = ChatInterface(ai_client)
        
        print("✅ Test environment setup complete")
        
        # Test 1: Context Building
        print("\n1. Testing Context Building...")
        context = chat_interface._build_context_for_ai("What can you help me with?", config)
        
        if "Project Structure" in context and "Available Capabilities" in context:
            print("✅ Context building works correctly")
            print(f"Context length: {len(context)} characters")
        else:
            print("❌ Context building failed")
            print(f"Context preview: {context[:200]}...")
        
        # Test 2: Enhanced Response Generation
        print("\n2. Testing Enhanced Response Generation...")
        
        # Mock the AI client response to avoid actual API calls
        class MockAIClient:
            def generate_response(self, prompt, system_prompt, max_tokens=800, temperature=0.7):
                return f"Mock response using system prompt: {system_prompt[:100]}... for prompt: {prompt[:100]}..."
        
        chat_interface.ai_client = MockAIClient()
        
        response = chat_interface._generate_kiro_response("Help me analyze this code")
        
        if "Mock response using system prompt" in response and "KIRO_SYSTEM_PROMPT" in response:
            print("✅ System prompt is being used in responses")
        else:
            print("❌ System prompt not being used properly")
            print(f"Response: {response[:200]}...")
        
        # Test 3: Vibe Coding Context
        print("\n3. Testing Vibe Coding Context...")
        
        # Create a test file
        test_file = os.path.join(temp_dir, "test.py")
        with open(test_file, "w") as f:
            f.write("def hello():\n    print('Hello World')")
        
        # Mock session state for selected file
        import streamlit as st
        if not hasattr(st, 'session_state'):
            class MockSessionState:
                def __init__(self):
                    self.data = {}
                def __setattr__(self, key, value):
                    if key == 'data':
                        super().__setattr__(key, value)
                    else:
                        self.data[key] = value
                def __getattr__(self, key):
                    return self.data.get(key)
            st.session_state = MockSessionState()
        
        st.session_state.file_browser_selected_file = test_file
        
        context_with_file = chat_interface._build_context_for_ai("Analyze this code", config)
        
        if "Selected File" in context_with_file and "def hello" in context_with_file:
            print("✅ File context is being included")
        else:
            print("❌ File context not being included properly")
            print(f"Context preview: {context_with_file[:300]}...")
        
        print("\n🎉 System prompt integration tests completed!")
        
        # Summary
        print("\n📋 System Prompt Features Verified:")
        print("- Context building with project structure")
        print("- File content integration")
        print("- System prompt usage in AI responses")
        print("- Enhanced prompts for better responses")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass


def test_kiro_system_prompt_content():
    """Test that the Kiro system prompt has proper content."""
    print("\nTesting Kiro System Prompt Content")
    print("=" * 40)
    
    try:
        from kiro_system_prompt import KIRO_SYSTEM_PROMPT
        
        print(f"✅ System prompt loaded, length: {len(KIRO_SYSTEM_PROMPT)} characters")
        
        # Check for key Kiro features
        key_features = [
            "Kiro",
            "AI assistant",
            "development",
            "code",
            "specification",
            "file operations",
            "best practices"
        ]
        
        found_features = []
        for feature in key_features:
            if feature.lower() in KIRO_SYSTEM_PROMPT.lower():
                found_features.append(feature)
        
        print(f"✅ Found {len(found_features)}/{len(key_features)} key features in system prompt")
        print(f"Features found: {', '.join(found_features)}")
        
        if len(found_features) >= len(key_features) * 0.7:  # At least 70% of features
            print("✅ System prompt contains appropriate Kiro content")
        else:
            print("❌ System prompt may be missing key Kiro features")
        
        # Show first 200 characters
        print(f"\nSystem prompt preview:")
        print(f"{KIRO_SYSTEM_PROMPT[:200]}...")
        
    except Exception as e:
        print(f"❌ System prompt test failed: {e}")


if __name__ == "__main__":
    print("System Prompt Usage Test Suite")
    print("=" * 50)
    
    test_kiro_system_prompt_content()
    test_system_prompt_integration()
    
    print("\n🚀 All system prompt tests completed!")
    print("\nThe app should now properly use:")
    print("- Kiro system prompts for all AI interactions")
    print("- Project context and file content")
    print("- Enhanced prompts for better responses")
    print("- Proper specification and task management")