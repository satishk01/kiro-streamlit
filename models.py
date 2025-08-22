"""Data models and state management for Kiro Streamlit application."""
import streamlit as st
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from enum import Enum
from workflow import WorkflowPhase, SpecificationState


@dataclass
class AppConfig:
    """Application configuration state."""
    selected_model: str = "Anthropic Claude Sonnet 3.7"
    working_directory: str = ""
    aws_region: str = "us-east-1"


class SessionStateManager:
    """Manages Streamlit session state for the application."""
    
    # Session state keys
    CONFIG_KEY = "app_config"
    WORKFLOW_KEY = "current_workflow"
    FEATURE_NAME_KEY = "feature_name"
    CURRENT_CONTENT_KEY = "current_content"
    FEEDBACK_KEY = "user_feedback"
    APPROVAL_STATUS_KEY = "approval_status"
    
    @classmethod
    def initialize_session_state(cls):
        """Initialize session state with default values."""
        if cls.CONFIG_KEY not in st.session_state:
            st.session_state[cls.CONFIG_KEY] = AppConfig()
        
        if cls.WORKFLOW_KEY not in st.session_state:
            st.session_state[cls.WORKFLOW_KEY] = None
        
        if cls.FEATURE_NAME_KEY not in st.session_state:
            st.session_state[cls.FEATURE_NAME_KEY] = ""
        
        if cls.CURRENT_CONTENT_KEY not in st.session_state:
            st.session_state[cls.CURRENT_CONTENT_KEY] = ""
        
        if cls.FEEDBACK_KEY not in st.session_state:
            st.session_state[cls.FEEDBACK_KEY] = ""
        
        if cls.APPROVAL_STATUS_KEY not in st.session_state:
            st.session_state[cls.APPROVAL_STATUS_KEY] = {
                "requirements": False,
                "design": False,
                "tasks": False
            }
    
    @classmethod
    def get_config(cls) -> AppConfig:
        """Get current application configuration."""
        return st.session_state.get(cls.CONFIG_KEY, AppConfig())
    
    @classmethod
    def update_config(cls, **kwargs):
        """Update application configuration."""
        config = cls.get_config()
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        st.session_state[cls.CONFIG_KEY] = config
    
    @classmethod
    def get_workflow(cls):
        """Get current workflow instance."""
        return st.session_state.get(cls.WORKFLOW_KEY)
    
    @classmethod
    def set_workflow(cls, workflow):
        """Set current workflow instance."""
        st.session_state[cls.WORKFLOW_KEY] = workflow
    
    @classmethod
    def get_feature_name(cls) -> str:
        """Get current feature name."""
        return st.session_state.get(cls.FEATURE_NAME_KEY, "")
    
    @classmethod
    def set_feature_name(cls, name: str):
        """Set current feature name."""
        st.session_state[cls.FEATURE_NAME_KEY] = name
    
    @classmethod
    def get_current_content(cls) -> str:
        """Get current document content."""
        return st.session_state.get(cls.CURRENT_CONTENT_KEY, "")
    
    @classmethod
    def set_current_content(cls, content: str):
        """Set current document content."""
        st.session_state[cls.CURRENT_CONTENT_KEY] = content
    
    @classmethod
    def get_feedback(cls) -> str:
        """Get user feedback."""
        return st.session_state.get(cls.FEEDBACK_KEY, "")
    
    @classmethod
    def set_feedback(cls, feedback: str):
        """Set user feedback."""
        st.session_state[cls.FEEDBACK_KEY] = feedback
    
    @classmethod
    def clear_feedback(cls):
        """Clear user feedback."""
        st.session_state[cls.FEEDBACK_KEY] = ""
    
    @classmethod
    def get_approval_status(cls, document_type: str) -> bool:
        """Get approval status for a document type."""
        approval_status = st.session_state.get(cls.APPROVAL_STATUS_KEY, {})
        return approval_status.get(document_type, False)
    
    @classmethod
    def set_approval_status(cls, document_type: str, approved: bool):
        """Set approval status for a document type."""
        if cls.APPROVAL_STATUS_KEY not in st.session_state:
            st.session_state[cls.APPROVAL_STATUS_KEY] = {}
        st.session_state[cls.APPROVAL_STATUS_KEY][document_type] = approved
    
    @classmethod
    def reset_workflow_state(cls):
        """Reset workflow-related session state."""
        st.session_state[cls.WORKFLOW_KEY] = None
        st.session_state[cls.FEATURE_NAME_KEY] = ""
        st.session_state[cls.CURRENT_CONTENT_KEY] = ""
        st.session_state[cls.FEEDBACK_KEY] = ""
        st.session_state[cls.APPROVAL_STATUS_KEY] = {
            "requirements": False,
            "design": False,
            "tasks": False
        }
    
    @classmethod
    def get_workflow_progress(cls) -> Dict[str, bool]:
        """Get overall workflow progress."""
        workflow = cls.get_workflow()
        if not workflow:
            return {"requirements": False, "design": False, "tasks": False}
        
        return {
            "requirements": bool(workflow.state.requirements_content and workflow.state.requirements_approved),
            "design": bool(workflow.state.design_content and workflow.state.design_approved),
            "tasks": bool(workflow.state.tasks_content and workflow.state.tasks_approved)
        }
    
    @classmethod
    def is_workflow_complete(cls) -> bool:
        """Check if current workflow is complete."""
        workflow = cls.get_workflow()
        return workflow.is_complete() if workflow else False


