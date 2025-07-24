"""
Refactored Kimi Agent - Business Logic Focus
Uses MCP service discovery for all tool operations
"""

import openai
import os
import json
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from mcp_service_discovery import get_service_manager, ServiceInfo

class BusinessLogicAgent:
    """
    Refactored agent that focuses on business logic while using MCP for service discovery
    """
    
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.environ.get("MOONSHOT_API_KEY"),
            base_url=os.environ.get("MOONSHOT_API_BASE"),
        )
        self.service_manager = get_service_manager()
        self.conversation_history = [
            {
                "role": "system", 
                "content": "你是一个自动助手，当用户询问文件或目录信息时，你应该主动使用可用的工具来获取信息，然后直接回答用户的问题。如果用户询问文件概况，你应该：1) 使用list_files列出目录内容 2) 对找到的Python文件使用read_file读取内容 3) 根据读取的内容直接回答用户的问题，整个流程自动完成，不要中断用户等待确认。"
            }
        ]
        self.model_name = "kimi-k2-0711-preview"
    
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
            }
        ]
        
        # Check which services are available via MCP
        service_mapping = {
            "read_file": "file_reader",
            "list_files": "directory_lister", 
            "edit_file": "file_writer"
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
            # Map tool names to operation handlers
            operation_mapping = {
                "read_file": self._read_file_operation,
                "edit_file": self._write_file_operation,
                "list_files": self._list_directory_operation
            }
            
            if tool_name in operation_mapping:
                return operation_mapping[tool_name](parameters)
            else:
                return f"Unknown tool: {tool_name}"
                
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"
    
    def _read_file_operation(self, parameters: Dict[str, Any]) -> str:
        """Read file operation via MCP"""
        try:
            file_path = parameters.get("path")
            if not file_path:
                return "Error: path parameter required"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"
    
    def _write_file_operation(self, parameters: Dict[str, Any]) -> str:
        """Write file operation via MCP"""
        try:
            file_path = parameters.get("path")
            content = parameters.get("content")
            mode = parameters.get("mode", "write")
            
            if not file_path or content is None:
                return "Error: path and content parameters required"
            
            if mode == "append":
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write(content)
                return "Content appended successfully"
            elif mode == "replace":
                old_content = parameters.get("old_content", "")
                if not os.path.exists(file_path):
                    return "Error: file does not exist"
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                
                if old_content and old_content not in existing_content:
                    return "Error: old content not found in file"
                
                new_content = existing_content.replace(old_content, content)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return "File content replaced successfully"
            else:  # write mode
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return "File written successfully"
                
        except Exception as e:
            return f"Error writing file: {e}"
    
    def _list_directory_operation(self, parameters: Dict[str, Any]) -> str:
        """List directory operation via MCP"""
        try:
            path = parameters.get("path", ".")
            items = os.listdir(path)
            return "\n".join(items)
        except Exception as e:
            return f"Error listing directory: {e}"
    
    def _get_tool_definitions_for_llm(self) -> list:
        """Get tool definitions formatted for LLM consumption"""
        return self._get_available_tools()
    
    def process_user_input(self, user_input: str) -> str:
        """Process user input using business logic and MCP services"""
        
        # Add user message to conversation
        self.conversation_history.append({"role": "user", "content": user_input})
        
        try:
            # Get available tools
            tools = self._get_tool_definitions_for_llm()
            
            # Call LLM with tools
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=self.conversation_history,
                tools=tools,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            self.conversation_history.append(response_message)
            
            # Process tool calls iteratively like original
            current_message = response_message
            while True:
                if current_message.tool_calls:
                    # Process all tool calls
                    for tool_call in current_message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        print(f"🤖 Kimi wants to use tool: {tool_name}({json.dumps(tool_args, indent=2)})")
                        
                        # Execute via MCP
                        tool_result = self._execute_tool_via_mcp(tool_name, tool_args)
                        
                        # Add tool result to conversation
                        self.conversation_history.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(tool_result)
                        })
                    
                    # Get next response after tool execution
                    next_response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=self.conversation_history,
                        tools=tools,
                        tool_choice="auto"
                    )
                    current_message = next_response.choices[0].message
                    self.conversation_history.append(current_message)
                    
                else:
                    # No more tool calls, return final response
                    return current_message.content or "I processed your request but have no response"
            
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