"""Main Streamlit application for Kiro specification workflow."""
import streamlit as st
import os
from pathlib import Path
from config import ConfigManager, BEDROCK_MODELS
from ai_client import AIClient
from file_manager import FileManager
from workflow import SpecWorkflow, WorkflowPhase
from models import SessionStateManager, UIStateManager, AppConfig


def setup_page_config():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="Kiro Spec Creator",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def render_sidebar():
    """Render sidebar with configuration options."""
    st.sidebar.title("🤖 Kiro Spec Creator")
    st.sidebar.markdown("---")
    
    # Model selection
    st.sidebar.subheader("AI Model Configuration")
    
    # Get available models (may be updated by discovery)
    config_manager = ConfigManager()
    available_models = list(config_manager.get_available_models().keys())
    current_config = SessionStateManager.get_config()
    
    if available_models:
        selected_model = st.sidebar.selectbox(
            "Select AI Model",
            available_models,
            index=available_models.index(current_config.selected_model) if current_config.selected_model in available_models else 0,
            key="model_selector"
        )
        
        # Update config if model changed
        if selected_model != current_config.selected_model:
            SessionStateManager.update_config(selected_model=selected_model)
    else:
        st.sidebar.error("No models configured. Test AWS connection to discover available models.")
        selected_model = current_config.selected_model
    
    # Directory configuration
    st.sidebar.subheader("Project Configuration")
    
    working_directory = st.sidebar.text_input(
        "Working Directory",
        value=current_config.working_directory,
        placeholder="/path/to/your/project",
        help="Directory where .kiro/specs will be created",
        key="directory_input"
    )
    
    # Validate directory
    config_manager = ConfigManager()
    if working_directory:
        if config_manager.validate_directory(working_directory):
            st.sidebar.success("✅ Directory is valid")
            SessionStateManager.update_config(working_directory=working_directory)
            
            # Ensure .kiro structure exists
            file_manager = FileManager(working_directory)
            if file_manager.ensure_kiro_structure():
                st.sidebar.info("📁 .kiro/specs structure ready")
        else:
            st.sidebar.error("❌ Directory does not exist or is not accessible")
    
    # AWS Configuration
    st.sidebar.subheader("AWS Configuration")
    
    # Common Bedrock regions
    bedrock_regions = [
        "us-east-1", "us-west-2", "eu-west-1", "eu-central-1", 
        "ap-southeast-1", "ap-northeast-1"
    ]
    
    if current_config.aws_region in bedrock_regions:
        region_index = bedrock_regions.index(current_config.aws_region)
    else:
        region_index = 0
    
    aws_region = st.sidebar.selectbox(
        "AWS Region",
        bedrock_regions,
        index=region_index,
        help="AWS region for Bedrock service (us-east-1 recommended)"
    )
    
    if aws_region != current_config.aws_region:
        SessionStateManager.update_config(aws_region=aws_region)
    
    # Test AWS connectivity and discover models
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        test_connection = st.button("Test Connection", key="test_conn")
    
    with col2:
        discover_models = st.button("Discover Models", key="discover_models")
    
    if test_connection or discover_models:
        with st.sidebar:
            with st.spinner("Testing connection and discovering models..."):
                try:
                    config_manager = ConfigManager()
                    basic_success, basic_message = config_manager.test_aws_connectivity()
                    
                    if basic_success:
                        st.success(f"✅ {basic_message}")
                        
                        # Test specific model if one is selected
                        if selected_model and not discover_models:
                            ai_client = AIClient(selected_model, aws_region)
                            model_success, model_message = ai_client.test_connection()
                            
                            if model_success:
                                st.success(f"✅ Model test: {model_message}")
                            else:
                                st.error(f"❌ Model test failed: {model_message}")
                        
                        # Refresh the page to show updated models
                        if discover_models:
                            st.rerun()
                            
                    else:
                        st.error(f"❌ AWS connection failed: {basic_message}")
                        
                        # Show setup instructions on failure
                        with st.expander("📋 Setup Instructions"):
                            st.markdown(config_manager.get_setup_instructions())
                        
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")
                    with st.expander("📋 Setup Instructions"):
                        st.markdown(config_manager.get_setup_instructions())
    
    st.sidebar.markdown("---")
    
    # Existing specs
    if working_directory and config_manager.validate_directory(working_directory):
        file_manager = FileManager(working_directory)
        existing_specs = file_manager.list_existing_specs()
        
        if existing_specs:
            st.sidebar.subheader("Existing Specifications")
            for spec in existing_specs:
                req_exists, design_exists, tasks_exists = file_manager.get_spec_status(spec)
                status_icons = ""
                if req_exists:
                    status_icons += "📋"
                if design_exists:
                    status_icons += "🏗️"
                if tasks_exists:
                    status_icons += "✅"
                
                if st.sidebar.button(f"{status_icons} {spec}", key=f"load_{spec}"):
                    SessionStateManager.set_feature_name(spec)
                    # Load existing workflow
                    ai_client = AIClient(selected_model, aws_region)
                    workflow = SpecWorkflow(spec, working_directory, ai_client)
                    workflow.load_existing_spec()
                    SessionStateManager.set_workflow(workflow)
                    st.rerun()


