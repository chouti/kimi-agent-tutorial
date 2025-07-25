"""
File reader service for MCP-based file operations.
Provides secure file reading capabilities with encoding support.
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class FileReaderService:
    """Secure file reading service for MCP"""
    
    def __init__(self):
        self.name = "file_reader"
        self.description = "Secure file reading with encoding support"
        self.capabilities = ["read", "text_processing", "encoding_detection"]
    
    def read_file(self, path: str, encoding: str = 'utf-8', max_size: int = 1024*1024) -> str:
        """Read file content with security checks"""
        try:
            file_path = Path(path).resolve()
            
            # Security check: prevent path traversal
            if not self._is_safe_path(file_path):
                raise ValueError("Path traversal detected")
            
            # Check if file exists and is readable
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            
            if not file_path.is_file():
                raise ValueError(f"Path is not a file: {path}")
            
            # Check file size
            if file_path.stat().st_size > max_size:
                raise ValueError(f"File too large: {file_path.stat().st_size} bytes")
            
            # Read with encoding detection
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    return content
            except UnicodeDecodeError:
                # Try with different encodings
                for alt_encoding in ['gbk', 'gb2312', 'latin1']:
                    try:
                        with open(file_path, 'r', encoding=alt_encoding) as f:
                            content = f.read()
                            logger.warning(f"Used {alt_encoding} encoding for {path}")
                            return content
                    except UnicodeDecodeError:
                        continue
                raise ValueError("Unable to decode file with any supported encoding")
                
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            raise
    
    def _is_safe_path(self, path: Path) -> bool:
        """Check if path is safe (no directory traversal)"""
        try:
            resolved = path.resolve()
            cwd = Path.cwd().resolve()
            # Ensure path is within current working directory
            return str(resolved).startswith(str(cwd))
        except Exception:
            return False
    
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get file metadata information"""
        try:
            file_path = Path(path).resolve()
            if not self._is_safe_path(file_path):
                raise ValueError("Path traversal detected")
            
            stat = file_path.stat()
            return {
                "exists": file_path.exists(),
                "is_file": file_path.is_file(),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "encoding": "utf-8"  # Default assumption
            }
        except Exception as e:
            logger.error(f"Error getting file info for {path}: {e}")
            return {"error": str(e)}
    
    def execute(self, parameters: Dict[str, Any]) -> str:
        """Execute file reading operation with parameter mapping"""
        try:
            path = parameters.get('path', '') or ''
            encoding = parameters.get('encoding', 'utf-8')
            max_size = parameters.get('max_size', 1024*1024)
            
            content = self.read_file(path, encoding, max_size)
            return json.dumps({
                "content": content,
                "path": path,
                "size": len(content),
                "success": True
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e), "success": False})

# Global service instance
_file_reader_service = FileReaderService()

def get_file_reader() -> FileReaderService:
    """Get the global file reader service instance"""
    return _file_reader_service

def register_file_reader_service():
    """Register the file reader service with MCP"""
    from mcp_service_discovery import get_service_manager
    service_manager = get_service_manager()
    
    return service_manager.register_custom_service(
        name="file_reader",
        description="Secure file reading with encoding support and path validation",
        capabilities=["read", "text_processing", "encoding_detection"],
        metadata={
            "type": "builtin",
            "priority": "high",
            "max_file_size": 1024*1024,
            "supported_encodings": ["utf-8", "gbk", "gb2312", "latin1"]
        }
    )

if __name__ == "__main__":
    print("Testing file reader service...")
    service = get_file_reader()
    
    try:
        content = service.read_file(__file__)
        print(f"Successfully read {len(content)} characters")
        
        info = service.get_file_info(__file__)
        print(f"File info: {info}")
        
    except Exception as e:
        print(f"Error: {e}")