"""
Refactored Kimi Agent - Business Logic Focus
Uses MCP service discovery for all tool operations
"""

import os
import json
import logging
from typing import Dict, Any, Optional

from mcp_service_discovery import get_service_manager, ServiceInfo

# Configure logging for refactored_agent
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Handle OpenAI import gracefully
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI not available, using mock client")
    OPENAI_AVAILABLE = False

class BusinessLogicAgent:
    """
    Refactored agent that focuses on business logic while using MCP for service discovery
    """
    
    def __init__(self):
        if OPENAI_AVAILABLE:
            self.client = openai.OpenAI(
                api_key=os.environ.get("MOONSHOT_API_KEY"),
                base_url=os.environ.get("MOONSHOT_API_BASE"),
            )
            self.model_name = "kimi-k2-0711-preview"
        else:
            self.client = None
            self.model_name = "mock-model"
        
        self.service_manager = get_service_manager()
        self.conversation_history = [
            {
                "role": "system", 
                "content": "你是一个自动助手，当用户询问文件或目录信息时，你应该主动使用可用的工具来获取信息，然后直接回答用户的问题。如果用户询问文件概况，你应该：1) 使用list_files列出目录内容 2) 对找到的Python文件使用read_file读取内容 3) 根据读取的内容直接回答用户的问题，整个流程自动完成，不要中断用户等待确认。"
            }
        ]
    
    def _get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get available tools from MCP service discovery"""
        tools = {}
        
        # Map service capabilities to tool definitions matching original format
        tool_definitions = [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Reads the content of a file at the given path.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "The relative path of the file to read."
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "Lists all files and directories in a given path.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "The directory path to list files from."
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "Edits a file by replacing old_content with new_content. If old_content is empty, it creates a new file or appends.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "The path to the file."
                            },
                            "old_content": {
                                "type": "string",
                                "description": "The exact content to be replaced. Use an empty string to create a new file or append."
                            },
                            "new_content": {
                                "type": "string",
                                "description": "The new content to replace the old content."
                            }
                        },
                        "required": ["path", "old_content", "new_content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "git_status",
                    "description": "Get the current git repository status including branch, changes, and staged files.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        ]
        
        # Check which services are available via MCP
        service_mapping = {
            "read_file": "file_reader",
            "list_files": "directory_lister", 
            "edit_file": "file_writer",
            "git_status": "git_service"
        }
        
        available_tools = []
        for tool_def in tool_definitions:
            tool_name = tool_def["function"]["name"]
            service_name = service_mapping.get(tool_name)
            if service_name:
                service = self.service_manager.get_service(service_name)
                if service:
                    available_tools.append(tool_def)
        
        return available_tools
    
    def _execute_tool_via_mcp(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Execute a tool operation via MCP service discovery"""
        try:
            # Map tool names to MCP service names and import actual service instances
            service_mapping = {
                "read_file": ("file_reader", "file_reader"),
                "edit_file": ("file_writer", "file_writer"), 
                "list_files": ("directory_lister", "directory_lister"),
                "git_status": ("git_service", "git_service")
            }
            
            service_info = service_mapping.get(tool_name)
            if not service_info:
                return f"Unknown tool: {tool_name}"
            
            service_name, service_module = service_info
            
            # Check if service is available via MCP
            service = self.service_manager.get_service(service_name)
            if not service:
                return f"Service {service_name} not available"
            
            # Map parameters for different tool types
            mapped_params = self._map_tool_parameters(tool_name, parameters)
            
            # Import and use actual service instances
            try:
                if tool_name == "read_file":
                    from file_reader import get_file_reader
                    return get_file_reader().read_file(mapped_params.get('path', ''))
                elif tool_name == "edit_file":
                    from file_writer import get_file_writer
                    service = get_file_writer()
                    if mapped_params.get('old_content'):
                        return service.edit_file(
                            mapped_params.get('path', ''),
                            mapped_params.get('old_content', ''),
                            mapped_params.get('content', '')
                        )
                    else:
                        return service.write_file(
                            mapped_params.get('path', ''),
                            mapped_params.get('content', ''),
                            mapped_params.get('mode', 'write')
                        )
                elif tool_name == "list_files":
                    from directory_lister import get_directory_lister
                    return get_directory_lister().list_directory(mapped_params.get('path', '.'))
                elif tool_name == "git_status":
                    from git_service import get_git_service
                    return get_git_service().get_status()
                else:
                    # Fallback to generic execute method on service instance
                    return str(service.execute(mapped_params))
                    
            except ImportError as e:
                # Fallback to service.execute if direct import fails
                logger.warning(f"Direct import failed, falling back to service.execute: {e}")
                return str(service.execute(mapped_params))
                
        except Exception as e:
            return f"Error executing tool '{tool_name}' via MCP: {str(e)}"
    
    def _map_tool_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Map tool parameters to MCP service format"""
        if tool_name == "read_file":
            return {"path": parameters.get("path", "")}
        elif tool_name == "edit_file":
            return {
                "path": parameters.get("path", ""),
                "content": parameters.get("new_content", parameters.get("content", "")),
                "old_content": parameters.get("old_content", ""),
                "mode": "replace" if parameters.get("old_content") else "write"
            }
        elif tool_name == "list_files":
            return {"path": parameters.get("path", ".")}
        elif tool_name == "git_status":
            return {}
        return parameters
    
    def _get_tool_definitions_for_llm(self) -> list:
        """Get tool definitions formatted for LLM consumption"""
        return self._get_available_tools()
    
    def _mock_llm_response(self, messages: list, tools: list) -> object:
        """Mock LLM response when OpenAI not available"""
        class MockResponse:
            def __init__(self):
                self.choices = [MockChoice()]
        
        class MockChoice:
            def __init__(self):
                self.message = MockMessage()
        
        class MockMessage:
            def __init__(self):
                self.content = "OpenAI API not available. Please install openai package and set MOONSHOT_API_KEY."
                self.tool_calls = []
        
        return MockResponse()
    
    def _mock_client(self):
        """Mock OpenAI client for testing"""
        class MockClient:
            def __init__(self):
                pass
            
            def chat_completions_create(self, **kwargs):
                return self._mock_llm_response(kwargs.get('messages', []), kwargs.get('tools', []))
        
        return MockClient()
    
    def process_user_input(self, user_input: str) -> str:
        """Process user input using business logic and MCP services"""
        
        # Add user message to conversation
        self.conversation_history.append({"role": "user", "content": user_input})
        
        try:
            # Get available tools
            tools = self._get_tool_definitions_for_llm()
            
            # Call LLM with tools or use mock
            if self.client:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=self.conversation_history,
                    tools=tools,
                    tool_choice="auto"
                )
            else:
                response = self._mock_llm_response(self.conversation_history, tools)
            
            response_message = response.choices[0].message
            self.conversation_history.append(response_message)
            
            # Process tool calls iteratively with safety limits
            max_iterations = 10
            iteration_count = 0
            current_message = response_message
            
            while iteration_count < max_iterations:
                if current_message.tool_calls:
                    # Process all tool calls in this iteration
                    tool_results = []
                    for tool_call in current_message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        print(f"🤖 Kimi wants to use tool: {tool_name}({json.dumps(tool_args, indent=2)})")
                        
                        # Execute via MCP
                        try:
                            tool_result = self._execute_tool_via_mcp(tool_name, tool_args)
                            tool_results.append({
                                "tool_call_id": tool_call.id,
                                "tool_name": tool_name,
                                "result": tool_result
                            })
                        except Exception as e:
                            tool_results.append({
                                "tool_call_id": tool_call.id,
                                "tool_name": tool_name,
                                "result": f"Error: {str(e)}"
                            })
                    
                    # Add all tool results to conversation
                    for result in tool_results:
                        self.conversation_history.append({
                            "role": "tool",
                            "tool_call_id": result["tool_call_id"],
                            "content": str(result["result"])
                        })
                    
                    iteration_count += 1
                    if iteration_count >= max_iterations:
                        return "抱歉，处理请求时达到最大工具调用次数限制。让我直接为您提供已收集的信息：\n\n" + self._summarize_current_state()
                    
                    # Get next response after tool execution
                    try:
                        if self.client:
                            next_response = self.client.chat.completions.create(
                                model=self.model_name,
                                messages=self.conversation_history,
                                tools=tools,
                                tool_choice="auto"
                            )
                        else:
                            next_response = self._mock_llm_response(self.conversation_history, tools)
                        
                        current_message = next_response.choices[0].message
                        self.conversation_history.append(current_message)
                        
                        # If no more tool calls, break the loop
                        if not current_message.tool_calls:
                            break
                            
                    except Exception as e:
                        return f"处理请求时发生错误: {str(e)}"
                        
                else:
                    # No more tool calls, return final response
                    break
                    
            return current_message.content or "处理完成，但没有生成回复"
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about available MCP services"""
        services = self.service_manager.discovery.list_services()
        return {
            "total_services": len(services),
            "services": [{"name": s.name, "description": s.description, "capabilities": s.capabilities} 
                        for s in services]
        }
    
    def _summarize_current_state(self) -> str:
        """Summarize current conversation state when max iterations reached"""
        recent_messages = self.conversation_history[-5:]  # Last 5 messages
        summary = []
        
        for msg in recent_messages:
            # Handle both dict and ChatCompletionMessage objects
            if hasattr(msg, 'role'):
                role = msg.role
                content = str(getattr(msg, 'content', ''))
            else:
                role = msg.get("role", "")
                content = str(msg.get("content", ""))
                
            if role == "tool":
                # Truncate long content
                if len(content) > 200:
                    content = content[:200] + "..."
                summary.append(f"工具结果: {content}")
            elif role == "assistant" and content:
                summary.append(f"助手回复: {content}")
        
        return "\n".join(summary) if summary else "已收集一些信息但无法总结"
    
    def run_interactive(self):
        """Run the agent in interactive mode"""
        print("🤖 Chat with Kimi (MCP-powered)")
        print("Type 'quit' to exit, 'services' to see available services")
        
        while True:
            try:
                user_input = input("\n🙂 You: ").strip()
                
                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'services':
                    service_info = self.get_service_info()
                    print(f"\n📋 Available MCP Services:")
                    for service in service_info["services"]:
                        print(f"  • {service['name']}: {service['description']}")
                        print(f"    Capabilities: {', '.join(service['capabilities'])}")
                    continue
                
                response = self.process_user_input(user_input)
                print(f"\n🤖 Kimi: {response}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    agent = BusinessLogicAgent()
    agent.run_interactive()