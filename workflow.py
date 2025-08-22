"""Workflow engine for Kiro specification creation process."""
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
from ai_client import AIClient
from file_manager import FileManager


class WorkflowPhase(Enum):
    """Workflow phases for specification creation."""
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    TASKS = "tasks"
    COMPLETE = "complete"


@dataclass
class SpecificationState:
    """State management for specification workflow."""
    feature_name: str
    current_phase: WorkflowPhase
    working_directory: str
    requirements_content: str = ""
    design_content: str = ""
    tasks_content: str = ""
    requirements_approved: bool = False
    design_approved: bool = False
    tasks_approved: bool = False


class SpecWorkflow:
    """Manages the three-phase specification creation workflow."""
    
    def __init__(self, feature_name: str, working_dir: str, ai_client: AIClient):
        self.feature_name = feature_name
        self.working_dir = working_dir
        self.ai_client = ai_client
        self.file_manager = FileManager(working_dir)
        self.state = SpecificationState(
            feature_name=feature_name,
            current_phase=WorkflowPhase.REQUIREMENTS,
            working_directory=working_dir
        )
        
        # Ensure directory structure exists
        self.file_manager.ensure_kiro_structure()
        self.file_manager.create_spec_directory(feature_name)
    
    def create_requirements(self, feature_idea: str) -> str:
        """Generate initial requirements document based on feature idea."""
        if self.state.current_phase != WorkflowPhase.REQUIREMENTS:
            raise ValueError("Must be in requirements phase to create requirements")
        
        requirements_prompt = f"""
        Create a requirements document for the following feature idea: {feature_idea}

        Generate an initial set of requirements in EARS format. The document should include:
        
        1. A clear introduction section that summarizes the feature
        2. A hierarchical numbered list of requirements where each contains:
           - A user story in the format "As a [role], I want [feature], so that [benefit]"
           - A numbered list of acceptance criteria in EARS format (Easy Approach to Requirements Syntax)
        
        Use this exact format:
        
        # Requirements Document
        
        ## Introduction
        [Introduction text here]
        
        ## Requirements
        
        ### Requirement 1
        **User Story:** As a [role], I want [feature], so that [benefit]
        
        #### Acceptance Criteria
        1. WHEN [event] THEN [system] SHALL [response]
        2. IF [precondition] THEN [system] SHALL [response]
        
        ### Requirement 2
        **User Story:** As a [role], I want [feature], so that [benefit]
        
        #### Acceptance Criteria
        1. WHEN [event] THEN [system] SHALL [response]
        2. WHEN [event] AND [condition] THEN [system] SHALL [response]
        
        Consider edge cases, user experience, technical constraints, and success criteria.
        """
        
        content = self.ai_client.generate_content(requirements_prompt)
        self.state.requirements_content = content
        
        # Save to file
        self.file_manager.save_document(self.feature_name, "requirements", content)
        
        return content
    
    def update_requirements(self, feedback: str) -> str:
        """Update requirements based on user feedback."""
        if not self.state.requirements_content:
            raise ValueError("No requirements content to update")
        
        # Create backup before modification
        self.file_manager.backup_document(self.feature_name, "requirements")
        
        updated_content = self.ai_client.process_feedback(
            self.state.requirements_content, 
            feedback
        )
        
        self.state.requirements_content = updated_content
        self.file_manager.save_document(self.feature_name, "requirements", updated_content)
        
        return updated_content
    
    def approve_requirements(self) -> bool:
        """Mark requirements as approved and advance to design phase."""
        if not self.state.requirements_content:
            return False
        
        self.state.requirements_approved = True
        self.state.current_phase = WorkflowPhase.DESIGN
        return True
    
    def create_design(self) -> str:
        """Generate design document based on approved requirements."""
        if self.state.current_phase != WorkflowPhase.DESIGN:
            raise ValueError("Must be in design phase to create design")
        
        if not self.state.requirements_approved:
            raise ValueError("Requirements must be approved before creating design")
        
        design_prompt = f"""
        Based on the following approved requirements, create a comprehensive design document:
        
        {self.state.requirements_content}
        
        The design document must include these sections:
        1. Overview
        2. Architecture  
        3. Components and Interfaces
        4. Data Models
        5. Error Handling
        6. Testing Strategy
        
        Include diagrams using Mermaid syntax where appropriate. Ensure the design addresses all requirements and highlight key design decisions with rationales.
        """
        
        content = self.ai_client.generate_content(design_prompt)
        self.state.design_content = content
        
        # Save to file
        self.file_manager.save_document(self.feature_name, "design", content)
        
        return content
    
    def update_design(self, feedback: str) -> str:
        """Update design based on user feedback."""
        if not self.state.design_content:
            raise ValueError("No design content to update")
        
        # Create backup before modification
        self.file_manager.backup_document(self.feature_name, "design")
        
        updated_content = self.ai_client.process_feedback(
            self.state.design_content, 
            feedback
        )
        
        self.state.design_content = updated_content
        self.file_manager.save_document(self.feature_name, "design", updated_content)
        
        return updated_content
    
    def approve_design(self) -> bool:
        """Mark design as approved and advance to tasks phase."""
        if not self.state.design_content:
            return False
        
        self.state.design_approved = True
        self.state.current_phase = WorkflowPhase.TASKS
        return True
    
    def create_tasks(self) -> str:
        """Generate implementation tasks based on approved design."""
        if self.state.current_phase != WorkflowPhase.TASKS:
            raise ValueError("Must be in tasks phase to create tasks")
        
        if not self.state.design_approved:
            raise ValueError("Design must be approved before creating tasks")
        
        tasks_prompt = f"""
        Convert the following feature design into a series of implementation tasks:
        
        Requirements:
        {self.state.requirements_content}
        
        Design:
        {self.state.design_content}
        
        Create an actionable implementation plan with these constraints:
        - Format as numbered checkbox list with maximum two levels of hierarchy
        - Each task must involve writing, modifying, or testing code
        - Include specific requirement references for each task
        - Build incrementally with test-driven development
        - Focus ONLY on coding tasks (no deployment, user testing, etc.)
        
        Use this format:
        # Implementation Plan
        
        - [ ] 1. Task description
          - Additional details
          - _Requirements: X.X_
        
        - [ ] 2. Another task
        - [ ] 2.1 Sub-task
          - Sub-task details  
          - _Requirements: Y.Y_
        """
        
        content = self.ai_client.generate_content(tasks_prompt)
        self.state.tasks_content = content
        
        # Save to file
        self.file_manager.save_document(self.feature_name, "tasks", content)
        
        return content
    
    def update_tasks(self, feedback: str) -> str:
        """Update tasks based on user feedback."""
        if not self.state.tasks_content:
            raise ValueError("No tasks content to update")
        
        # Create backup before modification
        self.file_manager.backup_document(self.feature_name, "tasks")
        
        updated_content = self.ai_client.process_feedback(
            self.state.tasks_content, 
            feedback
        )
        
        self.state.tasks_content = updated_content
        self.file_manager.save_document(self.feature_name, "tasks", updated_content)
        
        return updated_content
    
    def approve_tasks(self) -> bool:
        """Mark tasks as approved and complete the workflow."""
        if not self.state.tasks_content:
            return False
        
        self.state.tasks_approved = True
        self.state.current_phase = WorkflowPhase.COMPLETE
        return True
    
    def get_current_phase(self) -> WorkflowPhase:
        """Get current workflow phase."""
        return self.state.current_phase
    
    def get_phase_name(self) -> str:
        """Get human-readable current phase name."""
        return self.state.current_phase.value.title()
    
    def can_advance_phase(self) -> bool:
        """Check if workflow can advance to next phase."""
        if self.state.current_phase == WorkflowPhase.REQUIREMENTS:
            return bool(self.state.requirements_content)
        elif self.state.current_phase == WorkflowPhase.DESIGN:
            return self.state.requirements_approved and bool(self.state.design_content)
        elif self.state.current_phase == WorkflowPhase.TASKS:
            return self.state.design_approved and bool(self.state.tasks_content)
        return False
    
    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return (self.state.current_phase == WorkflowPhase.COMPLETE and 
                self.state.requirements_approved and 
                self.state.design_approved and 
                self.state.tasks_approved)
    
    def load_existing_spec(self) -> bool:
        """Load existing specification from files if available."""
        try:
            # Load existing documents
            requirements = self.file_manager.load_document(self.feature_name, "requirements")
            design = self.file_manager.load_document(self.feature_name, "design")
            tasks = self.file_manager.load_document(self.feature_name, "tasks")
            
            if requirements:
                self.state.requirements_content = requirements
                self.state.requirements_approved = True
            
            if design:
                self.state.design_content = design
                self.state.design_approved = True
            
            if tasks:
                self.state.tasks_content = tasks
                self.state.tasks_approved = True
            
            # Determine current phase based on what exists
            if tasks:
                self.state.current_phase = WorkflowPhase.COMPLETE
            elif design:
                self.state.current_phase = WorkflowPhase.TASKS
            elif requirements:
                self.state.current_phase = WorkflowPhase.DESIGN
            else:
                self.state.current_phase = WorkflowPhase.REQUIREMENTS
            
            return True
            
        except Exception as e:
            print(f"Error loading existing spec: {str(e)}")
            return False