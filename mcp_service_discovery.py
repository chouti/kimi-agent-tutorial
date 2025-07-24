"""
MCP-based service discovery layer for the Kimi agent.
This module handles service registration, discovery, and management via MCP.
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ServiceInfo:
    """Represents a registered service with MCP"""
    name: str
    description: str
    endpoint: str
    capabilities: List[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class MCPServiceDiscovery(ABC):
    """Abstract base class for MCP service discovery"""
    
    @abstractmethod
    def register_service(self, service: ServiceInfo) -> bool:
        """Register a service with MCP"""
        pass
    
    @abstractmethod
    def discover_service(self, name: str) -> Optional[ServiceInfo]:
        """Discover a service by name"""
        pass
    
    @abstractmethod
    def list_services(self) -> List[ServiceInfo]:
        """List all available services"""
        pass
    
    @abstractmethod
    def unregister_service(self, name: str) -> bool:
        """Unregister a service"""
        pass

class LocalMCPServiceDiscovery(MCPServiceDiscovery):
    """Local implementation of MCP service discovery using file-based registry"""
    
    def __init__(self, registry_file: str = ".mcp_registry.json"):
        self.registry_file = registry_file
        self._ensure_registry_exists()
    
    def _ensure_registry_exists(self):
        """Ensure the registry file exists"""
        if not os.path.exists(self.registry_file):
            with open(self.registry_file, 'w') as f:
                json.dump({}, f)
    
    def _load_registry(self) -> Dict[str, Dict[str, Any]]:
        """Load service registry from file"""
        try:
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_registry(self, registry: Dict[str, Dict[str, Any]]):
        """Save service registry to file"""
        with open(self.registry_file, 'w') as f:
            json.dump(registry, f, indent=2)
    
    def register_service(self, service: ServiceInfo) -> bool:
        """Register a service with MCP"""
        try:
            registry = self._load_registry()
            registry[service.name] = service.to_dict()
            self._save_registry(registry)
            logger.info(f"Service '{service.name}' registered successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to register service '{service.name}': {e}")
            return False
    
    def discover_service(self, name: str) -> Optional[ServiceInfo]:
        """Discover a service by name"""
        try:
            registry = self._load_registry()
            if name in registry:
                service_data = registry[name]
                return ServiceInfo(**service_data)
            return None
        except Exception as e:
            logger.error(f"Failed to discover service '{name}': {e}")
            return None
    
    def list_services(self) -> List[ServiceInfo]:
        """List all available services"""
        try:
            registry = self._load_registry()
            return [ServiceInfo(**service_data) for service_data in registry.values()]
        except Exception as e:
            logger.error(f"Failed to list services: {e}")
            return []
    
    def unregister_service(self, name: str) -> bool:
        """Unregister a service"""
        try:
            registry = self._load_registry()
            if name in registry:
                del registry[name]
                self._save_registry(registry)
                logger.info(f"Service '{name}' unregistered successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unregister service '{name}': {e}")
            return False

class MCPServiceManager:
    """Manages MCP services and provides service discovery functionality"""
    
    def __init__(self, discovery_backend: MCPServiceDiscovery = None):
        self.discovery = discovery_backend or LocalMCPServiceDiscovery()
        self._register_builtin_services()
    
    def _register_builtin_services(self):
        """Register built-in services for file operations"""
        builtin_services = [
            ServiceInfo(
                name="file_reader",
                description="Read file contents",
                endpoint="local",
                capabilities=["read", "text_processing"],
                metadata={"type": "builtin", "priority": "high"}
            ),
            ServiceInfo(
                name="file_writer",
                description="Write or edit file contents",
                endpoint="local",
                capabilities=["write", "edit", "create"],
                metadata={"type": "builtin", "priority": "high"}
            ),
            ServiceInfo(
                name="directory_lister",
                description="List directory contents",
                endpoint="local",
                capabilities=["list", "directory"],
                metadata={"type": "builtin", "priority": "high"}
            )
        ]
        
        for service in builtin_services:
            if not self.discovery.discover_service(service.name):
                self.discovery.register_service(service)
    
    def get_service(self, name: str) -> Optional[ServiceInfo]:
        """Get a service by name"""
        return self.discovery.discover_service(name)
    
    def get_services_by_capability(self, capability: str) -> List[ServiceInfo]:
        """Get all services that support a specific capability"""
        services = self.discovery.list_services()
        return [s for s in services if capability in s.capabilities]
    
    def register_custom_service(self, name: str, description: str, 
                              capabilities: List[str], metadata: Dict[str, Any] = None) -> bool:
        """Register a custom service"""
        service = ServiceInfo(
            name=name,
            description=description,
            endpoint="custom",
            capabilities=capabilities,
            metadata=metadata or {}
        )
        return self.discovery.register_service(service)

# Global service manager instance
_service_manager = None

def get_service_manager() -> MCPServiceManager:
    """Get the global service manager instance"""
    global _service_manager
    if _service_manager is None:
        _service_manager = MCPServiceManager()
    return _service_manager