"""Task execution system for Kiro-like behavior."""
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from ai_client import AIClient
from workflow import SpecWorkflow
from vibe_coding import VibeCoding
from kiro_system_prompt import KIRO_SYSTEM_PROMPT


@dataclass
class Task:
    """Represents a task from a specification."""
    id: str
    title: str
    description: str
    category: str
    priority: str
    estimated_hours: Optional[float] = None
    dependencies: List[str] = None
    status: str = "pending"
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class TaskExecutor:
    """Handles task execution and Jira integration like real Kiro."""
    
    def __init__(self, ai_client: AIClient, working_directory: str):
        """Initialize task executor."""
        self.ai_client = ai_client
        self.working_directory = Path(working_directory)
        self.vibe_coding = VibeCoding(ai_client, working_directory)
    
    def parse_tasks_from_spec(self, spec_name: str) -> List[Task]:
        """Parse tasks from a specification's tasks.md file."""
        tasks_file = self.working_directory / ".kiro" / "specs" / spec_name / "tasks.md"
        
        if not tasks_file.exists():
            return []
        
        try:
            with open(tasks_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self._extract_tasks_from_markdown(content)
            
        except Exception as e:
            print(f"Error parsing tasks: {e}")
            return []
    
    def _extract_tasks_from_markdown(self, content: str) -> List[Task]:
        """Extract structured tasks from markdown content."""
        tasks = []
        lines = content.split('\n')
        
        current_task = None
        current_description = []
        task_counter = 1
        
        for line in lines:
            original_line = line
            line = line.strip()
            
            # Look for checkbox tasks (- [ ] or - [x]) with task numbers
            checkbox_match = re.match(r'^-\s*\[[\sx]\]\s*(\d+\.\s*.+)', line)
            if checkbox_match:
                # Save previous task if exists
                if current_task:
                    current_task.description = '\n'.join(current_description).strip()
                    tasks.append(current_task)
                
                title = checkbox_match.group(1).strip()
                
                # Extract status from checkbox
                status = "completed" if "[x]" in original_line else "pending"
                
                # Create new task
                current_task = Task(
                    id=f"task-{task_counter}",
                    title=title,
                    description="",
                    category=self._determine_category(title),
                    priority=self._determine_priority(title),
                    status=status
                )
                current_description = []
                task_counter += 1
            
            elif current_task and line and not line.startswith('#'):
                # Add to current task description
                # Include indented content and bullet points as part of description
                if line.startswith('  ') or line.startswith('-') or line.startswith('*'):
                    current_description.append(line)
                elif line and not line.startswith('- ['):  # Don't include other tasks
                    current_description.append(line)
        
        # Don't forget the last task
        if current_task:
            current_task.description = '\n'.join(current_description).strip()
            tasks.append(current_task)
        
        return tasks
    
    def _determine_category(self, title: str) -> str:
        """Determine task category based on title."""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['api', 'endpoint', 'service', 'backend', 'server']):
            return "Backend"
        elif any(word in title_lower for word in ['ui', 'frontend', 'component', 'interface', 'react', 'vue']):
            return "Frontend"
        elif any(word in title_lower for word in ['database', 'db', 'schema', 'migration', 'sql']):
            return "Database"
        elif any(word in title_lower for word in ['test', 'testing', 'unit', 'integration', 'spec']):
            return "Testing"
        elif any(word in title_lower for word in ['deploy', 'deployment', 'devops', 'ci/cd', 'docker']):
            return "DevOps"
        elif any(word in title_lower for word in ['doc', 'documentation', 'readme', 'guide']):
            return "Documentation"
        else:
            return "Development"
    
    def _determine_priority(self, title: str) -> str:
        """Determine task priority based on title and content."""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['critical', 'urgent', 'security', 'auth', 'core']):
            return "High"
        elif any(word in title_lower for word in ['setup', 'config', 'main', 'implement', 'create']):
            return "Medium"
        elif any(word in title_lower for word in ['test', 'doc', 'cleanup', 'refactor', 'optimize']):
            return "Low"
        else:
            return "Medium"
    
    def execute_task(self, task_id: str, spec_name: str) -> str:
        """Execute a specific task from a specification."""
        tasks = self.parse_tasks_from_spec(spec_name)
        
        # Find the task
        task = None
        for t in tasks:
            if t.id == task_id or task_id.lower() in t.title.lower():
                task = t
                break
        
        if not task:
            return f"Task '{task_id}' not found in specification '{spec_name}'. Available tasks: {[t.title for t in tasks[:5]]}"
        
        # Get spec context
        spec_context = self._get_spec_context(spec_name)
        
        # Create execution prompt
        execution_prompt = f"""I need to implement this task from the {spec_name} specification:

**Task**: {task.title}
**Description**: {task.description}
**Category**: {task.category}
**Priority**: {task.priority}

**Specification Context**:
{spec_context}

**Current Project Structure**:
{self.vibe_coding.get_project_context()}

Please implement this task by:
1. Creating or modifying the necessary files
2. Writing the required code
3. Following best practices and the existing project structure
4. Providing clear explanations of what you're doing

Use the FILE_CREATE, FILE_MODIFY, and SHELL_COMMAND patterns to specify the operations needed."""
        
        # Use vibe coding to implement the task
        result = self.vibe_coding.process_vibe_request(execution_prompt)
        
        if result.success:
            # Execute the file operations
            if result.file_operations:
                success, errors = self.vibe_coding.execute_file_operations(result.file_operations)
                
                if success:
                    # Mark task as completed
                    self._mark_task_completed(task_id, spec_name)
                    
                    operation_summary = "\n".join([f"✅ {op.operation.title()}: `{op.file_path}`" for op in result.file_operations])
                    
                    response = f"**Task Completed**: {task.title}\n\n{result.response}\n\n**Files Modified**:\n{operation_summary}"
                    
                    if result.shell_commands:
                        commands = "\n".join([f"```bash\n{cmd}\n```" for cmd in result.shell_commands])
                        response += f"\n\n**Next Steps - Run These Commands**:\n{commands}"
                    
                    return response
                else:
                    return f"Task implementation generated but file operations failed:\n{result.response}\n\nErrors: {errors}"
            else:
                return f"Task analysis completed:\n{result.response}\n\nNo file operations were needed for this task."
        else:
            return f"Failed to implement task: {result.error_message}"
    
    def _get_spec_context(self, spec_name: str) -> str:
        """Get context from all specification files."""
        spec_dir = self.working_directory / ".kiro" / "specs" / spec_name
        context = ""
        
        for file_name in ["requirements.md", "design.md", "tasks.md"]:
            file_path = spec_dir / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    context += f"\n\n## {file_name}\n{content[:1000]}..." if len(content) > 1000 else f"\n\n## {file_name}\n{content}"
                except Exception:
                    pass
        
        return context
    
    def _mark_task_completed(self, task_id: str, spec_name: str):
        """Mark a task as completed in the tasks file."""
        tasks_file = self.working_directory / ".kiro" / "specs" / spec_name / "tasks.md"
        
        if not tasks_file.exists():
            return
        
        try:
            with open(tasks_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add completion marker
            completion_marker = f"\n\n<!-- TASK_COMPLETED: {task_id} at {self._get_timestamp()} -->"
            
            with open(tasks_file, 'w', encoding='utf-8') as f:
                f.write(content + completion_marker)
                
        except Exception as e:
            print(f"Error marking task completed: {e}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def create_jira_tickets(self, spec_name: str) -> str:
        """Create properly formatted Jira tickets from specification tasks."""
        tasks = self.parse_tasks_from_spec(spec_name)
        
        if not tasks:
            return f"No tasks found in specification '{spec_name}' to create Jira tickets from."
        
        # Get spec context for better ticket descriptions
        spec_context = self._get_spec_context(spec_name)
        
        # Generate proper Jira tickets using AI
        jira_prompt = f"""Based on the {spec_name} specification and its tasks, create professional Jira tickets in proper format.

**Specification Context:**
{spec_context[:2000]}...

**Tasks to Convert:**
"""
        
        for i, task in enumerate(tasks, 1):
            jira_prompt += f"\n{i}. **{task.title}**\n   Category: {task.category}\n   Priority: {task.priority}\n   Description: {task.description}\n"
        
        jira_prompt += """

Create Jira tickets with this EXACT format for each task:

---
**TICKET #{number}**

**Summary:** [Clear, actionable title under 100 characters]

**Issue Type:** Story/Task/Bug

**Priority:** High/Medium/Low

**Description:**
[Detailed description with context and acceptance criteria]

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

**Story Points:** [1, 2, 3, 5, 8, 13]

**Labels:** [comma-separated tags like: backend, api, authentication]

**Components:** [system components affected]

**Epic Link:** {spec_name}

---

Make each ticket:
1. Self-contained and actionable
2. Include clear acceptance criteria
3. Reference the overall specification context
4. Use proper Jira formatting
5. Include realistic story point estimates
6. Add relevant labels and components

Generate professional, ready-to-import Jira tickets."""
        
        try:
            response = self.ai_client.generate_response(
                prompt=jira_prompt,
                system_prompt=KIRO_SYSTEM_PROMPT,
                max_tokens=3000,
                temperature=0.3
            )
            
            return f"**🎫 Jira Tickets for {spec_name} Specification**\n\n{response}\n\n---\n\n**📋 Import Instructions:**\n1. Copy each ticket section above\n2. Create new tickets in your Jira project\n3. Use the Epic Link '{spec_name}' to group them\n4. Adjust story points and assignments as needed\n\n**💡 Tip:** You can also use Jira's CSV import feature with this data."
            
        except Exception as e:
            return f"Error generating Jira tickets: {str(e)}"
    
    def list_available_tasks(self, spec_name: str) -> str:
        """List all available tasks from a specification."""
        tasks = self.parse_tasks_from_spec(spec_name)
        
        if not tasks:
            return f"No tasks found in specification '{spec_name}'."
        
        task_list = f"**📋 Available Tasks in {spec_name}**:\n\n"
        
        for i, task in enumerate(tasks, 1):
            status_icon = "✅" if task.status == "completed" else "⏳"
            task_list += f"{i}. {status_icon} **{task.title}** ({task.category}, {task.priority})\n"
            if task.description:
                task_list += f"   {task.description[:100]}...\n\n"
            else:
                task_list += "\n"
        
        task_list += "\n**🚀 To execute a task:**\n- \"Execute task [number]\" or \"Implement [task name]\"\n- \"What's next?\" for recommendations"
        
        return task_list
    
    def get_next_task(self, spec_name: str) -> str:
        """Get the next recommended task to work on."""
        tasks = self.parse_tasks_from_spec(spec_name)
        
        if not tasks:
            return f"No tasks found in specification '{spec_name}'."
        
        # Find first incomplete high priority task
        for task in tasks:
            if task.status != "completed" and task.priority == "High":
                return f"**🎯 Next Recommended Task**: {task.title}\n\n**Description**: {task.description}\n\n**Category**: {task.category}\n**Priority**: {task.priority}\n\n💡 Say 'Execute this task' or 'Implement {task.title}' to start working on it."
        
        # If no high priority, find first incomplete task
        for task in tasks:
            if task.status != "completed":
                return f"**📝 Next Task**: {task.title}\n\n**Description**: {task.description}\n\n**Category**: {task.category}\n**Priority**: {task.priority}\n\n💡 Say 'Execute this task' or 'Implement {task.title}' to start working on it."
        
        return f"🎉 All tasks in '{spec_name}' appear to be completed! Great work!"