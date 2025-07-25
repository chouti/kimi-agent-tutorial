"""
Directory listing service for MCP-based directory operations.
Provides secure directory browsing and file listing capabilities.
"""

import os
import logging
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class DirectoryListerService:
    """Secure directory listing service for MCP"""
    
    def __init__(self):
        self.name = "directory_lister"
        self.description = "Secure directory listing and file information"
        self.capabilities = ["list", "directory", "file_info", "metadata"]
    
    def list_directory(self, path: str = ".", include_hidden: bool = False) -> Dict[str, Any]:
        """List directory contents with detailed information"""
        try:
            dir_path = Path(path).resolve()
            
            # Security check: prevent path traversal
            if not self._is_safe_path(dir_path):
                raise ValueError("Path traversal detected")
            
            if not dir_path.exists():
                raise FileNotFoundError(f"Directory not found: {path}")
            
            if not dir_path.is_dir():
                raise ValueError(f"Path is not a directory: {path}")
            
            items = []
            try:
                for item in dir_path.iterdir():
                    if not include_hidden and item.name.startswith('.'):
                        continue
                    
                    stat = item.stat()
                    items.append({
                        "name": item.name,
                        "path": str(item.relative_to(Path.cwd())),
                        "type": "directory" if item.is_dir() else "file",
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "permissions": oct(stat.st_mode)[-3:]
                    })
            except PermissionError as e:
                raise PermissionError(f"Permission denied accessing: {path}")
            
            return {
                "directory": str(dir_path),
                "items": items,
                "total_count": len(items)
            }
            
        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
            raise
    
    def list_files_only(self, path: str = ".", include_hidden: bool = False) -> List[str]:
        """List only file names in directory"""
        try:
            dir_path = Path(path).resolve()
            
            if not self._is_safe_path(dir_path):
                raise ValueError("Path traversal detected")
            
            if not dir_path.exists() or not dir_path.is_dir():
                return []
            
            files = []
            for item in dir_path.iterdir():
                if item.is_file():
                    if not include_hidden or not item.name.startswith('.'):
                        files.append(item.name)
            
            return sorted(files)
            
        except Exception as e:
            logger.error(f"Error listing files {path}: {e}")
            return []
    
    def list_directories_only(self, path: str = ".", include_hidden: bool = False) -> List[str]:
        """List only directory names in directory"""
        try:
            dir_path = Path(path).resolve()
            
            if not self._is_safe_path(dir_path):
                raise ValueError("Path traversal detected")
            
            if not dir_path.exists() or not dir_path.is_dir():
                return []
            
            directories = []
            for item in dir_path.iterdir():
                if item.is_dir():
                    if not include_hidden or not item.name.startswith('.'):
                        directories.append(item.name)
            
            return sorted(directories)
            
        except Exception as e:
            logger.error(f"Error listing directories {path}: {e}")
            return []
    
    def _is_safe_path(self, path: Path) -> bool:
        """Check if path is safe (no directory traversal)"""
        try:
            resolved = path.resolve()
            cwd = Path.cwd().resolve()
            return str(resolved).startswith(str(cwd))
        except Exception:
            return False
    
    def get_directory_info(self, path: str = ".") -> Dict[str, Any]:
        """Get detailed directory information"""
        try:
            dir_path = Path(path).resolve()
            
            if not self._is_safe_path(dir_path):
                raise ValueError("Path traversal detected")
            
            if not dir_path.exists() or not dir_path.is_dir():
                raise FileNotFoundError(f"Directory not found: {path}")
            
            stat = dir_path.stat()
            items = list(dir_path.iterdir())
            
            file_count = sum(1 for item in items if item.is_file())
            dir_count = sum(1 for item in items if item.is_dir())
            
            return {
                "path": str(dir_path),
                "exists": True,
                "is_directory": True,
                "total_items": len(items),
                "file_count": file_count,
                "directory_count": dir_count,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:]
            }
            
        except Exception as e:
            logger.error(f"Error getting directory info {path}: {e}")
            return {"error": str(e), "exists": False}
    
    def execute(self, parameters: Dict[str, Any]) -> str:
        """Execute directory listing operation with parameter mapping"""
        try:
            path = parameters.get('path', '.') or '.'
            include_hidden = parameters.get('include_hidden', False)
            
            result = self.list_directory(path, include_hidden)
            
            # Return JSON string for structured data
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({"error": str(e)})

# Global service instance
_directory_lister_service = DirectoryListerService()

def get_directory_lister() -> DirectoryListerService:
    """Get the global directory lister service instance"""
    return _directory_lister_service

def register_directory_lister_service():
    """Register the directory lister service with MCP"""
    from mcp_service_discovery import get_service_manager
    service_manager = get_service_manager()
    
    return service_manager.register_custom_service(
        name="directory_lister",
        description="Secure directory listing and file information with path validation",
        capabilities=["list", "directory", "file_info", "metadata"],
        metadata={
            "type": "builtin",
            "priority": "high",
            "include_hidden": False,
            "max_items": 1000
        }
    )

if __name__ == "__main__":
    print("Testing directory lister service...")
    service = get_directory_lister()
    
    try:
        result = service.list_directory(".")
        print(f"Found {result['total_count']} items in current directory")
        
        info = service.get_directory_info(".")
        print(f"Directory info: {info}")
        
    except Exception as e:
        print(f"Error: {e}")