"""Chat interface with intent classification for Kiro-like behavior."""
import streamlit as st
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import json

from intent_classifier import IntentClassifier, ConversationManager
from ai_client import AIClient
from models import SessionStateManager
from workflow import SpecWorkflow


@dataclass
class ChatMessage:
    """Represents a chat message."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    intent_info: Optional[Dict] = None


class ChatInterface:
    """Main chat interface with intent classification."""
    
    def __init__(self, ai_client: AIClient):
        """Initialize the chat interface."""
        self.ai_client = ai_client
        self.intent_classifier = IntentClassifier(ai_client)
        self.conversation_manager = ConversationManager()
        
        # Initialize session state for chat
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        if "chat_input" not in st.session_state:
            st.session_state.chat_input = ""
        if "show_intent_debug" not in st.session_state:
            st.session_state.show_intent_debug = False
    
    def render_chat_interface(self):
        """Render the main chat interface."""
        st.markdown('<div class="main-header">💬 Kiro Assistant</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Ask questions, request changes, or create specifications</div>', unsafe_allow_html=True)
        
        # Debug toggle
        with st.expander("🔧 Debug Options", expanded=False):
            st.session_state.show_intent_debug = st.checkbox(
                "Show intent classification details",
                value=st.session_state.show_intent_debug,
                help="Display intent classification scores for debugging"
            )
        
        # Chat messages container
        self._render_chat_messages()
        
        # Chat input
        self._render_chat_input()
    
    def _render_chat_messages(self):
        """Render the chat message history."""
        if not st.session_state.chat_messages:
            st.markdown("""
            <div class="document-container">
                <div class="document-header">👋 Welcome to Kiro Assistant</div>
                <div class="document-content">
                    <p>I can help you with:</p>
                    <ul>
                        <li><strong>Creating specifications</strong> - Say "create a spec for [feature]"</li>
                        <li><strong>Answering questions</strong> - Ask about code, concepts, or best practices</li>
                        <li><strong>Making changes</strong> - Request code modifications or file operations</li>
                        <li><strong>Executing tasks</strong> - Work through implementation tasks from specs</li>
                    </ul>
                    <p>Try asking me something or describe what you'd like to build!</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Display messages
        for message in st.session_state.chat_messages:
            self._render_message(message)
    
    def _render_message(self, message: ChatMessage):
        """Render a single chat message."""
        if message.role == "user":
            # User message
            st.markdown(f"""
            <div class="document-container" style="margin-left: 2rem;">
                <div class="document-header">👤 You</div>
                <div class="document-content">
                    {message.content}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show intent debug info if enabled
            if st.session_state.show_intent_debug and message.intent_info:
                intent_info = message.intent_info
                st.markdown(f"""
                <div style="margin-left: 2rem; margin-top: -1rem;">
                    <small style="color: #6b7280;">
                        Intent: {intent_info.get('primary_intent', 'unknown')} 
                        (chat: {intent_info.get('chat', 0):.2f}, 
                         do: {intent_info.get('do', 0):.2f}, 
                         spec: {intent_info.get('spec', 0):.2f})
                    </small>
                </div>
                """, unsafe_allow_html=True)
        
        else:
            # Assistant message
            st.markdown(f"""
            <div class="document-container" style="margin-right: 2rem;">
                <div class="document-header">🤖 Kiro</div>
                <div class="document-content">
                    {message.content}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_chat_input(self):
        """Render the chat input area."""
        st.markdown("---")
        
        # Chat input form
        with st.form("chat_form", clear_on_submit=True):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                user_input = st.text_area(
                    "Message",
                    placeholder="Ask a question, request changes, or say 'create a spec for [feature name]'...",
                    height=100,
                    key="chat_input_area",
                    label_visibility="collapsed"
                )
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)  # Spacing
                submit_button = st.form_submit_button("Send", use_container_width=True, type="primary")
        
        # Process input when submitted
        if submit_button and user_input.strip():
            self._process_user_input(user_input.strip())
    
    def _process_user_input(self, user_input: str):
        """Process user input and generate appropriate response."""
        try:
            # Get conversation history for context
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in st.session_state.chat_messages[-5:]  # Last 5 messages
            ]
            
            # Classify intent
            intent_result = self.intent_classifier.classify_intent(user_input, history)
            
            # Add user message to chat
            user_message = ChatMessage(
                role="user",
                content=user_input,
                timestamp=datetime.now(),
                intent_info={
                    "primary_intent": intent_result.primary_intent,
                    "chat": intent_result.chat,
                    "do": intent_result.do,
                    "spec": intent_result.spec
                }
            )
            st.session_state.chat_messages.append(user_message)
            
            # Generate response based on intent
            if intent_result.primary_intent == "spec":
                response = self._handle_spec_intent(user_input, intent_result)
            elif intent_result.primary_intent == "do":
                response = self._handle_do_intent(user_input, intent_result)
            else:
                response = self._handle_chat_intent(user_input, intent_result)
            
            # Add assistant response to chat
            assistant_message = ChatMessage(
                role="assistant",
                content=response,
                timestamp=datetime.now()
            )
            st.session_state.chat_messages.append(assistant_message)
            
            # Update conversation manager
            self.conversation_manager.add_message("user", user_input)
            self.conversation_manager.add_message("assistant", response)
            
            # Rerun to show new messages
            st.rerun()
            
        except Exception as e:
            st.error(f"Error processing message: {str(e)}")
    
    def _handle_spec_intent(self, user_input: str, intent_result) -> str:
        """Handle specification-related requests."""
        # Check if user wants to create a new spec
        if any(keyword in user_input.lower() for keyword in ["create spec", "create specification", "generate spec"]):
            return self._suggest_spec_creation(user_input)
        
        # Check if user wants to execute tasks
        if any(keyword in user_input.lower() for keyword in ["execute task", "start task", "next task"]):
            return self._handle_task_execution(user_input)
        
        # General spec guidance
        return """I can help you with specifications! Here are some options:

**Create a new specification:**
- Use the "Create New Specification" form above
- Or tell me more about what you want to build

**Work with existing specs:**
- Load a specification from the sidebar
- Execute specific tasks from your implementation plan

**Need help?**
- Ask me about the specification workflow
- Get guidance on requirements, design, or tasks

What would you like to do?"""
    
    def _handle_do_intent(self, user_input: str, intent_result) -> str:
        """Handle action/modification requests."""
        # This would integrate with actual code modification capabilities
        # For now, provide helpful guidance
        
        if "?" in user_input:
            # Question - provide informational response
            return self._generate_informational_response(user_input)
        else:
            # Action request - guide user
            return f"""I understand you want me to: {user_input}

Currently, I'm focused on helping with specifications. For code modifications and file operations, you can:

1. **Create a specification first** - This helps plan the implementation
2. **Use the task execution feature** - Break down work into manageable steps
3. **Ask specific questions** - I can provide guidance and best practices

Would you like to create a specification for this work, or do you have specific questions I can help with?"""
    
    def _handle_chat_intent(self, user_input: str, intent_result) -> str:
        """Handle general chat/informational requests."""
        return self._generate_informational_response(user_input)
    
    def _generate_informational_response(self, user_input: str) -> str:
        """Generate an informational response using the AI client."""
        try:
            system_prompt = """You are Kiro, a helpful AI assistant focused on software development and specifications. 
            Provide clear, concise, and helpful responses. If the question is about creating specifications or planning features, 
            gently suggest using the specification workflow. Keep responses focused and practical."""
            
            response = self.ai_client.generate_response(
                prompt=user_input,
                system_prompt=system_prompt,
                max_tokens=500,
                temperature=0.7
            )
            
            return response
            
        except Exception as e:
            return f"I apologize, but I encountered an error generating a response: {str(e)}\n\nPlease try rephrasing your question or check your connection settings."
    
    def _suggest_spec_creation(self, user_input: str) -> str:
        """Suggest creating a specification based on user input."""
        # Extract potential feature name from input
        feature_suggestion = self._extract_feature_name(user_input)
        
        suggestion = "I'd be happy to help you create a specification! "
        
        if feature_suggestion:
            suggestion += f"It looks like you want to create a spec for: **{feature_suggestion}**\n\n"
        
        suggestion += """To get started:

1. **Use the form above** - Fill in the feature name and description
2. **Or provide more details** - Tell me more about what you want to build

The specification workflow will help you create:
- 📋 **Requirements** - User stories and acceptance criteria
- 🏗️ **Design** - Technical architecture and components  
- ✅ **Tasks** - Implementation plan with actionable steps

What would you like to build?"""
        
        return suggestion
    
    def _extract_feature_name(self, user_input: str) -> Optional[str]:
        """Extract potential feature name from user input."""
        # Simple extraction - look for common patterns
        import re
        
        patterns = [
            r"spec for (.+?)(?:\.|$)",
            r"specification for (.+?)(?:\.|$)",
            r"create.*?spec.*?for (.+?)(?:\.|$)",
            r"build (.+?)(?:\.|$)",
            r"create (.+?)(?:\.|$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                feature_name = match.group(1).strip()
                # Clean up the feature name
                feature_name = re.sub(r'[^\w\s-]', '', feature_name)
                feature_name = re.sub(r'\s+', '-', feature_name)
                return feature_name
        
        return None
    
    def _handle_task_execution(self, user_input: str) -> str:
        """Handle task execution requests."""
        # Check if there's an active workflow
        current_workflow = SessionStateManager.get_workflow()
        
        if not current_workflow:
            return """To execute tasks, you need to have an active specification loaded.

**To get started:**
1. Load an existing specification from the sidebar
2. Or create a new specification first

**Available specifications:**
Check the sidebar for any existing specs you can load.

Once you have a specification loaded, I can help you execute specific tasks from the implementation plan."""
        
        # If there's an active workflow, provide task guidance
        current_phase = current_workflow.get_current_phase()
        
        return f"""I can see you have the **{current_workflow.feature_name}** specification loaded.

**Current Phase:** {current_phase.value.title()}

To execute tasks:
1. Make sure all previous phases are complete
2. Use the main interface above to work through the workflow
3. Ask me specific questions about implementation

**Need help with a specific task?**
Tell me which task number you want to work on, and I can provide guidance!"""
    
    def clear_chat(self):
        """Clear the chat history."""
        st.session_state.chat_messages = []
        self.conversation_manager.clear_history()
    
    def export_chat(self) -> str:
        """Export chat history as JSON."""
        chat_data = {
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "intent_info": msg.intent_info
                }
                for msg in st.session_state.chat_messages
            ],
            "exported_at": datetime.now().isoformat()
        }
        return json.dumps(chat_data, indent=2)