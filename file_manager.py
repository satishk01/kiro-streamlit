"""File management system for Kiro specification documents."""
import os
import re
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime


class FileManager:
    """Manages specification document persistence and retrieval."""
    
    def __init__(self, base_directory: str):
        self.base_directory = Path(base_directory)
        self.specs_directory = self.base_directory / ".kiro" / "specs"
    
    def _sanitize_feature_name(self, feature_name: str) -> str:
        """Sanitize feature name for file system compatibility."""
        # Convert to lowercase and replace spaces/special chars with hyphens
        sanitized = re.sub(r'[^\w\s-]', '', feature_name.lower())
        sanitized = re.sub(r'[\s_]+', '-', sanitized)
        # Remove leading/trailing hyphens
        sanitized = sanitized.strip('-')
        return sanitized or "unnamed-feature"
    
    def create_spec_directory(self, feature_name: str) -> str:
        """Create directory structure for a new specification."""
        try:
            sanitized_name = self._sanitize_feature_name(feature_name)
            spec_path = self.specs_directory / sanitized_name
            spec_path.mkdir(parents=True, exist_ok=True)
            return str(spec_path)
        except Exception as e:
            raise IOError(f"Failed to create spec directory: {str(e)}")
    
    def save_document(self, feature_name: str, document_type: str, content: str) -> bool:
        """Save a specification document (requirements, design, or tasks)."""
        try:
            sanitized_name = self._sanitize_feature_name(feature_name)
            spec_path = self.specs_directory / sanitized_name
            
            # Ensure directory exists
            spec_path.mkdir(parents=True, exist_ok=True)
            
            # Validate document type
            if document_type not in ['requirements', 'design', 'tasks']:
                raise ValueError(f"Invalid document type: {document_type}")
            
            # Save document
            file_path = spec_path / f"{document_type}.md"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            print(f"Error saving document: {str(e)}")
            return False
    
    def load_document(self, feature_name: str, document_type: str) -> Optional[str]:
        """Load a specification document."""
        try:
            sanitized_name = self._sanitize_feature_name(feature_name)
            file_path = self.specs_directory / sanitized_name / f"{document_type}.md"
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        except Exception as e:
            print(f"Error loading document: {str(e)}")
            return None
    
    def document_exists(self, feature_name: str, document_type: str) -> bool:
        """Check if a specification document exists."""
        try:
            sanitized_name = self._sanitize_feature_name(feature_name)
            file_path = self.specs_directory / sanitized_name / f"{document_type}.md"
            return file_path.exists()
        except Exception:
            return False
    
    def list_existing_specs(self) -> List[str]:
        """List all existing specification directories."""
        try:
            if not self.specs_directory.exists():
                return []
            
            specs = []
            for item in self.specs_directory.iterdir():
                if item.is_dir():
                    specs.append(item.name)
            
            return sorted(specs)
            
        except Exception as e:
            print(f"Error listing specs: {str(e)}")
            return []
    
    def get_spec_status(self, feature_name: str) -> Tuple[bool, bool, bool]:
        """Get completion status of requirements, design, and tasks documents."""
        sanitized_name = self._sanitize_feature_name(feature_name)
        
        requirements_exists = self.document_exists(feature_name, 'requirements')
        design_exists = self.document_exists(feature_name, 'design')
        tasks_exists = self.document_exists(feature_name, 'tasks')
        
        return requirements_exists, design_exists, tasks_exists
    
    def delete_spec(self, feature_name: str) -> bool:
        """Delete an entire specification directory."""
        try:
            sanitized_name = self._sanitize_feature_name(feature_name)
            spec_path = self.specs_directory / sanitized_name
            
            if spec_path.exists():
                import shutil
                shutil.rmtree(spec_path)
                return True
            return False
            
        except Exception as e:
            print(f"Error deleting spec: {str(e)}")
            return False
    
    def backup_document(self, feature_name: str, document_type: str) -> bool:
        """Create a backup of a document before modification."""
        try:
            content = self.load_document(feature_name, document_type)
            if content is None:
                return False
            
            sanitized_name = self._sanitize_feature_name(feature_name)
            spec_path = self.specs_directory / sanitized_name
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{document_type}_backup_{timestamp}.md"
            backup_path = spec_path / backup_filename
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            print(f"Error creating backup: {str(e)}")
            return False
    
    def validate_base_directory(self) -> bool:
        """Validate that the base directory is accessible."""
        try:
            return self.base_directory.exists() and self.base_directory.is_dir()
        except Exception:
            return False
    
    def ensure_kiro_structure(self) -> bool:
        """Ensure .kiro/specs directory structure exists."""
        try:
            self.specs_directory.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating .kiro structure: {str(e)}")
            return False