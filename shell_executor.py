"""
Shell execution service for MCP-based command execution.
Provides secure shell command execution with safety controls and permission management.
"""

import subprocess
import shlex
import os
import re
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from mcp_service_discovery import ServiceInfo, get_service_manager

# Import LLM security analyzer
try:
    from llm_security_analyzer import get_hybrid_security_analyzer
    LLM_ENABLED = True
except ImportError:
    LLM_ENABLED = False
    get_hybrid_security_analyzer = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommandStatus(Enum):
    """Command execution status"""
    SUCCESS = "success"
    ERROR = "error"
    BLOCKED = "blocked"
    TIMEOUT = "timeout"

class SecurityLevel(Enum):
    """Security permission levels"""
    SAFE = "safe"
    MODERATE = "moderate"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"

@dataclass
class CommandResult:
    """Result of command execution"""
    command: str
    status: CommandStatus
    stdout: str
    stderr: str
    return_code: int
    execution_time: float
    security_level: SecurityLevel
    blocked_reason: Optional[str] = None

@dataclass
class SecurityRule:
    """Security rule for command validation"""
    pattern: str
    level: SecurityLevel
    description: str
    allowed: bool = False

class ShellSecurity:
    """Security manager for shell command execution"""
    
    def __init__(self):
        self.dangerous_commands = {
            'rm': ['-rf', '--no-preserve-root'],
            'sudo': [],
            'su': [],
            'dd': [],
            'mkfs': [],
            'fdisk': [],
            'chmod': ['777', '000'],
            'chown': [],
            'wget': [],
            'curl': [],
            'nc': [],
            'netcat': [],
            'telnet': [],
        }
        
        self.dangerous_patterns = [
            r'\|\s*rm',  # pipe to rm
            r'>\s*/dev/(sda|sdb)',  # redirect to disk
            r':\(\)\{\s*:\|\s*:\s*&\s*\};\s*:',  # fork bomb
            r'rm\s+-(rf|fr)',  # rm -rf
            r'sudo\s+rm',  # sudo rm
            r'mkfs\.?\w*\s+/dev',  # format disk
            r'dd\s+.*of=/dev',  # dd to disk
        ]
        
        self.allowed_commands = {
            'ls', 'cat', 'grep', 'find', 'pwd', 'echo', 'date', 'whoami',
            'ps', 'top', 'df', 'du', 'head', 'tail', 'wc', 'sort', 'uniq',
            'cut', 'awk', 'sed', 'tr', 'xargs', 'which', 'whereis', 'file',
            'stat', 'dirname', 'basename', 'dirname', 'realpath', 'readlink',
            'env', 'printenv', 'uptime', 'hostname', 'uname', 'lsb_release',
            'python3', 'python', 'node', 'npm', 'pip', 'pip3', 'git'
        }
    
    def validate_command(self, command: str) -> SecurityLevel:
        """Validate command against security rules"""
        command_parts = shlex.split(command)
        if not command_parts:
            return SecurityLevel.BLOCKED
        
        cmd = command_parts[0]
        
        # Check for dangerous commands
        if cmd in self.dangerous_commands:
            return SecurityLevel.BLOCKED
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return SecurityLevel.BLOCKED
        
        # Check if command is explicitly allowed
        if cmd in self.allowed_commands:
            return SecurityLevel.SAFE
        
        # Check for system modification commands
        if any(sys_cmd in cmd for sys_cmd in ['systemctl', 'service', 'init', 'rc']):
            return SecurityLevel.RESTRICTED
        
        return SecurityLevel.MODERATE
    
    def sanitize_command(self, command: str) -> str:
        """Sanitize command for safe execution"""
        # Remove any potential command chaining
        dangerous_chars = ['&', '|', ';', '`', '$', '(', ')', '<', '>']
        for char in dangerous_chars:
            if char in command and char not in ['|', '>']:  # Allow pipes and redirects but carefully
                command = command.replace(char, '\\' + char)
        
        return command.strip()

