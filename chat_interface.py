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
from task_executor import TaskExecutor


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
        """Legacy method - redirect to unified interface."""
        self.render_unified_kiro_interface()
    
    def render_unified_kiro_interface(self):
        """Render the unified Kiro interface - everything in one chat like real Kiro."""
        # Kiro-style header
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown('<div class="main-header">🤖 Kiro</div>', unsafe_allow_html=True)
            st.markdown('<div class="sub-header">AI Development Assistant</div>', unsafe_allow_html=True)
        
        with col2:
            # Show current spec context if any
            current_workflow = SessionStateManager.get_workflow()
            if current_workflow:
                config = SessionStateManager.get_config()
                if config.working_directory:
                    try:
                        task_executor = TaskExecutor(self.ai_client, config.working_directory)
                        task_count = len(task_executor.parse_tasks_from_spec(current_workflow.feature_name))
                        st.markdown(f'<div class="status-indicator status-info">📋 Active: {current_workflow.feature_name} ({task_count} tasks)</div>', unsafe_allow_html=True)
                    except:
                        st.markdown(f'<div class="status-indicator status-info">📋 Active: {current_workflow.feature_name}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="status-indicator status-info">📋 Active: {current_workflow.feature_name}</div>', unsafe_allow_html=True)
        
        # Debug toggle (collapsed by default)
        with st.expander("🔧 Debug Options", expanded=False):
            st.session_state.show_intent_debug = st.checkbox(
                "Show intent classification details",
                value=st.session_state.show_intent_debug,
                help="Display intent classification scores for debugging"
            )
            
            st.session_state.show_context_debug = st.checkbox(
                "Show AI context information",
                value=getattr(st.session_state, 'show_context_debug', False),
                help="Display the context information sent to AI"
            )
            
            if st.button("🔍 Show Current Context"):
                config = SessionStateManager.get_config()
                if config.working_directory:
                    context = self._build_context_for_ai("Debug context check", config)
                    st.markdown("**Current Context:**")
                    st.code(context, language="markdown")
                else:
                    st.info("Set working directory to see context")
        
        # Chat messages container
        self._render_chat_messages()
        
        # Chat input
        self._render_chat_input()
    
    def _render_chat_messages(self):
        """Render the chat message history."""
        if not st.session_state.chat_messages:
            st.markdown("""
            <div class="document-container">
                <div class="document-header">👋 Welcome to Kiro</div>
                <div class="document-content">
                    <p>I'm your AI development assistant. I can help you with everything from planning to implementation:</p>
                    
                    <h4>📋 Specification & Planning</h4>
                    <ul>
                        <li>"Create a spec for user authentication system"</li>
                        <li>"Generate a specification for the payment module"</li>
                        <li>"What's the next task I should work on?"</li>
                        <li>"Create Jira tickets from the current spec"</li>
                    </ul>
                    
                    <h4>⚡ Development & Implementation</h4>
                    <ul>
                        <li>"Execute task 1" or "Implement the database setup"</li>
                        <li>"Create a FastAPI endpoint for user login"</li>
                        <li>"Add error handling to the auth function"</li>
                        <li>"Generate a React component for the dashboard"</li>
                    </ul>
                    
                    <h4>🔍 Code Review & Analysis</h4>
                    <ul>
                        <li>"Review this code for security issues"</li>
                        <li>"Suggest improvements for performance"</li>
                        <li>"Explain how this authentication system works"</li>
                        <li>"What are the best practices for this pattern?"</li>
                    </ul>
                    
                    <h4>📁 Project Management</h4>
                    <ul>
                        <li>"List available tasks in the current spec"</li>
                        <li>"Show me the project structure"</li>
                        <li>"Create documentation for this module"</li>
                        <li>"Generate tests for the user service"</li>
                    </ul>
                    
                    <p><strong>Just talk to me naturally!</strong> I understand context and can work on whatever you need. Select files in the sidebar to give me more context about your project.</p>
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
            
            # Show context debug info if enabled
            if getattr(st.session_state, 'show_context_debug', False) and message.role == "user":
                config = SessionStateManager.get_config()
                if config.working_directory:
                    context = self._build_context_for_ai(message.content, config)
                    with st.expander("🔍 Context sent to AI", expanded=False):
                        st.code(context[:500] + "..." if len(context) > 500 else context, language="markdown")
        
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
        """Process user input with unified Kiro-like behavior."""
        try:
            config = SessionStateManager.get_config()
            
            if not config.working_directory:
                response = "Please set your working directory in the sidebar first so I can help you with your project."
            else:
                # Get conversation history for context
                history = [
                    {"role": msg.role, "content": msg.content}
                    for msg in st.session_state.chat_messages[-5:]  # Last 5 messages
                ]
                
                # Classify intent for debugging but handle everything unified
                intent_result = self.intent_classifier.classify_intent(user_input, history)
                
                # Handle request in unified Kiro style
                response = self._handle_unified_kiro_request(user_input, intent_result)
            
            # Add user message to chat
            user_message = ChatMessage(
                role="user",
                content=user_input,
                timestamp=datetime.now(),
                intent_info={
                    "primary_intent": getattr(intent_result, 'primary_intent', 'chat'),
                    "chat": getattr(intent_result, 'chat', 0.5),
                    "do": getattr(intent_result, 'do', 0.5),
                    "spec": getattr(intent_result, 'spec', 0.5)
                } if 'intent_result' in locals() else {}
            )
            st.session_state.chat_messages.append(user_message)
            
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
    
    def _handle_unified_kiro_request(self, user_input: str, intent_result) -> str:
        """Handle all requests in unified Kiro style - no mode switching needed."""
        config = SessionStateManager.get_config()
        task_executor = TaskExecutor(self.ai_client, config.working_directory)
        current_workflow = SessionStateManager.get_workflow()
        
        user_lower = user_input.lower()
        
        # 1. SPEC CREATION - Create new specifications
        if any(keyword in user_lower for keyword in ["create spec", "create specification", "generate spec", "spec for"]):
            return self._create_spec_from_chat(user_input)
        
        # 2. JIRA TICKETS - Generate Jira tickets from current spec
        if any(keyword in user_lower for keyword in ["create jira", "jira ticket", "jira task", "generate jira"]):
            if not current_workflow:
                return "I need an active specification to create Jira tickets. Load a spec from the sidebar or create one by saying 'Create a spec for [your feature]'."
            return task_executor.create_jira_tickets(current_workflow.feature_name)
        
        # 3. TASK EXECUTION - Execute specific tasks from specs
        if any(keyword in user_lower for keyword in ["execute task", "implement task", "start task", "run task", "work on task"]):
            if not current_workflow:
                return "I need an active specification to execute tasks. Load a spec from the sidebar or create one first."
            
            task_id = self._extract_task_identifier(user_input)
            if task_id:
                return task_executor.execute_task(task_id, current_workflow.feature_name)
            else:
                return task_executor.list_available_tasks(current_workflow.feature_name)
        
        # 4. TASK MANAGEMENT - List tasks, get next task, etc.
        if any(keyword in user_lower for keyword in ["list task", "show task", "available task", "what task"]):
            if not current_workflow:
                return "No active specification. Load a spec from the sidebar to see its tasks."
            return task_executor.list_available_tasks(current_workflow.feature_name)
        
        if any(keyword in user_lower for keyword in ["next task", "what next", "what should i", "recommend"]):
            if not current_workflow:
                return "No active specification. Load a spec from the sidebar to get task recommendations."
            return task_executor.get_next_task(current_workflow.feature_name)
        
        # 5. VIBE CODING - Direct development requests
        if self._is_vibe_coding_request(user_input):
            return self._handle_vibe_coding(user_input)
        
        # 6. SPEC UPDATES - Update existing spec documents
        if any(keyword in user_lower for keyword in ["update requirement", "modify requirement", "change requirement"]):
            if not current_workflow:
                return "I need an active specification to update requirements. Load a spec from the sidebar first."
            return self._handle_spec_update(user_input, "requirements", current_workflow)
        
        if any(keyword in user_lower for keyword in ["update design", "modify design", "change design"]):
            if not current_workflow:
                return "I need an active specification to update the design. Load a spec from the sidebar first."
            return self._handle_spec_update(user_input, "design", current_workflow)
        
        if any(keyword in user_lower for keyword in ["add task", "more task", "update task"]):
            if not current_workflow:
                return "I need an active specification to update tasks. Load a spec from the sidebar first."
            return self._handle_spec_update(user_input, "tasks", current_workflow)
        
        # 7. CONTEXT-AWARE RESPONSES - Provide helpful guidance based on current state
        if current_workflow:
            # User has active spec - provide spec-specific help with context
            context_info = self._build_context_for_ai(user_input, config)
            
            enhanced_prompt = f"""User Request: {user_input}

{context_info}

The user has an active specification ({current_workflow.feature_name}) and is asking for help. Provide contextual assistance based on their project, current spec, and available tasks. Be specific and actionable."""

            try:
                response = self.ai_client.generate_response(
                    prompt=enhanced_prompt,
                    system_prompt=KIRO_SYSTEM_PROMPT,
                    max_tokens=1000,
                    temperature=0.7
                )
                return response
            except Exception as e:
                return f"I'm here to help with your **{current_workflow.feature_name}** specification. Current spec has {len(task_executor.parse_tasks_from_spec(current_workflow.feature_name))} tasks ready for implementation. What would you like to work on?"
        
        else:
            # No active spec - general Kiro help with full context
            return self._generate_kiro_response(user_input)
    
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
        """Generate a response using the full Kiro system prompt with proper context."""
        try:
            # Get project context
            config = SessionStateManager.get_config()
            context_info = self._build_context_for_ai(user_input, config)
            
            # Enhanced prompt with context
            enhanced_prompt = f"""User Request: {user_input}

{context_info}

Please respond as Kiro, using the context above to provide accurate, helpful assistance. If the user is asking about code, files, or project structure, use the provided context. If they want to create specifications, modify code, or perform development tasks, provide actionable guidance."""

            response = self.ai_client.generate_response(
                prompt=enhanced_prompt,
                system_prompt=KIRO_SYSTEM_PROMPT,
                max_tokens=1200,
                temperature=0.7
            )
            
            return response
            
        except Exception as e:
            return f"I ran into an issue generating a response: {str(e)}\n\nTry rephrasing your question or check your connection settings."
    
    def _create_spec_from_chat(self, user_input: str) -> str:
        """Create a specification directly from chat input with proper context."""
        try:
            # Extract feature name and description from user input
            feature_name = self._extract_feature_name(user_input)
            if not feature_name:
                feature_name = "code-specification"
            
            # Get current config
            config = SessionStateManager.get_config()
            
            if not config.working_directory or not config.selected_model:
                return """To create a specification, I need you to configure the application first:

1. **Set Working Directory** - Choose where to save the specification files
2. **Select AI Model** - Pick Amazon Nova Pro or Anthropic Claude Sonnet 3.7
3. **Test Connection** - Verify AWS Bedrock access

Once configured, I can create specifications directly from our chat!"""
            
            # Build context for better spec creation
            context_info = self._build_context_for_ai(user_input, config)
            
            # Enhanced feature description with context
            enhanced_description = f"""Feature Request: {user_input}

{context_info}

Please create a comprehensive specification for this feature, considering the current project context and following Kiro's specification standards."""
            
            # Create the specification workflow
            ai_client = AIClient(config.selected_model, config.aws_region)
            workflow = SpecWorkflow(feature_name, config.working_directory, ai_client)
            
            # Generate initial requirements with enhanced context
            requirements_content = workflow.create_requirements(enhanced_description)
            
            # Update session state
            SessionStateManager.set_workflow(workflow)
            SessionStateManager.set_feature_name(feature_name)
            SessionStateManager.set_current_content(requirements_content)
            
            return f"""✅ **Specification Created: {feature_name}**

I've analyzed your request in the context of your current project and created a comprehensive specification.

**📋 Requirements Generated**
- User stories with acceptance criteria
- Technical requirements based on project context
- Integration considerations with existing codebase

**📁 Files Created:**
- `{config.working_directory}/.kiro/specs/{feature_name}/requirements.md`

**🚀 Next Steps:**
- Say "Show me the requirements" to review them
- Say "Create the design document" to continue
- Say "List available tasks" once the spec is complete

The specification is now active and I can help you with tasks, Jira tickets, and implementation!"""
            
        except Exception as e:
            return f"""I encountered an error creating the specification: {str(e)}

Please check:
- Your AWS connection is working
- The working directory is accessible  
- The AI model is properly configured

Try rephrasing your request or check the debug options for more details."""
    
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
        """Handle vibe coding requests with file operations and proper context."""
        try:
            config = SessionStateManager.get_config()
            
            if not config.working_directory:
                return """To perform file operations, I need a working directory configured.

Please set your working directory in the sidebar first, then I can help you with:
- Creating and modifying files
- Generating code
- Refactoring existing code
- File operations and project management"""
            
            # Build comprehensive context for vibe coding
            context_info = self._build_context_for_ai(user_input, config)
            
            # Enhanced vibe coding prompt with context
            enhanced_request = f"""Development Request: {user_input}

{context_info}

Please analyze the request in the context of the current project structure and provide specific, actionable code solutions. Use the Kiro system prompt guidelines for code generation, file operations, and best practices."""
            
            # Initialize vibe coding with enhanced context
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
            
            # Process the vibe coding request with enhanced context
            result = vibe_coding.process_vibe_request(enhanced_request, context_files)
            
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
    
    def _extract_task_identifier(self, user_input: str) -> str:
        """Extract task identifier from user input."""
        import re
        
        # Look for task numbers
        number_match = re.search(r'task\s+(\d+)', user_input.lower())
        if number_match:
            return f"task-{number_match.group(1)}"
        
        # Look for task names after keywords
        keywords = ['execute', 'implement', 'start', 'work on', 'run']
        for keyword in keywords:
            pattern = f'{keyword}\s+(.+?)(?:\s|$)'
            match = re.search(pattern, user_input.lower())
            if match:
                task_name = match.group(1).strip()
                # Clean up common words
                task_name = re.sub(r'\b(task|the|a|an)\b', '', task_name).strip()
                if task_name:
                    return task_name
        
        return ""
    
    def _handle_spec_update(self, user_input: str, doc_type: str, workflow: SpecWorkflow) -> str:
        """Handle updates to specification documents."""
        try:
            if doc_type == "requirements":
                # Extract what user wants to change about requirements
                change_request = user_input.replace("update requirement", "").replace("modify requirement", "").strip()
                updated_content = workflow.update_requirements(change_request)
                return f"✅ **Requirements Updated**\n\nI've updated the requirements based on your request. The changes have been saved to the requirements.md file.\n\n**Summary of changes:** {change_request}"
            
            elif doc_type == "design":
                change_request = user_input.replace("update design", "").replace("modify design", "").strip()
                updated_content = workflow.update_design(change_request)
                return f"✅ **Design Updated**\n\nI've updated the design document based on your request. The changes have been saved to the design.md file.\n\n**Summary of changes:** {change_request}"
            
            elif doc_type == "tasks":
                change_request = user_input.replace("add task", "").replace("more task", "").replace("update task", "").strip()
                updated_content = workflow.update_tasks(change_request)
                return f"✅ **Tasks Updated**\n\nI've updated the implementation tasks based on your request. The changes have been saved to the tasks.md file.\n\n**Summary of changes:** {change_request}"
            
            else:
                return f"Unknown document type: {doc_type}"
                
        except Exception as e:
            return f"Error updating {doc_type}: {str(e)}" 
   def _build_context_for_ai(self, user_input: str, config) -> str:
        """Build comprehensive context for AI responses."""
        context_parts = []
        
        # 1. Project Structure Context
        if config.working_directory:
            try:
                from pathlib import Path
                project_root = Path(config.working_directory)
                
                # Get key project files
                key_files = []
                for pattern in ["*.py", "*.md", "*.json", "*.txt"]:
                    key_files.extend(list(project_root.glob(pattern)))
                
                if key_files:
                    context_parts.append("**Project Structure:**")
                    context_parts.append(f"Working Directory: {config.working_directory}")
                    context_parts.append("Key Files:")
                    for file in key_files[:10]:  # Limit to first 10 files
                        relative_path = file.relative_to(project_root)
                        context_parts.append(f"- {relative_path}")
                    
                    if len(key_files) > 10:
                        context_parts.append(f"... and {len(key_files) - 10} more files")
            except Exception:
                pass
        
        # 2. Active Specification Context
        current_workflow = SessionStateManager.get_workflow()
        if current_workflow:
            context_parts.append(f"\n**Active Specification:** {current_workflow.feature_name}")
            
            # Get spec files content
            try:
                spec_dir = Path(config.working_directory) / ".kiro" / "specs" / current_workflow.feature_name
                
                for doc_name in ["requirements.md", "design.md", "tasks.md"]:
                    doc_path = spec_dir / doc_name
                    if doc_path.exists():
                        with open(doc_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Include first 500 chars of each document
                        preview = content[:500] + "..." if len(content) > 500 else content
                        context_parts.append(f"\n**{doc_name}:**")
                        context_parts.append(preview)
            except Exception:
                pass
        
        # 3. Selected File Context
        if "file_browser_selected_file" in st.session_state and st.session_state.file_browser_selected_file:
            selected_file = st.session_state.file_browser_selected_file
            try:
                with open(selected_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                # Include file content (first 1000 chars)
                preview = file_content[:1000] + "..." if len(file_content) > 1000 else file_content
                context_parts.append(f"\n**Selected File:** {selected_file}")
                context_parts.append(f"```\n{preview}\n```")
            except Exception:
                pass
        
        # 4. Recent Chat Context
        if st.session_state.chat_messages:
            recent_messages = st.session_state.chat_messages[-3:]  # Last 3 messages
            context_parts.append("\n**Recent Conversation:**")
            for msg in recent_messages:
                role = "User" if msg.role == "user" else "Assistant"
                content_preview = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                context_parts.append(f"{role}: {content_preview}")
        
        # 5. Available Capabilities
        context_parts.append("\n**Available Capabilities:**")
        context_parts.append("- Specification creation and management")
        context_parts.append("- Code analysis and review")
        context_parts.append("- File operations and modifications")
        context_parts.append("- Task execution from specifications")
        context_parts.append("- Jira ticket generation")
        context_parts.append("- Project structure analysis")
        
        return "\n".join(context_parts)