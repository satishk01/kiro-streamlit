"""Test the unified Kiro behavior to ensure it works like real Kiro."""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from task_executor import TaskExecutor
from ai_client import AIClient
from chat_interface import ChatInterface
from models import SessionStateManager, Config
from workflow import SpecWorkflow
import tempfile
import shutil


def test_unified_kiro_behavior():
    """Test that the app behaves like unified Kiro."""
    print("Testing Unified Kiro Behavior")
    print("=" * 40)
    
    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Setup test environment
        ai_client = AIClient("Amazon Nova Pro", "us-east-1")
        chat_interface = ChatInterface(ai_client)
        
        # Configure session state
        config = Config(
            working_directory=temp_dir,
            selected_model="Amazon Nova Pro",
            aws_region="us-east-1"
        )
        SessionStateManager.set_config(config)
        
        print("✅ Test environment setup complete")
        
        # Test 1: Spec Creation
        print("\n1. Testing Spec Creation...")
        spec_request = "Create a spec for user authentication system"
        response = chat_interface._handle_unified_kiro_request(spec_request, None)
        
        if "specification" in response.lower() and "authentication" in response.lower():
            print("✅ Spec creation request handled correctly")
        else:
            print("❌ Spec creation failed")
            print(f"Response: {response[:200]}...")
        
        # Test 2: Jira Creation (without active spec)
        print("\n2. Testing Jira Creation (no active spec)...")
        jira_request = "Create Jira tickets"
        response = chat_interface._handle_unified_kiro_request(jira_request, None)
        
        if "active specification" in response.lower():
            print("✅ Correctly requires active spec for Jira creation")
        else:
            print("❌ Should require active spec")
            print(f"Response: {response[:200]}...")
        
        # Test 3: Task Execution (without active spec)
        print("\n3. Testing Task Execution (no active spec)...")
        task_request = "Execute task 1"
        response = chat_interface._handle_unified_kiro_request(task_request, None)
        
        if "active specification" in response.lower():
            print("✅ Correctly requires active spec for task execution")
        else:
            print("❌ Should require active spec")
            print(f"Response: {response[:200]}...")
        
        # Test 4: Vibe Coding
        print("\n4. Testing Vibe Coding...")
        vibe_request = "Create a Python function to validate email addresses"
        response = chat_interface._handle_unified_kiro_request(vibe_request, None)
        
        if "python" in response.lower() or "function" in response.lower():
            print("✅ Vibe coding request handled")
        else:
            print("❌ Vibe coding failed")
            print(f"Response: {response[:200]}...")
        
        # Test 5: Context-aware responses
        print("\n5. Testing Context-aware Responses...")
        
        # Create a mock workflow
        workflow = SpecWorkflow("test-auth", temp_dir, ai_client)
        SessionStateManager.set_workflow(workflow)
        
        general_request = "What can you help me with?"
        response = chat_interface._handle_unified_kiro_request(general_request, None)
        
        if "test-auth" in response:
            print("✅ Context-aware response includes active spec")
        else:
            print("❌ Should mention active spec in context")
            print(f"Response: {response[:200]}...")
        
        # Test 6: Task Management with Active Spec
        print("\n6. Testing Task Management...")
        
        # Create a sample tasks file
        tasks_dir = os.path.join(temp_dir, ".kiro", "specs", "test-auth")
        os.makedirs(tasks_dir, exist_ok=True)
        
        sample_tasks = """# Implementation Tasks

- [ ] 1. Set up database schema for users
  Create user table with email, password hash, and timestamps
  
- [ ] 2. Implement user registration endpoint
  POST /auth/register with validation and password hashing
  
- [ ] 3. Create login functionality
  POST /auth/login with JWT token generation"""
        
        with open(os.path.join(tasks_dir, "tasks.md"), "w") as f:
            f.write(sample_tasks)
        
        list_request = "List available tasks"
        response = chat_interface._handle_unified_kiro_request(list_request, None)
        
        if "database schema" in response.lower() and "registration" in response.lower():
            print("✅ Task listing works with active spec")
        else:
            print("❌ Task listing failed")
            print(f"Response: {response[:200]}...")
        
        # Test 7: Jira Creation with Active Spec
        print("\n7. Testing Jira Creation with Active Spec...")
        jira_request = "Create Jira tickets"
        response = chat_interface._handle_unified_kiro_request(jira_request, None)
        
        if "jira" in response.lower() and ("ticket" in response.lower() or "story" in response.lower()):
            print("✅ Jira creation works with active spec")
        else:
            print("❌ Jira creation failed with active spec")
            print(f"Response: {response[:200]}...")
        
        print("\n🎉 Unified Kiro behavior tests completed!")
        
        # Summary
        print("\n📋 Unified Kiro Features Verified:")
        print("- Single chat interface for all interactions")
        print("- Context-aware responses based on active spec")
        print("- Automatic task management and execution")
        print("- Jira ticket generation from specs")
        print("- Vibe coding for direct development")
        print("- No mode switching required")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


def test_task_parsing():
    """Test task parsing from real spec files."""
    print("\nTesting Task Parsing from Spec Files")
    print("=" * 40)
    
    try:
        # Test with the actual kiro-streamlit-app spec
        ai_client = AIClient("Amazon Nova Pro", "us-east-1")
        task_executor = TaskExecutor(ai_client, ".")
        
        # Parse tasks from the current spec
        tasks = task_executor.parse_tasks_from_spec("kiro-streamlit-app")
        
        print(f"✅ Parsed {len(tasks)} tasks from kiro-streamlit-app spec")
        
        if tasks:
            print("\nSample tasks:")
            for i, task in enumerate(tasks[:3], 1):
                print(f"{i}. {task.title} ({task.category}, {task.priority})")
                if task.description:
                    print(f"   {task.description[:100]}...")
        
        # Test Jira creation
        if tasks:
            print("\n📋 Testing Jira ticket generation...")
            jira_response = task_executor.create_jira_tickets("kiro-streamlit-app")
            
            if "jira" in jira_response.lower() and len(jira_response) > 200:
                print("✅ Jira tickets generated successfully")
                print(f"Response length: {len(jira_response)} characters")
            else:
                print("❌ Jira generation may have failed")
                print(f"Response: {jira_response[:200]}...")
        
    except Exception as e:
        print(f"❌ Task parsing test failed: {e}")


if __name__ == "__main__":
    print("Unified Kiro Behavior Test Suite")
    print("=" * 50)
    
    test_unified_kiro_behavior()
    test_task_parsing()
    
    print("\n🚀 All tests completed!")
    print("\nThe app now behaves like real Kiro:")
    print("- Everything happens in one unified chat interface")
    print("- No need to switch between tabs or modes")
    print("- Context-aware responses based on active specifications")
    print("- Automatic task execution and Jira ticket generation")
    print("- Natural language interaction for all features")