class UIStateManager:
    """Manages UI-specific state and interactions."""
    
    @staticmethod
    def show_phase_indicator(current_phase: WorkflowPhase):
        """Display current workflow phase indicator."""
        phases = [
            ("Requirements", WorkflowPhase.REQUIREMENTS),
            ("Design", WorkflowPhase.DESIGN),
            ("Tasks", WorkflowPhase.TASKS),
            ("Complete", WorkflowPhase.COMPLETE)
        ]
        
        cols = st.columns(len(phases))
        
        for i, (name, phase) in enumerate(phases):
            with cols[i]:
                if phase == current_phase:
                    st.markdown(f"**🔄 {name}**")
                elif phase.value in ["requirements", "design", "tasks"] and current_phase.value in ["design", "tasks", "complete"]:
                    # Show completed phases
                    if (phase == WorkflowPhase.REQUIREMENTS and current_phase != WorkflowPhase.REQUIREMENTS) or \
                       (phase == WorkflowPhase.DESIGN and current_phase in [WorkflowPhase.TASKS, WorkflowPhase.COMPLETE]) or \
                       (phase == WorkflowPhase.TASKS and current_phase == WorkflowPhase.COMPLETE):
                        st.markdown(f"✅ {name}")
                    else:
                        st.markdown(f"⏳ {name}")
                else:
                    st.markdown(f"⏳ {name}")
    
    @staticmethod
    def show_document_preview(content: str, title: str):
        """Display document content with proper formatting."""
        if content:
            st.subheader(title)
            st.markdown(content)
        else:
            st.info(f"No {title.lower()} content available yet.")
    
    @staticmethod
    def show_approval_buttons(document_type: str) -> Optional[str]:
        """Show approval buttons and return user action."""
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(f"✅ Approve {document_type.title()}", key=f"approve_{document_type}"):
                return "approve"
        
        with col2:
            if st.button(f"✏️ Request Changes", key=f"changes_{document_type}"):
                return "changes"
        
        return None
    
    @staticmethod
    def show_feedback_form(document_type: str) -> Optional[str]:
        """Show feedback form and return feedback text."""
        st.subheader(f"Provide Feedback for {document_type.title()}")
        
        feedback = st.text_area(
            "What changes would you like to see?",
            key=f"feedback_{document_type}",
            height=100,
            placeholder="Please describe the changes you'd like to see..."
        )
        
        if st.button("Submit Feedback", key=f"submit_feedback_{document_type}"):
            if feedback.strip():
                return feedback.strip()
            else:
                st.error("Please provide feedback before submitting.")
        
        return None