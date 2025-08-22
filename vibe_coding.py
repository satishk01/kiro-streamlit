"""Vibe coding functionality for Kiro - file operations and code generation."""
import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from ai_client import AIClient
from kiro_system_prompt import KIRO_SYSTEM_PROMPT


@dataclass
class FileOperation:
    """Represents a file operation to be performed."""
    operation: str  # 'create', 'modify', 'delete', 'read'
    file_path: str
    content: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    backup: bool = True


@dataclass
class CodeGenerationResult:
    """Result of code generation with file operations."""
    response: str
    file_operations: List[FileOperation]
    shell_commands: List[str]
    success: bool
    error_message: Optional[str] = None


class VibeCoding:
    """Handles vibe coding functionality - file operations and code generation."""
    
    def __init__(self, ai_client: AIClient, working_directory: str):
        """Initialize vibe coding with AI client and working directory."""
        self.ai_client = ai_client
        self.working_directory = Path(working_directory)
        self.backup_dir = self.working_directory / ".kiro" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def process_vibe_request(self, user_request: str, context_files: List[str] = None) -> CodeGenerationResult:
        """
        Process a vibe coding request and generate code/file operations.
        
        Args:
            user_request: The user's request for code generation or file operations
            context_files: List of file paths to include as context
            
        Returns:
            CodeGenerationResult with response and operations to perform
        """
        try:
            # Build context from files
            context = self._build_file_context(context_files or [])
            
            # Create enhanced prompt for vibe coding
            vibe_prompt = self._create_vibe_prompt(user_request, context)
            
            # Generate response using Kiro system prompt
            response = self.ai_client.generate_response(
                prompt=vibe_prompt,
                system_prompt=KIRO_SYSTEM_PROMPT,
                max_tokens=1500,
                temperature=0.3  # Lower temperature for more consistent code generation
            )
            
            # Parse response for file operations and commands
            file_operations, shell_commands = self._parse_response_for_operations(response)
            
            return CodeGenerationResult(
                response=response,
                file_operations=file_operations,
                shell_commands=shell_commands,
                success=True
            )
            
        except Exception as e:
            return CodeGenerationResult(
                response=f"Error processing vibe request: {str(e)}",
                file_operations=[],
                shell_commands=[],
                success=False,
                error_message=str(e)
            )
    
    def execute_file_operations(self, operations: List[FileOperation]) -> Tuple[bool, List[str]]:
        """
        Execute a list of file operations.
        
        Args:
            operations: List of FileOperation objects to execute
            
        Returns:
            Tuple of (success, error_messages)
        """
        errors = []
        
        for operation in operations:
            try:
                if operation.operation == "create":
                    self._create_file(operation)
                elif operation.operation == "modify":
                    self._modify_file(operation)
                elif operation.operation == "delete":
                    self._delete_file(operation)
                elif operation.operation == "read":
                    # Read operations don't modify files
                    continue
                else:
                    errors.append(f"Unknown operation: {operation.operation}")
                    
            except Exception as e:
                errors.append(f"Error executing {operation.operation} on {operation.file_path}: {str(e)}")
        
        return len(errors) == 0, errors
    
    def _build_file_context(self, file_paths: List[str]) -> str:
        """Build context string from file contents."""
        context = ""
        
        for file_path in file_paths:
            try:
                full_path = self.working_directory / file_path
                if full_path.exists() and full_path.is_file():
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    context += f"\n\n## File: {file_path}\n```\n{content}\n```"
                    
            except Exception as e:
                context += f"\n\n## File: {file_path}\n[Error reading file: {str(e)}]"
        
        return context
    
    def _create_vibe_prompt(self, user_request: str, context: str) -> str:
        """Create enhanced prompt for vibe coding."""
        prompt = f"""I need help with the following request:

{user_request}

Current working directory: {self.working_directory}

"""
        
        if context:
            prompt += f"Here are the relevant files for context:{context}\n\n"
        
        prompt += """Please provide a solution that includes:
1. Clear explanation of what you're doing
2. Any code that needs to be written
3. File operations needed (create, modify, delete)
4. Shell commands to run (if any)

Format file operations clearly using this pattern:
FILE_CREATE: path/to/file.py
FILE_MODIFY: path/to/existing_file.py (lines X-Y)
FILE_DELETE: path/to/file.py
SHELL_COMMAND: command to run

Focus on minimal, working solutions that follow best practices."""
        
        return prompt
    
    def _parse_response_for_operations(self, response: str) -> Tuple[List[FileOperation], List[str]]:
        """Parse AI response for file operations and shell commands."""
        file_operations = []
        shell_commands = []
        
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Parse file operations
            if line.startswith('FILE_CREATE:'):
                file_path = line.replace('FILE_CREATE:', '').strip()
                # Look for code blocks after this line
                content = self._extract_code_for_file(response, file_path)
                file_operations.append(FileOperation(
                    operation='create',
                    file_path=file_path,
                    content=content
                ))
            
            elif line.startswith('FILE_MODIFY:'):
                parts = line.replace('FILE_MODIFY:', '').strip()
                # Parse file path and optional line range
                file_path, line_range = self._parse_modify_instruction(parts)
                content = self._extract_code_for_file(response, file_path)
                
                operation = FileOperation(
                    operation='modify',
                    file_path=file_path,
                    content=content
                )
                
                if line_range:
                    operation.line_start, operation.line_end = line_range
                
                file_operations.append(operation)
            
            elif line.startswith('FILE_DELETE:'):
                file_path = line.replace('FILE_DELETE:', '').strip()
                file_operations.append(FileOperation(
                    operation='delete',
                    file_path=file_path
                ))
            
            elif line.startswith('SHELL_COMMAND:'):
                command = line.replace('SHELL_COMMAND:', '').strip()
                shell_commands.append(command)
        
        return file_operations, shell_commands
    
    def _extract_code_for_file(self, response: str, file_path: str) -> str:
        """Extract code content for a specific file from the response."""
        # Look for code blocks near the file path mention
        lines = response.split('\n')
        
        # Find the line mentioning the file
        file_line_idx = -1
        for i, line in enumerate(lines):
            if file_path in line and ('FILE_CREATE:' in line or 'FILE_MODIFY:' in line):
                file_line_idx = i
                break
        
        if file_line_idx == -1:
            return ""
        
        # Look for the next code block after the file mention
        code_content = ""
        in_code_block = False
        
        for i in range(file_line_idx + 1, len(lines)):
            line = lines[i]
            
            if line.strip().startswith('```'):
                if in_code_block:
                    # End of code block
                    break
                else:
                    # Start of code block
                    in_code_block = True
                    continue
            
            if in_code_block:
                code_content += line + '\n'
            
            # Stop if we hit another file operation
            if any(op in line for op in ['FILE_CREATE:', 'FILE_MODIFY:', 'FILE_DELETE:', 'SHELL_COMMAND:']):
                break
        
        return code_content.rstrip()
    
    def _parse_modify_instruction(self, instruction: str) -> Tuple[str, Optional[Tuple[int, int]]]:
        """Parse modify instruction to extract file path and line range."""
        # Pattern: "file.py (lines 10-20)" or just "file.py"
        match = re.match(r'(.+?)\s*\(lines?\s*(\d+)-(\d+)\)', instruction)
        
        if match:
            file_path = match.group(1).strip()
            line_start = int(match.group(2))
            line_end = int(match.group(3))
            return file_path, (line_start, line_end)
        else:
            return instruction.strip(), None
    
    def _create_file(self, operation: FileOperation):
        """Create a new file with the specified content."""
        file_path = self.working_directory / operation.file_path
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(operation.content or "")
    
    def _modify_file(self, operation: FileOperation):
        """Modify an existing file."""
        file_path = self.working_directory / operation.file_path
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {operation.file_path}")
        
        # Create backup if requested
        if operation.backup:
            self._create_backup(file_path)
        
        # Read current content
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Apply modification
        if operation.line_start is not None and operation.line_end is not None:
            # Replace specific lines
            new_lines = (operation.content or "").split('\n')
            # Convert to 0-based indexing
            start_idx = operation.line_start - 1
            end_idx = operation.line_end
            
            # Replace the lines
            lines[start_idx:end_idx] = [line + '\n' for line in new_lines]
        else:
            # Replace entire file content
            lines = (operation.content or "").split('\n')
            lines = [line + '\n' for line in lines]
        
        # Write modified content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    def _delete_file(self, operation: FileOperation):
        """Delete a file."""
        file_path = self.working_directory / operation.file_path
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {operation.file_path}")
        
        # Create backup if requested
        if operation.backup:
            self._create_backup(file_path)
        
        # Delete the file
        file_path.unlink()
    
    def _create_backup(self, file_path: Path):
        """Create a backup of the file before modification."""
        import datetime
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.name}.{timestamp}.backup"
        backup_path = self.backup_dir / backup_name
        
        # Copy file to backup location
        import shutil
        shutil.copy2(file_path, backup_path)
    
    def get_project_context(self, max_files: int = 10) -> str:
        """Get context about the current project structure."""
        context = f"Project directory: {self.working_directory}\n\n"
        
        # Get important files
        important_patterns = [
            "*.py", "*.js", "*.ts", "*.jsx", "*.tsx",
            "*.json", "*.yaml", "*.yml", "*.toml",
            "*.md", "README*", "requirements.txt",
            "package.json", "Cargo.toml", "go.mod"
        ]
        
        files_found = []
        for pattern in important_patterns:
            files_found.extend(self.working_directory.glob(pattern))
            if len(files_found) >= max_files:
                break
        
        context += "Key files:\n"
        for file_path in files_found[:max_files]:
            relative_path = file_path.relative_to(self.working_directory)
            context += f"- {relative_path}\n"
        
        return context
    
    def suggest_improvements(self, file_path: str) -> str:
        """Suggest improvements for a specific file."""
        try:
            full_path = self.working_directory / file_path
            
            if not full_path.exists():
                return f"File not found: {file_path}"
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            prompt = f"""Please review this code and suggest improvements:

File: {file_path}
```
{content}
```

Focus on:
1. Code quality and best practices
2. Performance optimizations
3. Security considerations
4. Readability and maintainability
5. Potential bugs or issues

Provide specific, actionable suggestions."""
            
            response = self.ai_client.generate_response(
                prompt=prompt,
                system_prompt=KIRO_SYSTEM_PROMPT,
                max_tokens=1000,
                temperature=0.3
            )
            
            return response
            
        except Exception as e:
            return f"Error analyzing file: {str(e)}"