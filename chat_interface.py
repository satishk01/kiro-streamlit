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
from kiro_system_prompt import KIRO_SYSTEM_PROMPT
from vibe_coding import VibeCoding


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
                        <li><strong>Vibe coding</strong> - "Create a Python script", "Add a function to handle auth"</li>
                        <li><strong>File operations</strong> - "Modify config.py", "Generate a new component"</li>
                        <li><strong>Code analysis</strong> - "Review this code", "Suggest improvements"</li>
                        <li><strong>Answering questions</strong> - Ask about code, concepts, or best practices</li>
                        <li><strong>Executing tasks</strong> - Work through implementation tasks from specs</li>
                    </ul>
                    <p><strong>Vibe Coding Examples:</strong></p>
                    <ul>
                        <li>"Create a FastAPI endpoint for user authentication"</li>
                        <li>"Add error handling to the database connection"</li>
                        <li>"Generate a React component for the dashboard"</li>
                        <li>"Refactor this function to be more efficient"</li>
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
        if any(keyword in user_input.lower() for keyword in ["create spec", "create specification", "generate spec", "detailed specification"]):
            return self._create_spec_from_chat(user_input)
        
        # Check if user wants to execute tasks
        if any(keyword in user_input.lower() for keyword in ["execute task", "start task", "next task"]):
            return self._handle_task_execution(user_input)
        
        # General spec guidance
        return """I can help you with specifications! Here are some options:

**Create a new specification:**
- Tell me what you want to build and I'll create a spec for you
- Or use the "Specification Workflow" tab above

**Work with existing specs:**
- Load a specification from the sidebar
- Execute specific tasks from your implementation plan

**Need help?**
- Ask me about the specification workflow
- Get guidance on requirements, design, or tasks

What would you like to do?"""
    
    def _handle_do_intent(self, user_input: str, intent_result) -> str:
        """Handle action/modification requests."""
        # Check if this is a vibe coding request (file operations, code generation)
        if self._is_vibe_coding_request(user_input):
            return self._handle_vibe_coding(user_input)
        
        # Use Kiro system prompt for regular responses
        return self._generate_kiro_response(user_input)
    
    def _handle_chat_intent(self, user_input: str, intent_result) -> str:
        """Handle general chat/informational requests."""
        return self._generate_kiro_response(user_input)
    
    def _generate_kiro_response(self, user_input: str) -> str:
        """Generate a response using the full Kiro system prompt."""
        try:
            response = self.ai_client.generate_response(
                prompt=user_input,
                system_prompt=KIRO_SYSTEM_PROMPT,
                max_tokens=800,
                temperature=0.7
            )
            
            return response
            
        except Exception as e:
            return f"I ran into an issue generating a response: {str(e)}\n\nTry rephrasing your question or check your connection settings."
    
    def _create_spec_from_chat(self, user_input: str) -> str:
        """Create a specification directly from chat input."""
        try:
            # Extract feature name and description from user input
            feature_name = self._extract_feature_name(user_input)
            if not feature_name:
                feature_name = "code-specification"
            
            # Use the user input as the feature description
            feature_description = user_input
            
            # Get current config
            config = SessionStateManager.get_config()
            
            if not config.working_directory or not config.selected_model:
                return """To create a specification, I need you to configure the application first:

1. **Set Working Directory** - Choose where to save the specification files
2. **Select AI Model** - Pick Amazon Nova Pro or Anthropic Claude Sonnet 3.7
3. **Test Connection** - Verify AWS Bedrock access

Once configured, I can create specifications directly from our chat!"""
            
            # Create the specification workflow
            ai_client = AIClient(config.selected_model, config.aws_region)
            workflow = SpecWorkflow(feature_name, config.working_directory, ai_client)
            
            # Generate initial requirements
            requirements_content = workflow.create_requirements(feature_description)
            
            # Update session state
            SessionStateManager.set_workflow(workflow)
            SessionStateManager.set_feature_name(feature_name)
            SessionStateManager.set_current_content(requirements_content)
            
            return f"""Perfect! I've created a specification for **{feature_name}**.

📋 **Requirements Generated**
The initial requirements document has been created based on your description. 

**Next Steps:**
1. Switch to the "Specification Workflow" tab to review the requirements
2. Approve or request changes to the requirements
3. Continue through the Design and Tasks phases

The specification will be saved to: `{config.working_directory}/.kiro/specs/{feature_name}/`

Would you like me to help with anything else while you review the requirements?"""
            
        except Exception as e:
            return f"""I encountered an error creating the specification: {str(e)}

Please check:
- Your AWS connection is working
- The working directory is accessible
- The AI model is properly configured

You can also use the "Specification Workflow" tab to create specifications manually."""
    
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
    
    def _is_vibe_coding_request(self, user_input: str) -> bool:
        """Check if the request is for vibe coding (file operations, code generation)."""
        vibe_keywords = [
            "create file", "write file", "generate code", "modify file", "edit file",
            "delete file", "refactor", "implement", "add function", "create class",
            "write script", "generate", "build", "make file", "update code",
            "fix code", "improve code", "optimize", "add to file"
        ]
        
        user_lower = user_input.lower()
        return any(keyword in user_lower for keyword in vibe_keywords)
    
    def _handle_vibe_coding(self, user_input: str) -> str:
        """Handle vibe coding requests with file operations."""
        try:
            config = SessionStateManager.get_config()
            
            if not config.working_directory:
                return """To perform file operations, I need a working directory configured.

Please set your working directory in the sidebar first, then I can help you with:
- Creating and modifying files
- Generating code
- Refactoring existing code
- File operations and project management"""
            
            # Initialize vibe coding
            vibe_coding = VibeCoding(self.ai_client, config.working_directory)
            
            # Get context files if any are selected
            context_files = []
            if "file_browser_selected_file" in st.session_state and st.session_state.file_browser_selected_file:
                selected_file = st.session_state.file_browser_selected_file
                # Convert absolute path to relative path
                from pathlib import Path
                try:
                    relative_path = Path(selected_file).relative_to(Path(config.working_directory))
                    context_files.append(str(relative_path))
                except ValueError:
                    pass  # File is outside working directory
            
            # Process the vibe coding request
            result = vibe_coding.process_vibe_request(user_input, context_files)
            
            if not result.success:
                return f"I encountered an issue: {result.error_message}\n\nTry rephrasing your request or check your configuration."
            
            # Execute file operations if any
            if result.file_operations:
                success, errors = vibe_coding.execute_file_operations(result.file_operations)
                
                if success:
                    operation_summary = self._format_operations_summary(result.file_operations)
                    response = f"{result.response}\n\n**Operations Completed:**\n{operation_summary}"
                else:
                    error_summary = "\n".join(errors)
                    response = f"{result.response}\n\n**Errors occurred:**\n{error_summary}"
            else:
                response = result.response
            
            # Add shell commands if any
            if result.shell_commands:
                commands_text = "\n".join([f"```bash\n{cmd}\n```" for cmd in result.shell_commands])
                response += f"\n\n**Suggested Commands:**\n{commands_text}"
            
            return response
            
        except Exception as e:
            return f"Error processing vibe coding request: {str(e)}\n\nPlease check your configuration and try again."
    
    def _format_operations_summary(self, operations) -> str:
        """Format a summary of completed file operations."""
        summary = []
        
        for op in operations:
            if op.operation == "create":
                summary.append(f"✅ Created: `{op.file_path}`")
            elif op.operation == "modify":
                summary.append(f"✅ Modified: `{op.file_path}`")
            elif op.operation == "delete":
                summary.append(f"✅ Deleted: `{op.file_path}`")
        
        return "\n".join(summary)
    
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