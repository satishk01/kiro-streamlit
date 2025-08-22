#!/usr/bin/env python3
"""Test spec creation detection logic."""

# Mock the necessary classes for testing
class MockIntentResult:
    def __init__(self, primary_intent='chat'):
        self.primary_intent = primary_intent

class MockChatInterface:
    def _detect_spec_creation_intent(self, user_input: str, intent_result, current_workflow) -> bool:
        """Detect if user input indicates they want to create a specification."""
        user_lower = user_input.lower()
        
        # 1. Explicit spec creation requests
        explicit_patterns = [
            "create spec", "create specification", "generate spec", "spec for",
            "new spec", "make spec", "build spec"
        ]
        
        if any(pattern in user_lower for pattern in explicit_patterns):
            return True
        
        # 2. Check intent classifier result
        if hasattr(intent_result, 'primary_intent') and intent_result.primary_intent == 'spec':
            return True
        
        # 3. Natural language patterns that indicate wanting to build something
        # Only trigger if no active workflow (don't interrupt existing work)
        if current_workflow:
            return False
        
        build_patterns = [
            "i want to build", "i need to create", "i want to make", "i need to build",
            "help me build", "help me create", "help me make", "let's build", "let's create",
            "i want to develop", "help me develop", "let's develop"
        ]
        
        if any(pattern in user_lower for pattern in build_patterns):
            return True
        
        # 4. Action + object patterns (build a, create a, etc.)
        action_object_patterns = [
            "build a", "create a", "make a", "develop a", "implement a",
            "design a", "plan a"
        ]
        
        if any(pattern in user_lower for pattern in action_object_patterns):
            return True
        
        # 5. System/feature description patterns
        system_patterns = [
            "system for", "feature for", "application for", "app for", "tool for",
            "service for", "api for", "website for", "dashboard for", "interface for"
        ]
        
        if any(pattern in user_lower for pattern in system_patterns):
            return True
        
        # 6. Heuristic: mentions building/creating + project indicators
        action_words = ["build", "create", "make", "develop", "implement", "design"]
        project_indicators = [
            "system", "feature", "app", "application", "tool", "service", "api", 
            "website", "dashboard", "interface", "authentication", "login", "user", 
            "management", "platform", "portal", "module", "component", "library"
        ]
        
        has_action = any(word in user_lower for word in action_words)
        has_project_indicator = any(indicator in user_lower for indicator in project_indicators)
        
        if has_action and has_project_indicator:
            return True
        
        # 7. Planning/architecture requests
        planning_patterns = [
            "plan for", "design for", "architecture for", "how to build", "how to create",
            "how to implement", "how to develop", "steps to build", "steps to create"
        ]
        
        if any(pattern in user_lower for pattern in planning_patterns):
            return True
        
        return False

def test_spec_detection():
    """Test the spec creation detection logic."""
    chat = MockChatInterface()
    
    # Test cases that SHOULD trigger spec creation
    should_trigger = [
        "I want to build a user authentication system",
        "Create a spec for user management",
        "Help me build a dashboard",
        "I need to create a login feature",
        "Build a REST API for users",
        "Let's create an authentication system",
        "I want to develop a user portal",
        "Make a user management system",
        "Design a login interface",
        "How to build a user authentication system",
        "Plan for user management feature"
    ]
    
    # Test cases that should NOT trigger spec creation
    should_not_trigger = [
        "How are you?",
        "What's the weather?",
        "Show me the current code",
        "List the files in this directory",
        "What does this function do?",
        "Fix this bug in my code"
    ]
    
    print("🧪 Testing Spec Creation Detection")
    print("=" * 50)
    
    print("\n✅ Should trigger spec creation:")
    for test_input in should_trigger:
        result = chat._detect_spec_creation_intent(test_input, MockIntentResult(), None)
        status = "✅" if result else "❌"
        print(f"{status} '{test_input}' -> {result}")
    
    print("\n❌ Should NOT trigger spec creation:")
    for test_input in should_not_trigger:
        result = chat._detect_spec_creation_intent(test_input, MockIntentResult(), None)
        status = "✅" if not result else "❌"
        print(f"{status} '{test_input}' -> {result}")
    
    print("\n🔄 With active workflow (should not trigger):")
    for test_input in should_trigger[:3]:
        result = chat._detect_spec_creation_intent(test_input, MockIntentResult(), "existing_workflow")
        status = "✅" if not result else "❌"
        print(f"{status} '{test_input}' (with workflow) -> {result}")

if __name__ == "__main__":
    test_spec_detection()