def render_main_content():
    """Render main content area."""
    config = SessionStateManager.get_config()
    
    # Check if configuration is complete
    if not config.working_directory or not config.selected_model:
        st.title("Welcome to Kiro Spec Creator")
        st.markdown("""
        This application helps you create comprehensive feature specifications using Kiro's proven workflow.
        
        **Getting Started:**
        1. Select an AI model from the sidebar (Amazon Nova Pro or Anthropic Claude Sonnet 3.7)
        2. Set your working directory where specifications will be saved
        3. Test your AWS connection to ensure Bedrock access
        4. Start creating a new specification or load an existing one
        
        **Workflow Overview:**
        - **Requirements**: Define user stories and acceptance criteria in EARS format
        - **Design**: Create comprehensive technical design with architecture and components
        - **Tasks**: Generate actionable implementation tasks with proper hierarchy
        """)
        return
    
    current_workflow = SessionStateManager.get_workflow()
    
    if not current_workflow:
        # No active workflow - show new spec creation
        render_new_spec_form()
    else:
        # Active workflow - show workflow interface
        render_workflow_interface(current_workflow)


def render_new_spec_form():
    """Render form for creating new specification."""
    st.title("Create New Specification")
    
    feature_name = st.text_input(
        "Feature Name",
        placeholder="e.g., user-authentication, payment-system",
        help="Use kebab-case format (lowercase with hyphens)",
        key="new_feature_name"
    )
    
    feature_idea = st.text_area(
        "Feature Idea",
        placeholder="Describe your feature idea in detail...",
        height=150,
        help="Provide a comprehensive description of what you want to build",
        key="feature_idea"
    )
    
    if st.button("Start Specification Workflow", disabled=not (feature_name and feature_idea)):
        if feature_name and feature_idea:
            try:
                config = SessionStateManager.get_config()
                ai_client = AIClient(config.selected_model, config.aws_region)
                
                # Create new workflow
                workflow = SpecWorkflow(feature_name, config.working_directory, ai_client)
                SessionStateManager.set_workflow(workflow)
                SessionStateManager.set_feature_name(feature_name)
                
                # Generate initial requirements
                with st.spinner("Generating initial requirements..."):
                    requirements_content = workflow.create_requirements(feature_idea)
                    SessionStateManager.set_current_content(requirements_content)
                
                st.success("Requirements generated! Please review and approve to continue.")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error creating specification: {str(e)}")


def render_workflow_interface(workflow: SpecWorkflow):
    """Render the main workflow interface."""
    st.title(f"Specification: {workflow.feature_name}")
    
    # Show phase indicator
    UIStateManager.show_phase_indicator(workflow.get_current_phase())
    
    st.markdown("---")
    
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
    st.header("📋 Requirements Phase")
    
    if workflow.state.requirements_content:
        UIStateManager.show_document_preview(workflow.state.requirements_content, "Requirements Document")
        
        if not workflow.state.requirements_approved:
            action = UIStateManager.show_approval_buttons("requirements")
            
            if action == "approve":
                workflow.approve_requirements()
                st.success("Requirements approved! Moving to design phase...")
                st.rerun()
            elif action == "changes":
                st.session_state["show_requirements_feedback"] = True
                st.rerun()
        
        # Show feedback form if requested
        if st.session_state.get("show_requirements_feedback", False):
            feedback = UIStateManager.show_feedback_form("requirements")
            if feedback:
                with st.spinner("Updating requirements based on feedback..."):
                    updated_content = workflow.update_requirements(feedback)
                    SessionStateManager.set_current_content(updated_content)
                st.session_state["show_requirements_feedback"] = False
                st.success("Requirements updated! Please review the changes.")
                st.rerun()
    else:
        st.info("No requirements content available. Please start a new specification.")


