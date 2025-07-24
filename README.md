# Kimi Agent - MCP Refactored

A refactored version of the Kimi AI agent that uses MCP (Model Context Protocol) for service discovery, separating business logic from service management.

## Architecture Overview

### Original Architecture
- Single monolithic agent with built-in file operations
- Hard-coded tool definitions and implementations
- Tightly coupled business logic and service operations

### Refactored Architecture
- **Business Logic Agent** (`refactored_agent.py`): Focuses on intelligent processing and decision making
- **MCP Service Discovery** (`mcp_service_discovery.py`): Handles service registration, discovery, and management
- **Modular Services**: Services are discovered and used dynamically via MCP

## Key Components

### 1. MCP Service Discovery (`mcp_service_discovery.py`)
- **Service Registration**: Dynamic service registration with metadata
- **Capability-based Discovery**: Find services by capabilities
- **Local File-based Registry**: Simple JSON-based service registry
- **Extensible Backend**: Support for different discovery backends

### 2. Business Logic Agent (`refactored_agent.py`)
- **Pure Business Logic**: Focuses on understanding user intent and orchestrating services
- **MCP Integration**: Uses MCP to discover and invoke services
- **Dynamic Tool Loading**: Tools are discovered at runtime via MCP
- **Clean Separation**: No direct file operations, all via MCP services

## Usage

### Running the Refactored Agent
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MOONSHOT_API_KEY="your-api-key"
export MOONSHOT_API_BASE="https://api.moonshot.cn/v1"

# Run the refactored agent
python refactored_agent.py
```

### Available Commands
- `quit`: Exit the agent
- `services`: List available MCP services
- Regular conversation: The agent will use appropriate services via MCP

### Service Management
The MCP service manager automatically registers built-in services:
- `file_reader`: Read file contents
- `file_writer`: Write/edit file contents  
- `directory_lister`: List directory contents

## Benefits of MCP Architecture

1. **Service Decoupling**: Services are independent and can be updated separately
2. **Dynamic Discovery**: New services can be added without agent restart
3. **Capability-based**: Services are discovered by what they can do, not just names
4. **Scalability**: Easy to add new service backends (HTTP, gRPC, etc.)
5. **Maintainability**: Clear separation of concerns
6. **Testability**: Services can be mocked and tested independently

## Extending the System

### Adding New Services
```python
from mcp_service_discovery import get_service_manager, ServiceInfo

# Register a new service
manager = get_service_manager()
manager.register_custom_service(
    name="my_custom_service",
    description="Does something useful",
    capabilities=["process", "transform"],
    metadata={"version": "1.0", "author": "you"}
)
```

### Adding New Backends
Extend `MCPServiceDiscovery` abstract class to implement different discovery backends:
- HTTP-based registry
- Database-backed registry
- Distributed service mesh
- Cloud provider service discovery

## Migration from Original

The original `main.py` is preserved. To use the new MCP-based agent:

1. **Original**: `python main.py` (monolithic, direct file operations)
2. **Refactored**: `python refactored_agent.py` (MCP-based, service discovery)

Both can coexist, allowing gradual migration.