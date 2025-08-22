"""File browser component for Kiro-like interface."""
import streamlit as st
import os
from pathlib import Path
from typing import List, Dict, Optional
import mimetypes


class FileBrowser:
    """File browser component similar to Kiro's file explorer."""
    
    def __init__(self, root_directory: str = None):
        """Initialize file browser with root directory."""
        self.root_directory = Path(root_directory) if root_directory else Path.cwd()
        
        # Initialize session state for file browser
        if "file_browser_current_path" not in st.session_state:
            st.session_state.file_browser_current_path = str(self.root_directory)
        if "file_browser_selected_file" not in st.session_state:
            st.session_state.file_browser_selected_file = None
        if "file_browser_expanded_dirs" not in st.session_state:
            st.session_state.file_browser_expanded_dirs = set()
    
    def render_file_browser(self, height: int = 400) -> Optional[str]:
        """
        Render the file browser interface.
        
        Args:
            height: Height of the file browser container
            
        Returns:
            Path of selected file, if any
        """
        st.markdown("**📁 File Explorer**")
        
        # Current path display
        current_path = Path(st.session_state.file_browser_current_path)
        
        # Breadcrumb navigation
        self._render_breadcrumb(current_path)
        
        # File tree container
        with st.container():
            st.markdown(f'<div style="height: {height}px; overflow-y: auto; border: 1px solid #e5e7eb; border-radius: 8px; padding: 0.5rem;">', unsafe_allow_html=True)
            
            try:
                # Render directory contents
                self._render_directory_contents(current_path)
                
            except PermissionError:
                st.error("Permission denied accessing this directory")
            except Exception as e:
                st.error(f"Error reading directory: {str(e)}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        return st.session_state.file_browser_selected_file
    
    def _render_breadcrumb(self, current_path: Path):
        """Render breadcrumb navigation."""
        parts = current_path.parts
        breadcrumb_html = '<div style="margin-bottom: 0.5rem; font-size: 0.875rem; color: #6b7280;">'
        
        # Home button
        if st.button("🏠", key="file_browser_home", help="Go to root directory"):
            st.session_state.file_browser_current_path = str(self.root_directory)
            st.rerun()
        
        # Path parts
        for i, part in enumerate(parts):
            if i > 0:
                breadcrumb_html += " / "
            breadcrumb_html += part
        
        breadcrumb_html += '</div>'
        st.markdown(breadcrumb_html, unsafe_allow_html=True)
    
    def _render_directory_contents(self, directory: Path):
        """Render the contents of a directory."""
        try:
            items = list(directory.iterdir())
            
            # Sort: directories first, then files
            directories = [item for item in items if item.is_dir() and not item.name.startswith('.')]
            files = [item for item in items if item.is_file() and not item.name.startswith('.')]
            
            # Show parent directory option if not at root
            if directory != self.root_directory:
                if st.button("📁 ..", key=f"file_browser_parent_{directory}", help="Go to parent directory"):
                    st.session_state.file_browser_current_path = str(directory.parent)
                    st.rerun()
            
            # Render directories
            for dir_path in sorted(directories, key=lambda x: x.name.lower()):
                self._render_directory_item(dir_path)
            
            # Render files
            for file_path in sorted(files, key=lambda x: x.name.lower()):
                self._render_file_item(file_path)
                
        except PermissionError:
            st.error("Permission denied")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    def _render_directory_item(self, dir_path: Path):
        """Render a directory item."""
        dir_key = f"file_browser_dir_{dir_path}"
        
        col1, col2 = st.columns([1, 10])
        
        with col1:
            # Directory icon
            st.markdown("📁")
        
        with col2:
            # Directory name as button
            if st.button(dir_path.name, key=dir_key, help=f"Open {dir_path.name}"):
                st.session_state.file_browser_current_path = str(dir_path)
                st.rerun()
    
    def _render_file_item(self, file_path: Path):
        """Render a file item."""
        file_key = f"file_browser_file_{file_path}"
        
        col1, col2, col3 = st.columns([1, 8, 2])
        
        with col1:
            # File icon based on type
            icon = self._get_file_icon(file_path)
            st.markdown(icon)
        
        with col2:
            # File name as button
            if st.button(file_path.name, key=file_key, help=f"Select {file_path.name}"):
                st.session_state.file_browser_selected_file = str(file_path)
                st.success(f"Selected: {file_path.name}")
        
        with col3:
            # File size
            try:
                size = file_path.stat().st_size
                size_str = self._format_file_size(size)
                st.markdown(f'<small style="color: #6b7280;">{size_str}</small>', unsafe_allow_html=True)
            except:
                pass
    
    def _get_file_icon(self, file_path: Path) -> str:
        """Get appropriate icon for file type."""
        suffix = file_path.suffix.lower()
        
        # Programming files
        if suffix in ['.py', '.pyx', '.pyi']:
            return "🐍"
        elif suffix in ['.js', '.jsx', '.ts', '.tsx']:
            return "📜"
        elif suffix in ['.html', '.htm']:
            return "🌐"
        elif suffix in ['.css', '.scss', '.sass']:
            return "🎨"
        elif suffix in ['.json', '.yaml', '.yml', '.toml']:
            return "⚙️"
        elif suffix in ['.md', '.markdown']:
            return "📝"
        elif suffix in ['.txt', '.log']:
            return "📄"
        elif suffix in ['.pdf']:
            return "📕"
        elif suffix in ['.jpg', '.jpeg', '.png', '.gif', '.svg']:
            return "🖼️"
        elif suffix in ['.zip', '.tar', '.gz', '.rar']:
            return "📦"
        elif suffix in ['.exe', '.app', '.deb', '.rpm']:
            return "⚡"
        else:
            return "📄"
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def get_selected_file(self) -> Optional[str]:
        """Get the currently selected file."""
        return st.session_state.file_browser_selected_file
    
    def set_root_directory(self, directory: str):
        """Set the root directory for the file browser."""
        self.root_directory = Path(directory)
        st.session_state.file_browser_current_path = str(self.root_directory)
    
    def render_file_content_preview(self, file_path: str, max_lines: int = 50) -> bool:
        """
        Render a preview of file content.
        
        Args:
            file_path: Path to the file to preview
            max_lines: Maximum number of lines to show
            
        Returns:
            True if preview was rendered, False otherwise
        """
        try:
            path = Path(file_path)
            
            if not path.exists() or not path.is_file():
                return False
            
            # Check file size (don't preview very large files)
            if path.stat().st_size > 1024 * 1024:  # 1MB limit
                st.warning("File too large to preview")
                return False
            
            # Try to read as text
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                if len(lines) > max_lines:
                    content = ''.join(lines[:max_lines])
                    content += f"\n... ({len(lines) - max_lines} more lines)"
                else:
                    content = ''.join(lines)
                
                # Determine language for syntax highlighting
                language = self._get_language_from_extension(path.suffix)
                
                st.markdown(f"**Preview: {path.name}**")
                st.code(content, language=language)
                
                return True
                
            except UnicodeDecodeError:
                st.info("Binary file - cannot preview content")
                return False
                
        except Exception as e:
            st.error(f"Error previewing file: {str(e)}")
            return False
    
    def _get_language_from_extension(self, extension: str) -> str:
        """Get language identifier for syntax highlighting."""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.sh': 'bash',
            '.sql': 'sql',
            '.xml': 'xml',
            '.toml': 'toml'
        }
        
        return ext_map.get(extension.lower(), 'text')