def render_design_phase(workflow: SpecWorkflow):
    """Render design phase interface."""
    st.header("🏗️ Design Phase")
    
    if not workflow.state.design_content:
        if st.button("Generate Design Document"):
            with st.spinner("Generating design document..."):
                design_content = workflow.create_design()
                SessionStateManager.set_current_content(design_content)
            st.rerun()
    else:
        UIStateManager.show_document_preview(workflow.state.design_content, "Design Document")
        
        if not workflow.state.design_approved:
            action = UIStateManager.show_approval_buttons("design")
            
            if action == "approve":
                workflow.approve_design()
                st.success("Design approved! Moving to tasks phase...")
                st.rerun()
            elif action == "changes":
                st.session_state["show_design_feedback"] = True
                st.rerun()
        
        # Show feedback form if requested
        if st.session_state.get("show_design_feedback", False):
            feedback = UIStateManager.show_feedback_form("design")
            if feedback:
                with st.spinner("Updating design based on feedback..."):
                    updated_content = workflow.update_design(feedback)
                    SessionStateManager.set_current_content(updated_content)
                st.session_state["show_design_feedback"] = False
                st.success("Design updated! Please review the changes.")
                st.rerun()


def render_tasks_phase(workflow: SpecWorkflow):
    """Render tasks phase interface."""
    st.header("✅ Tasks Phase")
    
    if not workflow.state.tasks_content:
        if st.button("Generate Implementation Tasks"):
            with st.spinner("Generating implementation tasks..."):
                tasks_content = workflow.create_tasks()
                SessionStateManager.set_current_content(tasks_content)
            st.rerun()
    else:
        UIStateManager.show_document_preview(workflow.state.tasks_content, "Implementation Tasks")
        
        if not workflow.state.tasks_approved:
            action = UIStateManager.show_approval_buttons("tasks")
            
            if action == "approve":
                workflow.approve_tasks()
                st.success("Tasks approved! Specification workflow complete!")
                st.rerun()
            elif action == "changes":
                st.session_state["show_tasks_feedback"] = True
                st.rerun()
        
        # Show feedback form if requested
        if st.session_state.get("show_tasks_feedback", False):
            feedback = UIStateManager.show_feedback_form("tasks")
            if feedback:
                with st.spinner("Updating tasks based on feedback..."):
                    updated_content = workflow.update_tasks(feedback)
                    SessionStateManager.set_current_content(updated_content)
                st.session_state["show_tasks_feedback"] = False
                st.success("Tasks updated! Please review the changes.")
                st.rerun()


def render_complete_phase(workflow: SpecWorkflow):
    """Render completion phase interface."""
    st.header("🎉 Specification Complete!")
    
    st.success("Your specification workflow is complete! All documents have been created and approved.")
    
    # Show summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📋 Requirements")
        st.info("✅ Approved")
    
    with col2:
        st.subheader("🏗️ Design")
        st.info("✅ Approved")
    
    with col3:
        st.subheader("✅ Tasks")
        st.info("✅ Approved")
    
    # Show file locations
    st.subheader("📁 Generated Files")
    config = SessionStateManager.get_config()
    base_path = Path(config.working_directory) / ".kiro" / "specs" / workflow.feature_name
    
    st.code(f"""
Files saved to: {base_path}
├── requirements.md
├── design.md
└── tasks.md
    """)
    
    # Option to start new spec
    if st.button("Start New Specification"):
        SessionStateManager.reset_workflow_state()
        st.rerun()


def main():
    """Main application entry point."""
    setup_page_config()
    SessionStateManager.initialize_session_state()
    
    render_sidebar()
    render_main_content()


if __name__ == "__main__":
    main()