class ShellExecutor:
    """Shell execution service for MCP with LLM-enhanced security"""
    
    def __init__(self, timeout: int = 30, max_output_size: int = 1024 * 1024,
                 enable_llm_security: bool = True):
        self.name = "shell_executor"
        self.description = "Secure shell command execution with LLM-enhanced safety controls"
        self.capabilities = [
            "execute", "list_processes", "system_info", "file_operations",
            "directory_operations", "network_info", "process_management",
            "llm_security_analysis"
        ]
        self.timeout = timeout
        self.max_output_size = max_output_size
        self.security = ShellSecurity()
        self.working_dir = os.getcwd()
        self.enable_llm_security = enable_llm_security and LLM_ENABLED
        
        if self.enable_llm_security and get_hybrid_security_analyzer:
            self.llm_security = get_hybrid_security_analyzer()
        else:
            self.llm_security = None
    
    def execute_command(self, command: str, cwd: Optional[str] = None, 
                       timeout: Optional[int] = None, 
                       capture_output: bool = True,
                       interactive_mode: bool = False) -> CommandResult:
        """Execute a shell command with security validation and optional user confirmation"""
        
        import time
        start_time = time.time()
        
        # Multi-layer security analysis
        security_result = self._perform_security_analysis(command)
        
        if security_result["final_security_level"] == "BLOCKED":
            return CommandResult(
                command=command,
                status=CommandStatus.BLOCKED,
                stdout="",
                stderr=f"Command blocked: {security_result['decision_reason']}",
                return_code=126,
                execution_time=time.time() - start_time,
                security_level=SecurityLevel.BLOCKED,
                blocked_reason=security_result['decision_reason']
            )
        
        # Interactive confirmation for moderate risk commands
        if interactive_mode and security_result["final_security_level"] in ["MODERATE", "RESTRICTED"]:
            requires_confirmation = security_result.get("requires_confirmation", True)
            risk_score = security_result.get("risk_score", 50)
            
            if requires_confirmation and risk_score > 30:
                print(f"\n⚠️  命令安全分析结果:")
                print(f"   命令: {command}")
                print(f"   风险等级: {security_result['final_security_level']}")
                print(f"   风险评分: {risk_score}/100")
                print(f"   分析结果: {security_result.get('decision_reason', '需要确认')}")
                
                if "alternatives" in security_result:
                    print(f"   建议替代: {security_result['alternatives']}")
                
                try:
                    user_input = input("\n   是否继续执行? [y/N]: ").strip().lower()
                    if user_input not in ['y', 'yes', '是']:
                        return CommandResult(
                            command=command,
                            status=CommandStatus.BLOCKED,
                            stdout="",
                            stderr="Command cancelled by user",
                            return_code=130,
                            execution_time=time.time() - start_time,
                            security_level=SecurityLevel.BLOCKED,
                            blocked_reason="User cancelled execution"
                        )
                except (KeyboardInterrupt, EOFError):
                    return CommandResult(
                        command=command,
                        status=CommandStatus.BLOCKED,
                        stdout="",
                        stderr="Command cancelled by user interruption",
                        return_code=130,
                        execution_time=time.time() - start_time,
                        security_level=SecurityLevel.BLOCKED,
                        blocked_reason="User interrupted"
                    )
        
        # Sanitize command
        sanitized_command = self.security.sanitize_command(command)
        
        # Set working directory
        execution_cwd = cwd or self.working_dir
        
        try:
            # Execute command
            result = subprocess.run(
                sanitized_command,
                shell=True,
                capture_output=capture_output,
                text=True,
                timeout=timeout or self.timeout,
                cwd=execution_cwd
            )
            
            # Check output size
            if len(result.stdout) > self.max_output_size:
                stdout = result.stdout[:self.max_output_size] + "\n[Output truncated]"
            else:
                stdout = result.stdout
            
            if len(result.stderr) > self.max_output_size:
                stderr = result.stderr[:self.max_output_size] + "\n[Error truncated]"
            else:
                stderr = result.stderr
            
            return CommandResult(
                command=sanitized_command,
                status=CommandStatus.SUCCESS if result.returncode == 0 else CommandStatus.ERROR,
                stdout=stdout,
                stderr=stderr,
                return_code=result.returncode,
                execution_time=time.time() - start_time,
                security_level=SecurityLevel.SAFE if result.returncode == 0 else SecurityLevel.RESTRICTED
            )
            
        except subprocess.TimeoutExpired:
            return CommandResult(
                command=sanitized_command,
                status=CommandStatus.TIMEOUT,
                stdout="",
                stderr=f"Command timed out after {timeout or self.timeout} seconds",
                return_code=124,
                execution_time=time.time() - start_time,
                security_level=SecurityLevel.BLOCKED
            )
        except Exception as e:
            return CommandResult(
                command=sanitized_command,
                status=CommandStatus.ERROR,
                stdout="",
                stderr=str(e),
                return_code=1,
                execution_time=time.time() - start_time,
                security_level=SecurityLevel.BLOCKED
            )
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get basic system information"""
        try:
            result = self.execute_command("uname -a")
            os_info = result.stdout if result.status == CommandStatus.SUCCESS else "Unknown"
            
            result = self.execute_command("whoami")
            user = result.stdout.strip() if result.status == CommandStatus.SUCCESS else "Unknown"
            
            result = self.execute_command("pwd")
            pwd = result.stdout.strip() if result.status == CommandStatus.SUCCESS else "Unknown"
            
            return {
                "os": os_info,
                "user": user,
                "working_directory": pwd,
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                "platform": os.sys.platform
            }
        except Exception as e:
            return {"error": str(e)}
    
    def list_directory(self, path: str = ".") -> Dict[str, Any]:
        """List directory contents"""
        try:
            result = self.execute_command(f"ls -la '{path}'")
            if result.status == CommandStatus.SUCCESS:
                lines = result.stdout.strip().split('\n')
                files = []
                for line in lines[1:]:  # Skip total line
                    parts = line.split(None, 8)
                    if len(parts) >= 9:
                        files.append({
                            "permissions": parts[0],
                            "links": parts[1],
                            "owner": parts[2],
                            "group": parts[3],
                            "size": parts[4],
                            "date": " ".join(parts[5:8]),
                            "name": parts[8]
                        })
                return {"files": files, "path": path}
            else:
                return {"error": result.stderr}
        except Exception as e:
            return {"error": str(e)}
    
    def get_process_list(self) -> Dict[str, Any]:
        """Get running processes"""
        try:
            # Use ps for Unix-like systems
            if os.name == 'posix':
                result = self.execute_command("ps aux | head -20")
            else:
                # Windows
                result = self.execute_command("tasklist /FO CSV | head -20")
            
            return {
                "output": result.stdout,
                "error": result.stderr if result.status != CommandStatus.SUCCESS else None
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage information"""
        try:
            if os.name == 'posix':
                result = self.execute_command("df -h")
            else:
                result = self.execute_command("wmic logicaldisk get size,freespace,caption")
            
            return {
                "output": result.stdout,
                "error": result.stderr if result.status != CommandStatus.SUCCESS else None
            }
        except Exception as e:
            return {"error": str(e)}
    
    def safe_file_operations(self, operation: str, path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """Safe file operations (read, write, append)"""
        try:
            path_obj = Path(path)
            
            if operation == "read":
                if not path_obj.exists():
                    return {"error": "File does not exist"}
                result = self.execute_command(f"cat '{path}'")
                return {"content": result.stdout, "error": result.stderr if result.status != CommandStatus.SUCCESS else None}
            
            elif operation == "write":
                if content is None:
                    return {"error": "Content required for write operation"}
                # Use echo for simple writes
                escaped_content = content.replace("'", "'\"'\"'")
                result = self.execute_command(f"echo '{escaped_content}' > '{path}'")
                return {"success": result.status == CommandStatus.SUCCESS, "error": result.stderr}
            
            elif operation == "append":
                if content is None:
                    return {"error": "Content required for append operation"}
                escaped_content = content.replace("'", "'\"'\"'")
                result = self.execute_command(f"echo '{escaped_content}' >> '{path}'")
                return {"success": result.status == CommandStatus.SUCCESS, "error": result.stderr}
            
            else:
                return {"error": f"Unsupported operation: {operation}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def validate_path(self, path: str) -> bool:
        """Validate if path is within allowed directories with symlink protection"""
        try:
            abs_path = Path(path).resolve()
            working_abs = Path(self.working_dir).resolve()
            
            # Check if path is within working directory
            return str(abs_path).startswith(str(working_abs))
        except Exception:
            return False
    
    def _perform_security_analysis(self, command: str) -> Dict[str, Any]:
        """Perform multi-layer security analysis"""
        context = {
            "working_directory": self.working_dir,
            "user": os.getenv("USER", "unknown"),
            "system": os.name,
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}"
        }
        
        if self.llm_security:
            # Use LLM-enhanced security analysis
            return self.llm_security.comprehensive_analysis(command, context)
        else:
            # Fallback to traditional security
            traditional_level = self.security.validate_command(command)
            return {
                "final_security_level": traditional_level,
                "decision_reason": "Traditional pattern-based security",
                "risk_score": 50 if traditional_level == "BLOCKED" else 20,
                "requires_confirmation": traditional_level != "SAFE"
            }
    
    def analyze_command_security(self, command: str) -> Dict[str, Any]:
        """Analyze command security using LLM when available"""
        if not self.llm_security or not self.enable_llm_security:
            return {
                "available": False,
                "message": "LLM security analysis not available",
                "traditional_only": True
            }
        
        context = {
            "working_directory": self.working_dir,
            "user": os.getenv("USER", "unknown"),
            "system": os.name
        }
        
        return self.llm_security.comprehensive_analysis(command, context)
    
    def get_security_capabilities(self) -> Dict[str, Any]:
        """Get security analysis capabilities"""
        return {
            "llm_enabled": self.enable_llm_security and self.llm_security is not None,
            "traditional_security": True,
            "layers": ["pattern_matching", "command_blacklist", "llm_analysis"] if self.enable_llm_security else ["pattern_matching", "command_blacklist"],
            "features": ["risk_scoring", "explanation", "alternatives", "confidence"] if self.enable_llm_security else ["basic_blocking"]
        }

# Global shell executor instance
_shell_executor = ShellExecutor()

def get_shell_executor() -> ShellExecutor:
    """Get the global shell executor instance"""
    return _shell_executor

def register_shell_service():
    """Register the shell executor service with MCP"""
    service_manager = get_service_manager()
    
    return service_manager.register_custom_service(
        name="shell_executor",
        description="Secure shell command execution with LLM-enhanced safety controls and multi-layer security",
        capabilities=[
            "execute", "system_info", "list_processes", "directory_operations",
            "file_operations", "disk_usage", "process_management", "network_info",
            "llm_security_analysis"
        ],
        metadata={
            "type": "builtin",
            "priority": "high",
            "category": "system_operations",
            "security_level": "moderate",
            "timeout": 30,
            "max_output_size": 1048576,
            "features": ["llm_security", "pattern_matching", "risk_scoring"]
        }
    )

if __name__ == "__main__":
    # Test the shell executor service
    print("Testing shell executor service registration...")
    success = register_shell_service()
    print(f"Shell service registration: {'SUCCESS' if success else 'FAILED'}")
    
    if success:
        executor = get_shell_executor()
        
        # Test basic functionality
        print("\\nTesting system info...")
        info = executor.get_system_info()
        print(f"System: {info.get('os', 'Unknown')[:50]}...")
        print(f"User: {info.get('user', 'Unknown')}")
        print(f"Working directory: {info.get('working_directory', 'Unknown')}")
        
        # Test safe command execution
        print("\\nTesting safe command execution...")
        result = executor.execute_command("ls -la")
        print(f"Command status: {result.status.value}")
        print(f"Output lines: {len(result.stdout.split())}")
        
        # Test security validation
        print("\\nTesting security validation...")
        blocked_result = executor.execute_command("rm -rf /")
        print(f"Dangerous command blocked: {blocked_result.status == CommandStatus.BLOCKED}")