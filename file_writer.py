"""
File writer service for MCP-based file operations.
Provides secure file writing, editing, and creation capabilities.
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class FileWriterService:
    """Secure file writing service for MCP"""
    
    def __init__(self):
        self.name = "file_writer"
        self.description = "Secure file writing, editing, and creation"
        self.capabilities = ["write", "edit", "create", "append", "replace"]
    
    def write_file(self, path: str, content: str, mode: str = 'write') -> str:
        """Write content to file with security checks"""
        try:
            file_path = Path(path).resolve()
            
            # Security check: prevent path traversal
            if not self._is_safe_path(file_path):
                raise ValueError("Path traversal detected")
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if mode == 'write':
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"File written successfully: {path}"
            
            elif mode == 'append':
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write(content)
                return f"Content appended successfully: {path}"
            
            elif mode == 'replace':
                # For backward compatibility
                return self.write_file(path, content, 'write')
            
            else:
                raise ValueError(f"Unsupported mode: {mode}")
                
        except Exception as e:
            logger.error(f"Error writing file {path}: {e}")
            raise
    
    def edit_file(self, path: str, old_content: str, new_content: str) -> str:
        """Edit file by replacing old content with new content"""
        try:
            file_path = Path(path).resolve()
            
            # Security check: prevent path traversal
            if not self._is_safe_path(file_path):
                raise ValueError("Path traversal detected")
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            
            # Read current content
            with open(file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
            
            # Replace content
            if old_content and old_content in current_content:
                new_content_full = current_content.replace(old_content, new_content)
            elif old_content == "":
                # Create new file or append
                new_content_full = new_content
            else:
                raise ValueError("Old content not found in file")
            
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content_full)
            
            return f"File edited successfully: {path}"
            
        except Exception as e:
            logger.error(f"Error editing file {path}: {e}")
            raise
    
    def _is_safe_path(self, path: Path) -> bool:
        """Check if path is safe (no directory traversal)"""
        try:
            resolved = path.resolve()
            cwd = Path.cwd().resolve()
            return str(resolved).startswith(str(cwd))
        except Exception:
            return False
    
    def create_file(self, path: str, content: str = "") -> str:
        """Create a new file"""
        return self.write_file(path, content, 'write')
    
    def append_to_file(self, path: str, content: str) -> str:
        """Append content to existing file"""
        return self.write_file(path, content, 'append')
    
    def execute(self, parameters: Dict[str, Any]) -> str:
        """Execute file writing operation with parameter mapping"""
        try:
            path = parameters.get('path', '') or ''
            content = parameters.get('content', parameters.get('new_content', ''))
            mode = parameters.get('mode', 'write')
            old_content = parameters.get('old_content', '')
            
            if old_content and old_content.strip():
                result = self.edit_file(path, old_content, content)
            else:
                result = self.write_file(path, content, mode)
            
            return json.dumps({
                "result": result,
                "path": path,
                "success": True
            }, ensure_ascii=False)
                
        except Exception as e:
            return json.dumps({"error": str(e), "success": False})

# Global service instance
_file_writer_service = FileWriterService()

def get_file_writer() -> FileWriterService:
    """Get the global file writer service instance"""
    return _file_writer_service

def register_file_writer_service():
    """Register the file writer service with MCP"""
    from mcp_service_discovery import get_service_manager
    service_manager = get_service_manager()
    
    return service_manager.register_custom_service(
        name="file_writer",
        description="Secure file writing, editing, and creation with path validation",
        capabilities=["write", "edit", "create", "append", "replace"],
        metadata={
            "type": "builtin",
            "priority": "high",
            "encoding": "utf-8",
            "max_file_size": 10*1024*1024
        }
    )

if __name__ == "__main__":
    print("Testing file writer service...")
    service = get_file_writer()
    
    try:
        # Test write
        result = service.write_file("test_write.txt", "Hello World!")
        print(result)
        
        # Test edit
        result = service.edit_file("test_write.txt", "Hello", "Hi")
        print(result)
        
        # Test append
        result = service.append_to_file("test_write.txt", "\nAppended text")
        print(result)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        try:
            Path("test_write.txt").unlink()
        except:
            pass