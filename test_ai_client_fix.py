"""Test script to verify AIClient method fix."""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_client import AIClient


def test_ai_client_methods():
    """Test that AIClient has both generate_content and generate_response methods."""
    print("Testing AIClient Method Availability")
    print("=" * 50)
    
    try:
        # Create AI client
        ai_client = AIClient("Amazon Nova Pro", "us-east-1")
        print("✅ AIClient created successfully")
        
        # Check if generate_content method exists
        if hasattr(ai_client, 'generate_content'):
            print("✅ generate_content method exists")
        else:
            print("❌ generate_content method missing")
        
        # Check if generate_response method exists
        if hasattr(ai_client, 'generate_response'):
            print("✅ generate_response method exists")
        else:
            print("❌ generate_response method missing")
        
        # Test method signatures
        import inspect
        
        # Check generate_content signature
        content_sig = inspect.signature(ai_client.generate_content)
        print(f"✅ generate_content signature: {content_sig}")
        
        # Check generate_response signature
        response_sig = inspect.signature(ai_client.generate_response)
        print(f"✅ generate_response signature: {response_sig}")
        
        print("\n✅ All method checks passed!")
        print("\nNote: Actual AI calls require AWS connection.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_ai_client_methods()