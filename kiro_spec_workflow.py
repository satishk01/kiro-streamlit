"""Kiro-style specification workflow that follows the exact Kiro process."""
import os
import re
from pathlib import Path
from typing import Optional
from ai_client import AIClient
from kiro_spec_system_prompt import KIRO_SPEC_SYSTEM_PROMPT


class KiroSpecWorkflow:
    """Handles the Kiro specification workflow with user approval at each stage."""
    
    def __init__(self, ai_client: AIClient, working_directory: str):
        """Initialize the Kiro spec workflow."""
        self.ai_client = ai_client
        self.working_directory = Path(working_directory)
        self.current_feature_name = None
        self.current_phase = "requirements"  # requirements, design, tasks, complete
    
    def create_spec_from_idea(self, user_idea: str) -> tuple[str, str]:
        """
        Create a specification from user idea following Kiro workflow.
        Returns (response_message, next_action)
        """
        # Extract feature name
        feature_name = self._extract_feature_name(user_idea)
        self.current_feature_name = feature_name
        
        # Create spec directory
        spec_dir = self.working_directory / ".kiro" / "specs" / feature_name
        spec_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate requirements document
        requirements_content = self._generate_requirements(user_idea, feature_name)
        
        # Save requirements file
        requirements_file = spec_dir / "requirements.md"
        with open(requirements_file, 'w', encoding='utf-8') as f:
            f.write(requirements_content)
        
        response = f"""I've created the initial requirements for **{feature_name}**.

The requirements document has been saved to `.kiro/specs/{feature_name}/requirements.md`

Here's what I've defined:

{requirements_content[:800]}...

The requirements include user stories and acceptance criteria in EARS format. Please review them carefully."""
        
        return response, "requirements-review"
    
    def handle_requirements_feedback(self, feedback: str) -> tuple[str, str]:
        """Handle user feedback on requirements."""
        if not self.current_feature_name:
            return "No active specification found.", "error"
        
        if self._is_approval(feedback):
            # User approved requirements, move to design
            self.current_phase = "design"
            return self._create_design_document()
        else:
            # User wants changes, update requirements
            return self._update_requirements(feedback)
    
    def handle_design_feedback(self, feedback: str) -> tuple[str, str]:
        """Handle user feedback on design."""
        if not self.current_feature_name:
            return "No active specification found.", "error"
        
        if self._is_approval(feedback):
            # User approved design, move to tasks
            self.current_phase = "tasks"
            return self._create_tasks_document()
        else:
            # User wants changes, update design
            return self._update_design(feedback)
    
    def handle_tasks_feedback(self, feedback: str) -> tuple[str, str]:
        """Handle user feedback on tasks."""
        if not self.current_feature_name:
            return "No active specification found.", "error"
        
        if self._is_approval(feedback):
            # User approved tasks, workflow complete
            self.current_phase = "complete"
            return self._complete_workflow()
        else:
            # User wants changes, update tasks
            return self._update_tasks(feedback)
    
    def _extract_feature_name(self, user_idea: str) -> str:
        """Extract feature name from user idea."""
        # Simple extraction - look for common patterns
        patterns = [
            r"spec for (.+?)(?:\.|$)",
            r"specification for (.+?)(?:\.|$)",
            r"create.*?spec.*?for (.+?)(?:\.|$)",
            r"build (.+?)(?:\.|$)",
            r"create (.+?)(?:\.|$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_idea.lower())
            if match:
                feature_name = match.group(1).strip()
                # Clean up the feature name
                feature_name = re.sub(r'[^\w\s-]', '', feature_name)
                feature_name = re.sub(r'\s+', '-', feature_name)
                return feature_name
        
        # Default name if no pattern matches
        return "new-feature"
    
    def _generate_requirements(self, user_idea: str, feature_name: str) -> str:
        """Generate initial requirements document."""
        prompt = f"""Create a comprehensive requirements document for the following feature idea:

**Feature Idea:** {user_idea}
**Feature Name:** {feature_name}

Generate a requirements document following this exact format:

# Requirements Document

## Introduction

[Clear introduction that summarizes the feature and its purpose]

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

[Continue with additional requirements as needed]

Focus on:
- Clear user stories that explain WHO wants WHAT and WHY
- Specific acceptance criteria using EARS format (WHEN/IF...THEN...SHALL)
- Edge cases and error conditions
- User experience considerations
- Technical constraints and requirements

Generate at least 3-5 comprehensive requirements that cover the core functionality."""

        try:
            response = self.ai_client.generate_response(
                prompt=prompt,
                system_prompt=KIRO_SPEC_SYSTEM_PROMPT,
                max_tokens=2000,
                temperature=0.3
            )
            return response
        except Exception as e:
            return f"# Requirements Document\n\nError generating requirements: {str(e)}"
    
    def _create_design_document(self) -> tuple[str, str]:
        """Create design document based on approved requirements."""
        if not self.current_feature_name:
            return "No active specification found.", "error"
        
        # Read requirements
        requirements_file = self.working_directory / ".kiro" / "specs" / self.current_feature_name / "requirements.md"
        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                requirements_content = f.read()
        except FileNotFoundError:
            return "Requirements file not found.", "error"
        
        # Generate design document
        design_content = self._generate_design(requirements_content)
        
        # Save design file
        design_file = self.working_directory / ".kiro" / "specs" / self.current_feature_name / "design.md"
        with open(design_file, 'w', encoding='utf-8') as f:
            f.write(design_content)
        
        response = f"""Great! I've created the design document for **{self.current_feature_name}**.

The design document has been saved to `.kiro/specs/{self.current_feature_name}/design.md`

Here's the design overview:

{design_content[:800]}...

The design includes architecture, components, data models, error handling, and testing strategy based on the approved requirements."""
        
        return response, "design-review"
    
    def _generate_design(self, requirements_content: str) -> str:
        """Generate design document based on requirements."""
        prompt = f"""Based on the following approved requirements, create a comprehensive design document:

**Requirements:**
{requirements_content}

Generate a design document following this exact format:

# Design Document

## Overview

[High-level overview of the feature and its purpose]

## Architecture

[System architecture and high-level design decisions]

## Components and Interfaces

[Detailed breakdown of components, modules, and their interfaces]

## Data Models

[Data structures, database schemas, API contracts]

## Error Handling

[Error handling strategy and error scenarios]

## Testing Strategy

[Approach to testing including unit, integration, and end-to-end tests]

Focus on:
- Technical architecture that addresses all requirements
- Clear component boundaries and interfaces
- Data flow and system interactions
- Scalability and performance considerations
- Security and error handling
- Testing approach for validation

Make design decisions based on the requirements and explain the rationale."""

        try:
            response = self.ai_client.generate_response(
                prompt=prompt,
                system_prompt=KIRO_SPEC_SYSTEM_PROMPT,
                max_tokens=2500,
                temperature=0.3
            )
            return response
        except Exception as e:
            return f"# Design Document\n\nError generating design: {str(e)}"
    
    def _create_tasks_document(self) -> tuple[str, str]:
        """Create tasks document based on approved design."""
        if not self.current_feature_name:
            return "No active specification found.", "error"
        
        # Read requirements and design
        spec_dir = self.working_directory / ".kiro" / "specs" / self.current_feature_name
        
        try:
            with open(spec_dir / "requirements.md", 'r', encoding='utf-8') as f:
                requirements_content = f.read()
            with open(spec_dir / "design.md", 'r', encoding='utf-8') as f:
                design_content = f.read()
        except FileNotFoundError as e:
            return f"Required file not found: {e}", "error"
        
        # Generate tasks document
        tasks_content = self._generate_tasks(requirements_content, design_content)
        
        # Save tasks file
        tasks_file = spec_dir / "tasks.md"
        with open(tasks_file, 'w', encoding='utf-8') as f:
            f.write(tasks_content)
        
        response = f"""Perfect! I've created the implementation plan for **{self.current_feature_name}**.

The tasks document has been saved to `.kiro/specs/{self.current_feature_name}/tasks.md`

Here's the implementation plan:

{tasks_content[:800]}...

The plan includes discrete, manageable coding tasks that build incrementally and reference specific requirements."""
        
        return response, "tasks-review"
    
    def _generate_tasks(self, requirements_content: str, design_content: str) -> str:
        """Generate tasks document based on requirements and design."""
        prompt = f"""Based on the approved requirements and design, create an implementation plan with coding tasks:

**Requirements:**
{requirements_content[:1000]}...

**Design:**
{design_content[:1000]}...

Convert the feature design into a series of prompts for a code-generation LLM that will implement each step in a test-driven manner. Prioritize best practices, incremental progress, and early testing, ensuring no big jumps in complexity at any stage. Make sure that each prompt builds on the previous prompts, and ends with wiring things together. There should be no hanging or orphaned code that isn't integrated into a previous step. Focus ONLY on tasks that involve writing, modifying, or testing code.

Format as a numbered checkbox list with maximum two levels of hierarchy:

# Implementation Plan

- [ ] 1. Set up project structure and core interfaces
  - Create directory structure for models, services, repositories, and API components
  - Define interfaces that establish system boundaries
  - _Requirements: 1.1_

- [ ] 2. Implement data models and validation
- [ ] 2.1 Create core data model interfaces and types
  - Write TypeScript interfaces for all data models
  - Implement validation functions for data integrity
  - _Requirements: 2.1, 3.3, 1.2_

- [ ] 2.2 Implement User model with validation
  - Write User class with validation methods
  - Create unit tests for User model validation
  - _Requirements: 1.2_

[Continue with additional coding tasks...]

Each task must:
- Involve writing, modifying, or testing specific code components
- Specify what files or components need to be created or modified
- Be concrete enough for a coding agent to execute
- Reference specific requirements from the requirements document
- Build incrementally on previous tasks

Do NOT include:
- User testing or feedback gathering
- Deployment tasks
- Performance metrics gathering
- Documentation creation
- Business process changes"""

        try:
            response = self.ai_client.generate_response(
                prompt=prompt,
                system_prompt=KIRO_SPEC_SYSTEM_PROMPT,
                max_tokens=3000,
                temperature=0.3
            )
            return response
        except Exception as e:
            return f"# Implementation Plan\n\nError generating tasks: {str(e)}"
    
    def _complete_workflow(self) -> tuple[str, str]:
        """Complete the specification workflow."""
        response = f"""🎉 Specification workflow complete for **{self.current_feature_name}**!

All three documents have been created and approved:

📋 **Requirements** - User stories and acceptance criteria
🏗️ **Design** - Architecture and technical specifications  
✅ **Tasks** - Implementation plan with coding tasks

**Files created:**
- `.kiro/specs/{self.current_feature_name}/requirements.md`
- `.kiro/specs/{self.current_feature_name}/design.md`
- `.kiro/specs/{self.current_feature_name}/tasks.md`

**Next steps:**
You can now begin executing tasks by opening the tasks.md file and clicking "Start task" next to task items, or ask me to "Execute task 1" to begin implementation.

The specification is ready for development!"""
        
        return response, "complete"
    
    def _update_requirements(self, feedback: str) -> tuple[str, str]:
        """Update requirements based on user feedback."""
        # Read current requirements
        requirements_file = self.working_directory / ".kiro" / "specs" / self.current_feature_name / "requirements.md"
        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                current_requirements = f.read()
        except FileNotFoundError:
            return "Requirements file not found.", "error"
        
        # Generate updated requirements
        prompt = f"""Update the following requirements document based on user feedback:

**Current Requirements:**
{current_requirements}

**User Feedback:**
{feedback}

Please modify the requirements document to address the user's feedback while maintaining the same format and structure. Keep all the good parts and only change what the user requested."""

        try:
            updated_requirements = self.ai_client.generate_response(
                prompt=prompt,
                system_prompt=KIRO_SPEC_SYSTEM_PROMPT,
                max_tokens=2000,
                temperature=0.3
            )
            
            # Save updated requirements
            with open(requirements_file, 'w', encoding='utf-8') as f:
                f.write(updated_requirements)
            
            response = f"""I've updated the requirements based on your feedback.

Here are the revised requirements:

{updated_requirements[:800]}...

Please review the changes. Do the requirements look good now?"""
            
            return response, "requirements-review"
            
        except Exception as e:
            return f"Error updating requirements: {str(e)}", "error"
    
    def _update_design(self, feedback: str) -> tuple[str, str]:
        """Update design based on user feedback."""
        # Similar implementation to _update_requirements but for design
        design_file = self.working_directory / ".kiro" / "specs" / self.current_feature_name / "design.md"
        try:
            with open(design_file, 'r', encoding='utf-8') as f:
                current_design = f.read()
        except FileNotFoundError:
            return "Design file not found.", "error"
        
        prompt = f"""Update the following design document based on user feedback:

**Current Design:**
{current_design}

**User Feedback:**
{feedback}

Please modify the design document to address the user's feedback while maintaining the same format and structure."""

        try:
            updated_design = self.ai_client.generate_response(
                prompt=prompt,
                system_prompt=KIRO_SPEC_SYSTEM_PROMPT,
                max_tokens=2500,
                temperature=0.3
            )
            
            with open(design_file, 'w', encoding='utf-8') as f:
                f.write(updated_design)
            
            response = f"""I've updated the design based on your feedback.

Here's the revised design:

{updated_design[:800]}...

Please review the changes. Does the design look good now?"""
            
            return response, "design-review"
            
        except Exception as e:
            return f"Error updating design: {str(e)}", "error"
    
    def _update_tasks(self, feedback: str) -> tuple[str, str]:
        """Update tasks based on user feedback."""
        # Similar implementation for tasks
        tasks_file = self.working_directory / ".kiro" / "specs" / self.current_feature_name / "tasks.md"
        try:
            with open(tasks_file, 'r', encoding='utf-8') as f:
                current_tasks = f.read()
        except FileNotFoundError:
            return "Tasks file not found.", "error"
        
        prompt = f"""Update the following implementation plan based on user feedback:

**Current Tasks:**
{current_tasks}

**User Feedback:**
{feedback}

Please modify the tasks document to address the user's feedback while maintaining the checkbox format and structure."""

        try:
            updated_tasks = self.ai_client.generate_response(
                prompt=prompt,
                system_prompt=KIRO_SPEC_SYSTEM_PROMPT,
                max_tokens=3000,
                temperature=0.3
            )
            
            with open(tasks_file, 'w', encoding='utf-8') as f:
                f.write(updated_tasks)
            
            response = f"""I've updated the implementation plan based on your feedback.

Here's the revised plan:

{updated_tasks[:800]}...

Please review the changes. Do the tasks look good now?"""
            
            return response, "tasks-review"
            
        except Exception as e:
            return f"Error updating tasks: {str(e)}", "error"
    
    def _is_approval(self, feedback: str) -> bool:
        """Check if user feedback is an approval."""
        approval_words = [
            "yes", "approved", "looks good", "good", "ok", "okay", 
            "approve", "accept", "fine", "great", "perfect", "correct",
            "move on", "continue", "next", "proceed"
        ]
        
        feedback_lower = feedback.lower().strip()
        
        # Direct approval words
        if any(word in feedback_lower for word in approval_words):
            return True
        
        # Short positive responses
        if feedback_lower in ["y", "👍", "✅", "sure", "yep", "yeah"]:
            return True
        
        return False
    
    def get_current_phase(self) -> str:
        """Get the current workflow phase."""
        return self.current_phase
    
    def get_feature_name(self) -> Optional[str]:
        """Get the current feature name."""
        return self.current_feature_name