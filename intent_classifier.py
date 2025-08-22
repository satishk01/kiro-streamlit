"""Intent classification system to mimic Kiro's behavior."""
import json
import re
from typing import Dict, List, Tuple
from dataclasses import dataclass
from ai_client import AIClient


@dataclass
class IntentResult:
    """Result of intent classification."""
    chat: float
    do: float
    spec: float
    
    @property
    def primary_intent(self) -> str:
        """Get the primary intent based on highest confidence."""
        if self.spec > max(self.chat, self.do):
            return "spec"
        elif self.do > self.chat:
            return "do"
        else:
            return "chat"


class IntentClassifier:
    """Classifies user intents to determine appropriate response mode."""
    
    INTENT_SYSTEM_PROMPT = """You are an intent classifier for a language model. Your job is to classify the user's intent based on their conversation history into one of two main categories:

1. **Do mode** (default for most requests)
2. **Spec mode** (only for specific specification/planning requests)

Return ONLY a JSON object with 3 properties (chat, do, spec) representing your confidence in each category. The values must always sum to 1.

### Category Definitions

#### 1. Do mode (DEFAULT CHOICE)
Input belongs in do mode if it:
- Is NOT explicitly about creating or working with specifications
- Requests modifications to code or the workspace
- Is an imperative sentence asking for action
- Starts with a base-form verb (e.g., "Write," "Create," "Generate")
- Has an implied subject ("you" is understood)
- Requests to run commands or make changes to files
- Asks for information, explanation, or clarification
- Ends with a question mark (?)
- Seeks information or explanation
- Starts with interrogative words like "who," "what," "where," "when," "why," or "how"
- Begins with a helping verb for yes/no questions, like "Is," "Are," "Can," "Should"
- Asks for explanation of code or concepts
- Examples include:
  - "Write a function to reverse a string."
  - "Create a new file called index.js."
  - "Fix the syntax errors in this function."
  - "Refactor this code to be more efficient."
  - "What is the capital of France?"
  - "How do promises work in JavaScript?"
  - "Can you explain this code?"
  - "Tell me about design patterns"

#### 2. Spec mode (ONLY for specification requests)
Input belongs in spec mode ONLY if it EXPLICITLY:
- Asks to create a specification (or spec)
- Uses the word "spec" or "specification" to request creating a formal spec
- Mentions creating a formal requirements document
- Involves executing tasks from existing specs
- Examples include:
  - "Create a spec for this feature"
  - "Generate a specification for the login system"
  - "Let's create a formal spec document for this project"
  - "Implement a spec based on this conversation"
  - "Execute task 3.2 from my-feature spec"
  - "Execute task 2 from My Feature"
  - "Start task 1 for the spec"
  - "Start the next task"
  - "What is the next task in the <feature name> spec?"

IMPORTANT: When in doubt, classify as "Do" mode. Only classify as "Spec" when the user is explicitly requesting to create or work with a formal specification document.

Ensure you look at the historical conversation between you and the user in addition to the latest user message when making your decision.

Previous messages may have context that is important to consider when combined with the user's latest reply.

IMPORTANT: Respond ONLY with a JSON object. No explanation, no commentary, no additional text, no code fences (```).

Example response:
{"chat": 0.0, "do": 0.9, "spec": 0.1}"""

    def __init__(self, ai_client: AIClient):
        """Initialize the intent classifier with an AI client."""
        self.ai_client = ai_client
        
    def classify_intent(self, user_message: str, conversation_history: List[Dict[str, str]] = None) -> IntentResult:
        """
        Classify user intent based on message and conversation history.
        
        Args:
            user_message: The latest user message
            conversation_history: List of previous messages with 'role' and 'content' keys
            
        Returns:
            IntentResult with confidence scores for each intent category
        """
        try:
            # First try rule-based classification for obvious cases
            rule_based_result = self._rule_based_classification(user_message)
            if rule_based_result:
                return rule_based_result
            
            # Fall back to AI-based classification
            return self._ai_based_classification(user_message, conversation_history)
            
        except Exception as e:
            # Default to "do" mode if classification fails
            print(f"Intent classification error: {e}")
            return IntentResult(chat=0.1, do=0.8, spec=0.1)
    
    def _rule_based_classification(self, user_message: str) -> IntentResult:
        """
        Apply rule-based classification for obvious cases.
        
        Returns:
            IntentResult if classification is confident, None otherwise
        """
        message_lower = user_message.lower().strip()
        
        # Strong spec indicators
        spec_keywords = [
            "create a spec",
            "generate a spec",
            "create specification",
            "generate specification",
            "formal spec",
            "spec document",
            "execute task",
            "start task",
            "next task",
            "task from",
            "spec for"
        ]
        
        for keyword in spec_keywords:
            if keyword in message_lower:
                return IntentResult(chat=0.0, do=0.1, spec=0.9)
        
        # Strong do indicators
        do_patterns = [
            r"^(write|create|generate|build|make|add|remove|delete|update|modify|fix|refactor)\s",
            r"^(how|what|why|when|where|who)\s",
            r"^(can|could|should|would|will|is|are|do|does)\s",
            r"\?$"  # Questions
        ]
        
        for pattern in do_patterns:
            if re.match(pattern, message_lower):
                return IntentResult(chat=0.1, do=0.8, spec=0.1)
        
        # If no strong indicators, return None to use AI classification
        return None
    
    def _ai_based_classification(self, user_message: str, conversation_history: List[Dict[str, str]] = None) -> IntentResult:
        """
        Use AI to classify intent when rule-based classification is uncertain.
        
        Args:
            user_message: The latest user message
            conversation_history: Previous conversation context
            
        Returns:
            IntentResult with AI-determined confidence scores
        """
        try:
            # Build context from conversation history
            context = ""
            if conversation_history:
                context = "Previous conversation:\n"
                for msg in conversation_history[-5:]:  # Last 5 messages for context
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    context += f"{role}: {content}\n"
                context += "\n"
            
            # Create the classification prompt
            prompt = f"{context}Here is the last user message:\n{user_message}"
            
            # Get AI classification
            response = self.ai_client.generate_response(
                prompt=prompt,
                system_prompt=self.INTENT_SYSTEM_PROMPT,
                max_tokens=100,
                temperature=0.1  # Low temperature for consistent classification
            )
            
            # Parse JSON response
            try:
                result_dict = json.loads(response.strip())
                
                # Validate the response format
                if not all(key in result_dict for key in ['chat', 'do', 'spec']):
                    raise ValueError("Missing required keys in response")
                
                # Ensure values sum to approximately 1.0
                total = sum(result_dict.values())
                if abs(total - 1.0) > 0.1:
                    # Normalize if needed
                    for key in result_dict:
                        result_dict[key] = result_dict[key] / total
                
                return IntentResult(
                    chat=float(result_dict['chat']),
                    do=float(result_dict['do']),
                    spec=float(result_dict['spec'])
                )
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                print(f"Failed to parse AI classification response: {e}")
                print(f"Response was: {response}")
                # Default to do mode
                return IntentResult(chat=0.1, do=0.8, spec=0.1)
                
        except Exception as e:
            print(f"AI classification error: {e}")
            # Default to do mode
            return IntentResult(chat=0.1, do=0.8, spec=0.1)
    
    def should_use_spec_mode(self, user_message: str, conversation_history: List[Dict[str, str]] = None, threshold: float = 0.6) -> bool:
        """
        Determine if spec mode should be used based on intent classification.
        
        Args:
            user_message: The user's message
            conversation_history: Previous conversation context
            threshold: Minimum confidence threshold for spec mode
            
        Returns:
            True if spec mode should be used, False otherwise
        """
        result = self.classify_intent(user_message, conversation_history)
        return result.spec >= threshold
    
    def get_mode_recommendation(self, user_message: str, conversation_history: List[Dict[str, str]] = None) -> Tuple[str, float]:
        """
        Get the recommended mode and confidence level.
        
        Args:
            user_message: The user's message
            conversation_history: Previous conversation context
            
        Returns:
            Tuple of (mode, confidence) where mode is 'chat', 'do', or 'spec'
        """
        result = self.classify_intent(user_message, conversation_history)
        
        if result.spec > max(result.chat, result.do):
            return ("spec", result.spec)
        elif result.do > result.chat:
            return ("do", result.do)
        else:
            return ("chat", result.chat)


class ConversationManager:
    """Manages conversation history for intent classification."""
    
    def __init__(self, max_history: int = 10):
        """Initialize with maximum history length."""
        self.max_history = max_history
        self.history: List[Dict[str, str]] = []
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.history.append({
            'role': role,
            'content': content
        })
        
        # Keep only the most recent messages
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get the current conversation history."""
        return self.history.copy()
    
    def clear_history(self):
        """Clear the conversation history."""
        self.history.clear()
    
    def get_recent_context(self, num_messages: int = 5) -> List[Dict[str, str]]:
        """Get the most recent messages for context."""
        return self.history[-num_messages:] if self.history else []