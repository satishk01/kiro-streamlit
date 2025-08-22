"""Test script for the intent classifier."""
from intent_classifier import IntentClassifier
from ai_client import AIClient


def test_rule_based_classification():
    """Test rule-based classification with sample inputs."""
    print("Testing Rule-Based Classification:")
    print("=" * 50)
    
    # Create a dummy AI client (won't be used for rule-based tests)
    ai_client = AIClient("test-model", "us-east-1")
    classifier = IntentClassifier(ai_client)
    
    test_cases = [
        # Spec mode examples
        ("Create a spec for user authentication", "spec"),
        ("Generate a specification for the login system", "spec"),
        ("Execute task 3.2 from my-feature spec", "spec"),
        ("Start the next task", "spec"),
        
        # Do mode examples
        ("Write a function to reverse a string", "do"),
        ("How do promises work in JavaScript?", "do"),
        ("Can you explain this code?", "do"),
        ("What is the capital of France?", "do"),
        ("Fix the syntax errors in this function", "do"),
        
        # Ambiguous cases (should default to do)
        ("Hello there", "do"),
        ("Help me with this project", "do"),
    ]
    
    for message, expected in test_cases:
        result = classifier._rule_based_classification(message)
        
        if result:
            actual = result.primary_intent
            status = "✅" if actual == expected else "❌"
            print(f"{status} '{message}' -> {actual} (expected: {expected})")
            if result:
                print(f"    Scores: chat={result.chat:.2f}, do={result.do:.2f}, spec={result.spec:.2f}")
        else:
            print(f"⚪ '{message}' -> No rule match (would use AI classification)")
        print()


def test_intent_patterns():
    """Test specific intent patterns."""
    print("\nTesting Intent Patterns:")
    print("=" * 50)
    
    ai_client = AIClient("test-model", "us-east-1")
    classifier = IntentClassifier(ai_client)
    
    # Test spec keywords
    spec_messages = [
        "I want to create a spec for my new feature",
        "Let's generate a specification document",
        "Can you help me create a formal spec?",
        "Execute task 1 from the authentication spec",
        "What's the next task in my project spec?",
    ]
    
    print("Spec Mode Messages:")
    for msg in spec_messages:
        result = classifier._rule_based_classification(msg)
        if result:
            print(f"  '{msg}' -> {result.primary_intent} (spec: {result.spec:.2f})")
        else:
            print(f"  '{msg}' -> No rule match")
    
    print("\nDo Mode Messages:")
    do_messages = [
        "Write a Python function",
        "How does async/await work?",
        "Can you refactor this code?",
        "What are the best practices for testing?",
        "Is this the right approach?",
    ]
    
    for msg in do_messages:
        result = classifier._rule_based_classification(msg)
        if result:
            print(f"  '{msg}' -> {result.primary_intent} (do: {result.do:.2f})")
        else:
            print(f"  '{msg}' -> No rule match")


if __name__ == "__main__":
    print("Intent Classifier Test Suite")
    print("=" * 50)
    
    try:
        test_rule_based_classification()
        test_intent_patterns()
        
        print("\n✅ All tests completed!")
        print("\nNote: AI-based classification tests require a valid AWS connection.")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")