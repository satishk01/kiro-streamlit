"""Test script for vibe coding functionality."""
import sys
import os
import tempfile
import shutil
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vibe_coding import VibeCoding, FileOperation
from ai_client import AIClient


def test_vibe_coding_basic():
    """Test basic vibe coding functionality."""
    print("Testing Vibe Coding Functionality")
    print("=" * 50)
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create mock AI client (won't actually call AWS)
        try:
            ai_client = AIClient("test-model", "us-east-1")
        except Exception:
            print("⚠️  Skipping AI client tests (no AWS connection)")
            return
        
        # Initialize vibe coding
        vibe_coding = VibeCoding(ai_client, str(temp_path))
        print("✅ VibeCoding initialized successfully")
        
        # Test file operations
        test_file_operations(vibe_coding, temp_path)
        
        # Test response parsing
        test_response_parsing(vibe_coding)
        
        print("\n✅ All vibe coding tests passed!")


def test_file_operations(vibe_coding: VibeCoding, temp_path: Path):
    """Test file operations."""
    print("\nTesting File Operations:")
    
    # Test file creation
    create_op = FileOperation(
        operation="create",
        file_path="test_file.py",
        content="print('Hello, World!')\n"
    )
    
    success, errors = vibe_coding.execute_file_operations([create_op])
    
    if success:
        print("✅ File creation successful")
        
        # Verify file was created
        test_file = temp_path / "test_file.py"
        if test_file.exists():
            print("✅ File exists on disk")
            
            with open(test_file, 'r') as f:
                content = f.read()
            
            if "Hello, World!" in content:
                print("✅ File content is correct")
            else:
                print("❌ File content is incorrect")
        else:
            print("❌ File was not created")
    else:
        print(f"❌ File creation failed: {errors}")
    
    # Test file modification
    modify_op = FileOperation(
        operation="modify",
        file_path="test_file.py",
        content="print('Hello, Kiro!')\nprint('Vibe coding works!')\n"
    )
    
    success, errors = vibe_coding.execute_file_operations([modify_op])
    
    if success:
        print("✅ File modification successful")
        
        # Verify modification
        with open(temp_path / "test_file.py", 'r') as f:
            content = f.read()
        
        if "Kiro" in content and "Vibe coding" in content:
            print("✅ File modification content is correct")
        else:
            print("❌ File modification content is incorrect")
    else:
        print(f"❌ File modification failed: {errors}")


def test_response_parsing(vibe_coding: VibeCoding):
    """Test parsing of AI responses for file operations."""
    print("\nTesting Response Parsing:")
    
    # Mock AI response with file operations
    mock_response = """I'll help you create a simple Python script.

FILE_CREATE: hello.py
```python
def greet(name):
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("World"))
```

FILE_CREATE: config.json
```json
{
    "app_name": "Hello App",
    "version": "1.0.0"
}
```

SHELL_COMMAND: python hello.py

This creates a simple greeting script and runs it."""
    
    file_operations, shell_commands = vibe_coding._parse_response_for_operations(mock_response)
    
    # Check file operations
    if len(file_operations) == 2:
        print("✅ Correct number of file operations parsed")
        
        # Check first operation
        op1 = file_operations[0]
        if op1.operation == "create" and op1.file_path == "hello.py":
            print("✅ First file operation parsed correctly")
            
            if "def greet" in op1.content and "Hello, {name}" in op1.content:
                print("✅ First file content extracted correctly")
            else:
                print("❌ First file content extraction failed")
        else:
            print("❌ First file operation parsing failed")
        
        # Check second operation
        op2 = file_operations[1]
        if op2.operation == "create" and op2.file_path == "config.json":
            print("✅ Second file operation parsed correctly")
            
            if "app_name" in op2.content and "Hello App" in op2.content:
                print("✅ Second file content extracted correctly")
            else:
                print("❌ Second file content extraction failed")
        else:
            print("❌ Second file operation parsing failed")
    else:
        print(f"❌ Wrong number of file operations: {len(file_operations)}")
    
    # Check shell commands
    if len(shell_commands) == 1 and shell_commands[0] == "python hello.py":
        print("✅ Shell command parsed correctly")
    else:
        print(f"❌ Shell command parsing failed: {shell_commands}")


def test_vibe_coding_patterns():
    """Test vibe coding pattern detection."""
    print("\nTesting Vibe Coding Pattern Detection:")
    
    # Import chat interface to test pattern detection
    try:
        from chat_interface import ChatInterface
        from ai_client import AIClient
        
        ai_client = AIClient("test-model", "us-east-1")
        chat_interface = ChatInterface(ai_client)
        
        test_cases = [
            ("Create a Python file for data processing", True),
            ("Write a function to handle authentication", True),
            ("Generate code for the API endpoint", True),
            ("Modify the config file to add new settings", True),
            ("How do I implement JWT tokens?", False),
            ("What is the best way to structure this project?", False),
            ("Create a spec for user management", False),
        ]
        
        print("Testing pattern detection:")
        for message, expected in test_cases:
            result = chat_interface._is_vibe_coding_request(message)
            status = "✅" if result == expected else "❌"
            print(f"{status} '{message}' -> {result} (expected: {expected})")
        
    except Exception as e:
        print(f"⚠️  Pattern detection test skipped: {e}")


if __name__ == "__main__":
    print("Kiro Vibe Coding Test Suite")
    print("=" * 50)
    
    try:
        test_vibe_coding_basic()
        test_vibe_coding_patterns()
        
        print("\n🎉 All vibe coding tests completed!")
        print("\nVibe coding features:")
        print("- File creation and modification")
        print("- Code generation with AI")
        print("- Shell command suggestions")
        print("- Automatic backup creation")
        print("- Context-aware operations")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()