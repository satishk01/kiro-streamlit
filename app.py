"""Main Streamlit application for Kiro specification workflow."""
import streamlit as st
import os
from pathlib import Path
from config import ConfigManager, BEDROCK_MODELS
from ai_client import AIClient
from file_manager import FileManager
from workflow import SpecWorkflow, WorkflowPhase
from models import SessionStateManager, UIStateManager, AppConfig
from chat_interface import ChatInterface


def setup_page_config():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="Kiro Spec Creator",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Enhanced CSS for Kiro-like styling with better UX
    st.markdown("""
    <style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Typography */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.5rem;
        line-height: 1.2;
    }
    
    .sub-header {
        font-size: 1.125rem;
        color: #6b7280;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Phase indicator styling */
    .phase-progress {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 2rem 0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    
    .phase-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        flex: 1;
        position: relative;
    }
    
    .phase-step:not(:last-child)::after {
        content: '';
        position: absolute;
        top: 20px;
        right: -50%;
        width: 100%;
        height: 2px;
        background: #e5e7eb;
        z-index: 1;
    }
    
    .phase-step.active::after {
        background: #3b82f6;
    }
    
    .phase-step.complete::after {
        background: #10b981;
    }
    
    .phase-icon {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.875rem;
        margin-bottom: 0.5rem;
        z-index: 2;
        position: relative;
    }
    
    .phase-icon.pending {
        background: #f3f4f6;
        color: #9ca3af;
        border: 2px solid #e5e7eb;
    }
    
    .phase-icon.active {
        background: #3b82f6;
        color: white;
        border: 2px solid #3b82f6;
    }
    
    .phase-icon.complete {
        background: #10b981;
        color: white;
        border: 2px solid #10b981;
    }
    
    .phase-label {
        font-size: 0.875rem;
        font-weight: 500;
        color: #374151;
    }
    
    /* Document preview styling */
    .document-container {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        margin: 2rem 0;
        overflow: hidden;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    
    .document-header {
        background: #f9fafb;
        border-bottom: 1px solid #e5e7eb;
        padding: 1rem 1.5rem;
        font-weight: 600;
        color: #374151;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .document-content {
        padding: 2rem;
        line-height: 1.6;
    }
    
    /* Action buttons */
    .action-row {
        display: flex;
        gap: 1rem;
        margin-top: 2rem;
        padding-top: 1.5rem;
        border-top: 1px solid #e5e7eb;
    }
    
    .btn-primary {
        background: #3b82f6 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }
    
    .btn-primary:hover {
        background: #2563eb !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
    }
    
    .btn-secondary {
        background: #f3f4f6 !important;
        color: #374151 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }
    
    .btn-secondary:hover {
        background: #e5e7eb !important;
        transform: translateY(-1px);
    }
    
    /* Sidebar sections */
    .sidebar-section {
        margin-bottom: 2rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid #e5e7eb;
    }
    
    .sidebar-section:last-child {
        border-bottom: none;
    }
    
    .sidebar-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.25rem;
    }
    
    .sidebar-subtitle {
        font-size: 0.875rem;
        color: #6b7280;
        margin-bottom: 1.5rem;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.375rem 0.75rem;
        border-radius: 6px;
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    
    .status-success {
        background: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
    }
    
    .status-warning {
        background: #fef3c7;
        color: #92400e;
        border: 1px solid #fde68a;
    }
    
    .status-error {
        background: #fee2e2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
    
    .status-info {
        background: #dbeafe;
        color: #1e40af;
        border: 1px solid #bfdbfe;
    }
    
    /* Spec list styling */
    .spec-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        background: white;
        transition: all 0.2s;
        cursor: pointer;
    }
    
    .spec-item:hover {
        border-color: #3b82f6;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
    }
    
    .spec-status {
        font-size: 1.25rem;
    }
    
    .spec-name {
        font-weight: 500;
        color: #374151;
        flex: 1;
    }
    
    /* Form styling */
    .form-container {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 2rem;
        margin: 2rem 0;
    }
    
    /* Welcome screen */
    .welcome-container {
        text-align: center;
        padding: 4rem 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        color: white;
        margin: 2rem 0;
    }
    
    .welcome-title {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    .welcome-subtitle {
        font-size: 1.25rem;
        opacity: 0.9;
        margin-bottom: 2rem;
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
        margin-top: 3rem;
    }
    
    .feature-card {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 2rem;
        backdrop-filter: blur(10px);
    }
    
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 1rem;
    }
    
    .feature-title {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .feature-description {
        opacity: 0.9;
        line-height: 1.5;
    }
    
    /* Chat interface styling */
    .chat-container {
        max-height: 600px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        background: #f9fafb;
    }
    
    .chat-message {
        margin-bottom: 1rem;
        padding: 1rem;
        border-radius: 8px;
        max-width: 80%;
    }
    
    .chat-message.user {
        background: #dbeafe;
        margin-left: auto;
        text-align: right;
    }
    
    .chat-message.assistant {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        margin-right: auto;
    }
    
    .chat-input-container {
        margin-top: 1rem;
        padding: 1rem;
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
    }
    
    .intent-debug {
        font-size: 0.75rem;
        color: #6b7280;
        margin-top: 0.25rem;
        font-style: italic;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding: 0 1.5rem;
        background: #f3f4f6;
        border-radius: 8px 8px 0 0;
        border: 1px solid #e5e7eb;
        border-bottom: none;
    }
    
    .stTabs [aria-selected="true"] {
        background: #ffffff;
        border-color: #3b82f6;
        color: #3b82f6;
    }
    </style>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render sidebar with configuration options."""
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-section">
            <div class="sidebar-title">🤖 Kiro</div>
            <div class="sidebar-subtitle">Specification Creator</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Model selection
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("**🧠 AI Model**")
        
        config_manager = ConfigManager()
        available_models = list(config_manager.get_available_models().keys())
        current_config = SessionStateManager.get_config()
        
        if available_models:
            selected_model = st.selectbox(
                "Select AI Model",
                available_models,
                index=available_models.index(current_config.selected_model) if current_config.selected_model in available_models else 0,
                key="model_selector",
                help="Choose the AI model for generating specifications"
            )
            
            if selected_model != current_config.selected_model:
                SessionStateManager.update_config(selected_model=selected_model)
        else:
            st.markdown('<div class="status-indicator status-error">❌ No models available</div>', unsafe_allow_html=True)
            selected_model = current_config.selected_model
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Project configuration
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("**📁 Project**")
        
        working_directory = st.text_input(
            "Working Directory",
            value=current_config.working_directory,
            placeholder="Enter project directory path",
            key="directory_input",
            help="Path where specifications will be saved"
        )
        
        if working_directory:
            if config_manager.validate_directory(working_directory):
                st.markdown('<div class="status-indicator status-success">✅ Directory ready</div>', unsafe_allow_html=True)
                SessionStateManager.update_config(working_directory=working_directory)
                
                file_manager = FileManager(working_directory)
                file_manager.ensure_kiro_structure()
            else:
                st.markdown('<div class="status-indicator status-error">❌ Invalid directory</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # AWS Configuration
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("**☁️ AWS Bedrock**")
        
        bedrock_regions = ["us-east-1", "us-west-2", "eu-west-1", "eu-central-1"]
        
        region_index = 0
        if current_config.aws_region in bedrock_regions:
            region_index = bedrock_regions.index(current_config.aws_region)
        
        aws_region = st.selectbox(
            "AWS Region",
            bedrock_regions,
            index=region_index,
            key="region_selector",
            help="Select AWS region for Bedrock service"
        )
        
        if aws_region != current_config.aws_region:
            SessionStateManager.update_config(aws_region=aws_region)
        
        # Connection test
        if st.button("🔗 Test Connection", use_container_width=True, type="primary"):
            with st.spinner("Testing connection..."):
                try:
                    basic_success, basic_message = config_manager.test_aws_connectivity()
                    
                    if basic_success:
                        st.markdown('<div class="status-indicator status-success">✅ AWS Connected</div>', unsafe_allow_html=True)
                        
                        if selected_model:
                            ai_client = AIClient(selected_model, aws_region)
                            model_success, model_message = ai_client.test_connection()
                            
                            if model_success:
                                st.markdown('<div class="status-indicator status-success">🤖 Model Ready</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="status-indicator status-error">❌ Model Error: {model_message}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="status-indicator status-error">❌ Connection Failed: {basic_message}</div>', unsafe_allow_html=True)
                        
                except Exception as e:
                    st.markdown(f'<div class="status-indicator status-error">❌ Error: {str(e)}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Existing specs
        if working_directory and config_manager.validate_directory(working_directory):
            file_manager = FileManager(working_directory)
            existing_specs = file_manager.list_existing_specs()
            
            if existing_specs:
                st.markdown("**📚 Specifications**")
                
                for spec in existing_specs:
                    req_exists, design_exists, tasks_exists = file_manager.get_spec_status(spec)
                    
                    # Create status indicator and description
                    if req_exists and design_exists and tasks_exists:
                        status = "✅"
                        status_text = "Complete"
                        status_class = "status-success"
                    elif req_exists and design_exists:
                        status = "🏗️"
                        status_text = "Design Ready"
                        status_class = "status-info"
                    elif req_exists:
                        status = "📋"
                        status_text = "Requirements Only"
                        status_class = "status-warning"
                    else:
                        status = "🔄"
                        status_text = "In Progress"
                        status_class = "status-warning"
                    
                    # Create clickable spec item
                    spec_container = st.container()
                    with spec_container:
                        if st.button(f"{status} {spec}", key=f"load_{spec}", use_container_width=True, help=f"Status: {status_text}"):
                            SessionStateManager.set_feature_name(spec)
                            ai_client = AIClient(selected_model, aws_region)
                            workflow = SpecWorkflow(spec, working_directory, ai_client)
                            workflow.load_existing_spec()
                            SessionStateManager.set_workflow(workflow)
                            st.rerun()
                        
                        # Show status below button
                        st.markdown(f'<div class="status-indicator {status_class}" style="margin-top: 0.25rem; font-size: 0.75rem;">{status_text}</div>', unsafe_allow_html=True)


def render_main_content():
    """Render main content area."""
    config = SessionStateManager.get_config()
    
    # Add tab navigation for different modes
    if config.working_directory and config.selected_model:
        tab1, tab2 = st.tabs(["💬 Chat Assistant", "📋 Specification Workflow"])
        
        with tab1:
            # Render chat interface
            ai_client = AIClient(config.selected_model, config.aws_region)
            chat_interface = ChatInterface(ai_client)
            chat_interface.render_chat_interface()
        
        with tab2:
            # Render specification workflow
            render_spec_workflow_content()
        
        return
    
    # Check if configuration is complete
    if not config.working_directory or not config.selected_model:
        st.markdown("""
        <div class="welcome-container">
            <div class="welcome-title">Welcome to Kiro</div>
            <div class="welcome-subtitle">Transform ideas into comprehensive specifications</div>
            
            <div class="feature-grid">
                <div class="feature-card">
                    <div class="feature-icon">📋</div>
                    <div class="feature-title">Requirements</div>
                    <div class="feature-description">Define user stories and acceptance criteria using EARS format for clear, testable requirements</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🏗️</div>
                    <div class="feature-title">Design</div>
                    <div class="feature-description">Create comprehensive technical designs with architecture, components, and data models</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">✅</div>
                    <div class="feature-title">Tasks</div>
                    <div class="feature-description">Generate actionable implementation tasks with proper hierarchy and dependencies</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Getting started steps
        st.markdown("### 🚀 Getting Started")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **1. Configure AI Model**
            - Select Amazon Nova Pro or Anthropic Claude Sonnet 3.7
            - Choose your preferred AWS region
            
            **2. Set Project Directory**
            - Specify where specifications will be saved
            - Kiro will create the necessary folder structure
            """)
        
        with col2:
            st.markdown("""
            **3. Test Connection**
            - Verify AWS Bedrock access
            - Ensure your selected model is available
            
            **4. Start Creating**
            - Begin with a new specification
            - Or load an existing one to continue
            """)
        
        return
    
def render_spec_workflow_content():
    """Render the specification workflow content."""
    current_workflow = SessionStateManager.get_workflow()
    
    if not current_workflow:
        # No active workflow - show new spec creation
        render_new_spec_form()
    else:
        # Active workflow - show workflow interface
        render_workflow_interface(current_workflow)


def render_new_spec_form():
    """Render form for creating new specification."""
    st.markdown('<div class="main-header">Create New Specification</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Transform your feature idea into a comprehensive specification</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    
    feature_name = st.text_input(
        "Feature Name",
        placeholder="e.g., user-authentication, payment-system, dashboard-analytics",
        help="Use kebab-case format (lowercase with hyphens). This will be used for file organization.",
        key="new_feature_name"
    )
    
    feature_idea = st.text_area(
        "Feature Description",
        placeholder="Describe your feature idea in detail...\n\nExample:\nI want to build a user authentication system that allows users to sign up, log in, and manage their profiles. The system should support email/password authentication, password reset functionality, and user profile management with avatar uploads.",
        height=200,
        help="Provide a comprehensive description of what you want to build. Include the main functionality, user interactions, and any specific requirements you have in mind.",
        key="feature_idea"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Action buttons
    col1, col2 = st.columns([3, 1])
    
    with col2:
        start_disabled = not (feature_name and feature_idea and len(feature_idea.strip()) > 20)
        
        if st.button("🚀 Start Workflow", disabled=start_disabled, use_container_width=True, type="primary"):
            if feature_name and feature_idea:
                try:
                    config = SessionStateManager.get_config()
                    ai_client = AIClient(config.selected_model, config.aws_region)
                    
                    # Create new workflow
                    workflow = SpecWorkflow(feature_name, config.working_directory, ai_client)
                    SessionStateManager.set_workflow(workflow)
                    SessionStateManager.set_feature_name(feature_name)
                    
                    # Generate initial requirements
                    with st.spinner("🤖 Generating initial requirements..."):
                        requirements_content = workflow.create_requirements(feature_idea)
                        SessionStateManager.set_current_content(requirements_content)
                    
                    st.success("✅ Requirements generated! Please review and approve to continue.")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error creating specification: {str(e)}")
    
    with col1:
        if start_disabled and feature_name:
            if len(feature_idea.strip()) <= 20:
                st.info("💡 Please provide a more detailed feature description (at least 20 characters)")
        elif start_disabled:
            st.info("💡 Please fill in both the feature name and description to get started")


def render_workflow_interface(workflow: SpecWorkflow):
    """Render the main workflow interface."""
    st.markdown(f'<div class="main-header">📋 {workflow.feature_name}</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Specification Workflow</div>', unsafe_allow_html=True)
    
    # Show phase indicator
    UIStateManager.show_phase_indicator(workflow.get_current_phase())
    
    # Handle different workflow phases
    if workflow.get_current_phase() == WorkflowPhase.REQUIREMENTS:
        render_requirements_phase(workflow)
    elif workflow.get_current_phase() == WorkflowPhase.DESIGN:
        render_design_phase(workflow)
    elif workflow.get_current_phase() == WorkflowPhase.TASKS:
        render_tasks_phase(workflow)
    elif workflow.get_current_phase() == WorkflowPhase.COMPLETE:
        render_complete_phase(workflow)


def render_requirements_phase(workflow: SpecWorkflow):
    """Render requirements phase interface."""
    if workflow.state.requirements_content:
        UIStateManager.show_document_preview(workflow.state.requirements_content, "Requirements Document")
        
        if not workflow.state.requirements_approved:
            # Show feedback form if requested
            if st.session_state.get("show_requirements_feedback", False):
                feedback = UIStateManager.show_feedback_form("requirements")
                if feedback:
                    with st.spinner("🤖 Updating requirements based on feedback..."):
                        updated_content = workflow.update_requirements(feedback)
                        SessionStateManager.set_current_content(updated_content)
                    st.session_state["show_requirements_feedback"] = False
                    st.success("✅ Requirements updated! Please review the changes.")
                    st.rerun()
            else:
                action = UIStateManager.show_approval_buttons("requirements")
                
                if action == "approve":
                    workflow.approve_requirements()
                    st.success("✅ Requirements approved! Moving to design phase...")
                    st.rerun()
                elif action == "changes":
                    st.session_state["show_requirements_feedback"] = True
                    st.rerun()
        else:
            st.markdown('<div class="status-indicator status-success">✅ Requirements approved and ready for design phase</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-indicator status-info">ℹ️ No requirements content available. Please start a new specification.</div>', unsafe_allow_html=True)


def render_design_phase(workflow: SpecWorkflow):
    """Render design phase interface."""
    if not workflow.state.design_content:
        st.markdown('<div class="status-indicator status-info">🏗️ Ready to generate design document</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🏗️ Generate Design", use_container_width=True, type="primary"):
                with st.spinner("🤖 Generating comprehensive design document..."):
                    design_content = workflow.create_design()
                    SessionStateManager.set_current_content(design_content)
                st.rerun()
        
        with col1:
            st.info("💡 The design document will include architecture, components, data models, and technical specifications based on your approved requirements.")
    else:
        UIStateManager.show_document_preview(workflow.state.design_content, "Design Document")
        
        if not workflow.state.design_approved:
            # Show feedback form if requested
            if st.session_state.get("show_design_feedback", False):
                feedback = UIStateManager.show_feedback_form("design")
                if feedback:
                    with st.spinner("🤖 Updating design based on feedback..."):
                        updated_content = workflow.update_design(feedback)
                        SessionStateManager.set_current_content(updated_content)
                    st.session_state["show_design_feedback"] = False
                    st.success("✅ Design updated! Please review the changes.")
                    st.rerun()
            else:
                action = UIStateManager.show_approval_buttons("design")
                
                if action == "approve":
                    workflow.approve_design()
                    st.success("✅ Design approved! Moving to tasks phase...")
                    st.rerun()
                elif action == "changes":
                    st.session_state["show_design_feedback"] = True
                    st.rerun()
        else:
            st.markdown('<div class="status-indicator status-success">✅ Design approved and ready for task generation</div>', unsafe_allow_html=True)


def render_tasks_phase(workflow: SpecWorkflow):
    """Render tasks phase interface."""
    if not workflow.state.tasks_content:
        st.markdown('<div class="status-indicator status-info">✅ Ready to generate implementation tasks</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("✅ Generate Tasks", use_container_width=True, type="primary"):
                with st.spinner("🤖 Generating actionable implementation tasks..."):
                    tasks_content = workflow.create_tasks()
                    SessionStateManager.set_current_content(tasks_content)
                st.rerun()
        
        with col1:
            st.info("💡 The implementation plan will break down your design into discrete, manageable coding tasks with proper hierarchy and dependencies.")
    else:
        UIStateManager.show_document_preview(workflow.state.tasks_content, "Implementation Tasks")
        
        if not workflow.state.tasks_approved:
            # Show feedback form if requested
            if st.session_state.get("show_tasks_feedback", False):
                feedback = UIStateManager.show_feedback_form("tasks")
                if feedback:
                    with st.spinner("🤖 Updating tasks based on feedback..."):
                        updated_content = workflow.update_tasks(feedback)
                        SessionStateManager.set_current_content(updated_content)
                    st.session_state["show_tasks_feedback"] = False
                    st.success("✅ Tasks updated! Please review the changes.")
                    st.rerun()
            else:
                action = UIStateManager.show_approval_buttons("tasks")
                
                if action == "approve":
                    workflow.approve_tasks()
                    st.success("🎉 Tasks approved! Specification workflow complete!")
                    st.rerun()
                elif action == "changes":
                    st.session_state["show_tasks_feedback"] = True
                    st.rerun()
        else:
            st.markdown('<div class="status-indicator status-success">✅ Tasks approved - specification workflow complete!</div>', unsafe_allow_html=True)


def render_complete_phase(workflow: SpecWorkflow):
    """Render completion phase interface."""
    st.markdown('<div class="main-header">🎉 Specification Complete!</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Your comprehensive specification is ready for implementation</div>', unsafe_allow_html=True)
    
    # Success message
    st.markdown('<div class="status-indicator status-success">✅ All documents have been created and approved</div>', unsafe_allow_html=True)
    
    # Show summary cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="document-container">
            <div class="document-header">📋 Requirements</div>
            <div class="document-content">
                <div class="status-indicator status-success">✅ Approved</div>
                <p>User stories and acceptance criteria defined</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="document-container">
            <div class="document-header">🏗️ Design</div>
            <div class="document-content">
                <div class="status-indicator status-success">✅ Approved</div>
                <p>Architecture and technical design completed</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="document-container">
            <div class="document-header">✅ Tasks</div>
            <div class="document-content">
                <div class="status-indicator status-success">✅ Approved</div>
                <p>Implementation plan ready for execution</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Show file locations
    st.markdown("### 📁 Generated Files")
    config = SessionStateManager.get_config()
    base_path = Path(config.working_directory) / ".kiro" / "specs" / workflow.feature_name
    
    st.markdown(f"""
    <div class="document-container">
        <div class="document-header">📂 File Structure</div>
        <div class="document-content">
            <code>
{base_path}<br>
├── requirements.md<br>
├── design.md<br>
└── tasks.md
            </code>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Action buttons
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🚀 Start New Spec", use_container_width=True, type="primary"):
            SessionStateManager.reset_workflow_state()
            st.rerun()
    
    with col1:
        st.info("💡 You can now use the generated tasks to implement your feature, or start working on a new specification.")


def main():
    """Main application entry point."""
    setup_page_config()
    SessionStateManager.initialize_session_state()
    
    render_sidebar()
    render_main_content()


if __name__ == "__main__":
    main()