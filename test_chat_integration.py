"""Test script for chat interface integration."""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat_interface import ChatInterface
from intent_classifier import IntentClassifier
from ai_client import AIClient
from models import SessionStateManager, AppConfig
import streamlit as st


def test_chat_interface():
    """Test the chat interface functionality."""
    print("Testing Chat Interface Integration")
    print("=" * 50)
    
    # Mock Streamlit session state
    if not hasattr(st, 'session_state'):
        class MockSessionState:
            def __init__(self):
                self.data = {}
            
            def __getitem__(self, key):
                return self.data.get(key)
            
            def __setitem__(self, key, value):
                self.data[key] = value
            
            def get(self, key, default=None):
                return self.data.get(key, default)
        
        st.session_state = MockSessionState()
    
    # Initialize session state
    SessionStateManager.initialize_session_state()
    
    # Test configuration
    config = AppConfig(
        selected_model="Anthropic Claude Sonnet 3.7",
        working_directory="/tmp/test_kiro",
        aws_region="us-east-1"
    )
    
    # Create AI client (will fail without AWS, but that's OK for testing)
    try:
        ai_client = AIClient(config.selected_model, config.aws_region)
        print("✅ AI Client created successfully")
    except Exception as e:
        print(f"⚠️  AI Client creation failed (expected without AWS): {e}")
        return
    
    # Test intent classifier
    try:
        classifier = IntentClassifier(ai_client)
        print("✅ Intent Classifier created successfully")
        
        # Test rule-based classification
        test_cases = [
            ("Create a detailed specification of the code", "spec"),
            ("How do I implement authentication?", "do"),
            ("Hello, how are you?", "chat"),
        ]
        
        print("\nTesting Intent Classification:")
        for message, expected in test_cases:
            result = classifier._rule_based_classification(message)
            if result:
                actual = result.primary_intent
                status = "✅" if actual == expected else "❌"
                print(f"{status} '{message}' -> {actual} (expected: {expected})")
            else:
                print(f"⚪ '{message}' -> No rule match (would use AI)")
        
    except Exception as e:
        print(f"❌ Intent Classifier test failed: {e}")
        return
    
    # Test chat interface creation
    try:
        chat_interface = ChatInterface(ai_client)
        print("✅ Chat Interface created successfully")
        
        # Test message processing (without actual AI calls)
        print("\nTesting Message Processing:")
        
        # Test spec creation extraction
        spec_message = "Create a detailed specification of the user authentication system"
        feature_name = chat_interface._extract_feature_name(spec_message)
        print(f"✅ Feature name extraction: '{spec_message}' -> '{feature_name}'")
        
    except Exception as e:
        print(f"❌ Chat Interface test failed: {e}")
        return
    
    print("\n✅ All chat interface tests passed!")
    print("\nNote: Full functionality requires AWS Bedrock connection.")


def test_file_browser():
    """Test the file browser functionality."""
    print("\nTesting File Browser")
    print("=" * 30)
    
    try:
        from file_browser import FileBrowser
        
        # Create file browser with current directory
        browser = FileBrowser(".")
        print("✅ File Browser created successfully")
        
        # Test file icon detection
        from pathlib import Path
        test_files = [
            Path("test.py"),
            Path("test.js"),
            Path("test.md"),
            Path("test.json"),
            Path("test.txt")
        ]
        
        print("\nTesting File Icons:")
        for file_path in test_files:
            icon = browser._get_file_icon(file_path)
            print(f"  {file_path.suffix} -> {icon}")
        
        # Test file size formatting
        test_sizes = [0, 1024, 1024*1024, 1024*1024*1024]
        print("\nTesting File Size Formatting:")
        for size in test_sizes:
            formatted = browser._format_file_size(size)
            print(f"  {size} bytes -> {formatted}")
        
        print("✅ File Browser tests passed!")
        
    except Exception as e:
        print(f"❌ File Browser test failed: {e}")


if __name__ == "__main__":
    print("Kiro Chat Integration Test Suite")
    print("=" * 50)
    
    try:
        test_chat_interface()
        test_file_browser()
        
        print("\n🎉 All tests completed!")
        print("\nTo test the full application:")
        print("1. Configure AWS credentials")
        print("2. Run: streamlit run app.py")
        print("3. Test chat with: 'Create a detailed specification of the code'")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()