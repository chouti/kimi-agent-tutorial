"""
Git service for MCP-based version control operations.
Provides git functionality through the MCP service discovery system.
"""

import subprocess
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from mcp_service_discovery import ServiceInfo, get_service_manager

@dataclass
class GitStatus:
    """Represents git repository status"""
    branch: str
    is_clean: bool
    staged_files: List[str]
    modified_files: List[str]
    untracked_files: List[str]
    ahead: int = 0
    behind: int = 0

@dataclass
class GitCommit:
    """Represents a git commit"""
    hash: str
    author: str
    email: str
    date: str
    message: str
    
class GitService:
    """Git service implementation for MCP"""
    
    def __init__(self):
        self.name = "git_service"
        self.description = "Git version control operations"
        self.capabilities = [
            "status", "commit", "push", "pull", "branch", "log",
            "diff", "add", "reset", "clone", "init"
        ]
    
    def _run_git_command(self, args: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
        """Execute a git command and return results"""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=cwd or os.getcwd(),
                capture_output=True,
                text=True,
                check=True
            )
            return {
                "success": True,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "stdout": e.stdout.strip() if e.stdout else "",
                "stderr": e.stderr.strip() if e.stderr else str(e),
                "returncode": e.returncode
            }
        except FileNotFoundError:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Git not found. Please install git.",
                "returncode": 127
            }
    
    def is_git_repository(self, path: str = None) -> bool:
        """Check if the given path is a git repository"""
        result = self._run_git_command(["rev-parse", "--git-dir"], cwd=path)
        return result["success"]
    
    def get_status(self, path: str = None) -> Dict[str, Any]:
        """Get git repository status"""
        if not self.is_git_repository(path):
            return {"error": "Not a git repository"}
        
        # Get branch name
        branch_result = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"], cwd=path)
        branch = branch_result["stdout"] if branch_result["success"] else "unknown"
        
        # Get status
        status_result = self._run_git_command(["status", "--porcelain=v1", "-b"], cwd=path)
        if not status_result["success"]:
            return {"error": status_result["stderr"]}
        
        lines = status_result["stdout"].split('\n') if status_result["stdout"] else []
        
        staged_files = []
        modified_files = []
        untracked_files = []
        ahead = 0
        behind = 0
        
        for line in lines:
            if line.startswith("##"):
                # Branch info line
                if "ahead" in line:
                    import re
                    ahead_match = re.search(r'ahead (\d+)', line)
                    behind_match = re.search(r'behind (\d+)', line)
                    if ahead_match:
                        ahead = int(ahead_match.group(1))
                    if behind_match:
                        behind = int(behind_match.group(1))
            elif line:
                status = line[:2]
                filename = line[3:]
                if status[0] != ' ':
                    staged_files.append(filename)
                if status[1] != ' ':
                    if status[1] == 'M':
                        modified_files.append(filename)
                    elif status[1] == '?':
                        untracked_files.append(filename)
        
        is_clean = len(staged_files) + len(modified_files) + len(untracked_files) == 0
        
        return {
            "branch": branch,
            "is_clean": is_clean,
            "staged_files": staged_files,
            "modified_files": modified_files,
            "untracked_files": untracked_files,
            "ahead": ahead,
            "behind": behind
        }
    
    def commit_changes(self, message: str, path: str = None) -> Dict[str, Any]:
        """Commit changes with the given message"""
        if not self.is_git_repository(path):
            return {"error": "Not a git repository"}
        
        result = self._run_git_command(["commit", "-m", message], cwd=path)
        return result
    
    def add_files(self, files: List[str] = None, path: str = None) -> Dict[str, Any]:
        """Add files to staging area"""
        if not self.is_git_repository(path):
            return {"error": "Not a git repository"}
        
        if files is None:
            # Add all files
            result = self._run_git_command(["add", "."], cwd=path)
        else:
            # Add specific files
            result = self._run_git_command(["add"] + files, cwd=path)
        
        return result
    
    def push_changes(self, remote: str = "origin", branch: str = None, path: str = None) -> Dict[str, Any]:
        """Push changes to remote repository"""
        if not self.is_git_repository(path):
            return {"error": "Not a git repository"}
        
        if branch is None:
            # Get current branch
            branch_result = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"], cwd=path)
            if not branch_result["success"]:
                return {"error": "Could not determine current branch"}
            branch = branch_result["stdout"]
        
        result = self._run_git_command(["push", remote, branch], cwd=path)
        return result
    
    def pull_changes(self, remote: str = "origin", branch: str = None, path: str = None) -> Dict[str, Any]:
        """Pull changes from remote repository"""
        if not self.is_git_repository(path):
            return {"error": "Not a git repository"}
        
        cmd = ["pull"]
        if remote and branch:
            cmd.extend([remote, branch])
        
        result = self._run_git_command(cmd, cwd=path)
        return result
    
    def get_log(self, max_count: int = 10, path: str = None) -> List[Dict[str, str]]:
        """Get git commit log"""
        if not self.is_git_repository(path):
            return []
        
        format_string = '%H|%an|%ae|%ad|%s'
        result = self._run_git_command([
            "log", f"--max-count={max_count}", f"--format={format_string}"
        ], cwd=path)
        
        if not result["success"]:
            return []
        
        commits = []
        lines = result["stdout"].split('\n') if result["stdout"] else []
        
        for line in lines:
            if line and '|' in line:
                parts = line.split('|', 4)
                if len(parts) == 5:
                    commits.append({
                        "hash": parts[0][:7],  # Short hash
                        "full_hash": parts[0],
                        "author": parts[1],
                        "email": parts[2],
                        "date": parts[3],
                        "message": parts[4]
                    })
        
        return commits
    
    def create_branch(self, branch_name: str, path: str = None) -> Dict[str, Any]:
        """Create a new branch"""
        if not self.is_git_repository(path):
            return {"error": "Not a git repository"}
        
        result = self._run_git_command(["checkout", "-b", branch_name], cwd=path)
        return result
    
    def get_branches(self, path: str = None) -> List[Dict[str, str]]:
        """Get all branches"""
        if not self.is_git_repository(path):
            return []
        
        result = self._run_git_command(["branch", "-a"], cwd=path)
        if not result["success"]:
            return []
        
        branches = []
        lines = result["stdout"].split('\n') if result["stdout"] else []
        
        for line in lines:
            line = line.strip()
            if line:
                is_current = line.startswith('*')
                name = line[2:] if is_current else line
                branches.append({
                    "name": name,
                    "is_current": is_current,
                    "is_remote": name.startswith('remotes/')
                })
        
        return branches
    
    def get_diff(self, path: str = None, staged: bool = False) -> str:
        """Get git diff"""
        if not self.is_git_repository(path):
            return "Not a git repository"
        
        cmd = ["diff"]
        if staged:
            cmd.append("--cached")
        
        result = self._run_git_command(cmd, cwd=path)
        return result["stdout"] if result["success"] else result["stderr"]
    
    def clone_repository(self, url: str, directory: str = None) -> Dict[str, Any]:
        """Clone a git repository"""
        cmd = ["clone", url]
        if directory:
            cmd.append(directory)
        
        result = self._run_git_command(cmd)
        return result
    
    def init_repository(self, path: str = None) -> Dict[str, Any]:
        """Initialize a new git repository"""
        result = self._run_git_command(["init"], cwd=path)
        return result

# Global git service instance
_git_service = GitService()

def get_git_service() -> GitService:
    """Get the global git service instance"""
    return _git_service

def register_git_service():
    """Register the git service with MCP"""
    service_manager = get_service_manager()
    
    return service_manager.register_custom_service(
        name="git_service",
        description="Git version control operations including status, commit, push, pull, branch management, and more",
        capabilities=[
            "status", "commit", "push", "pull", "branch", "log",
            "diff", "add", "reset", "clone", "init", "repository_management"
        ],
        metadata={
            "type": "builtin",
            "priority": "high",
            "category": "version_control"
        }
    )

if __name__ == "__main__":
    # Test the git service
    print("Testing git service registration...")
    success = register_git_service()
    print(f"Git service registration: {'SUCCESS' if success else 'FAILED'}")
    
    git_service = get_git_service()
    
    if git_service.is_git_repository():
        print("Current directory is a git repository")
        status = git_service.get_status()
        print(f"Current branch: {status.get('branch', 'unknown')}")
        print(f"Repository clean: {status.get('is_clean', False)}")
    else:
        print("Current directory is not a git repository")