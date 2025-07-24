# main.py
import openai
import os
import json
from pydantic import BaseModel, Field

# 1. 定义工具的输入格式
class ReadFileParams(BaseModel):
    path: str = Field(..., description="The relative path of the file to read.")

# 2. 定义工具执行函数
def read_file(params: ReadFileParams) -> str:
    """Reads the content of a file at the given path."""
    try:
        with open(params.path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"
    
class ListFilesParams(BaseModel):
    path: str = Field(default=".", description="The directory path to list files from.")

def list_files(params: ListFilesParams) -> str:
    """Lists all files and directories in a given path."""
    try:
        return "\n".join(os.listdir(params.path))
    except Exception as e:
        return f"Error listing files: {e}"
    
class EditFileParams(BaseModel):
    path: str = Field(..., description="The path to the file.")
    old_content: str = Field(..., description="The exact content to be replaced. Use an empty string to create a new file or append.")
    new_content: str = Field(..., description="The new content to replace the old content.")

def edit_file(params: EditFileParams) -> str:
    """Edits a file by replacing old_content with new_content. If old_content is empty, it creates a new file or appends."""
    try:
        # 如果文件不存在且old_content为空，则创建新文件
        if not os.path.exists(params.path) and params.old_content == "":
            with open(params.path, 'w', encoding='utf-8') as f:
                f.write(params.new_content)
            return "File created successfully."

        with open(params.path, 'r+', encoding='utf-8') as f:
            content = f.read()
            if params.old_content != "" and params.old_content not in content:
                return f"Error: old_content not found in the file."
            
            new_file_content = content.replace(params.old_content, params.new_content)
            f.seek(0)
            f.write(new_file_content)
            f.truncate()
            return "File edited successfully."

    except Exception as e:
        return f"Error editing file: {e}"

class KimiAgent:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.environ.get("MOONSHOT_API_KEY"),
            base_url=os.environ.get("MOONSHOT_API_BASE"),
        )
        self.conversation_history = [
            {"role": "system", "content": "你是一个自动助手，当用户询问文件或目录信息时，你应该主动使用可用的工具来获取信息，然后直接回答用户的问题。如果用户询问文件概况，你应该：1) 使用list_files列出目录内容 2) 对找到的Python文件使用read_file读取内容 3) 根据读取的内容直接回答用户的问题，整个流程自动完成，不要中断用户等待确认。"}
        ]
        self.model_name = "kimi-k2-0711-preview"
        # 将工具注册到Agent中
        self.tools = {
            "read_file": {
                "function": read_file,
                "pydantic_model": ReadFileParams
            },
            "list_files": {
                "function": list_files,
                "pydantic_model": ListFilesParams
            },
            "edit_file": {
                "function": edit_file,
                "pydantic_model": EditFileParams
            }
        }

    def _get_tool_definitions(self):
        # 这一步是将我们的Python工具函数，转换成AI能理解的JSON格式
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool["function"].__doc__,
                    "parameters": tool["pydantic_model"].model_json_schema()
                }
            } for name, tool in self.tools.items()
        ]

    def run(self):
        print("🤖 Chat with Kimi (type 'quit' to exit)")
        while True:
            user_input = input("🙂 You: ")
            if user_input.lower() == 'quit':
                break

            self.conversation_history.append({"role": "user", "content": user_input})
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=self.conversation_history,
                tools=self._get_tool_definitions(),
                tool_choice="auto"
            )

            response_message = response.choices[0].message
            self.conversation_history.append(response_message)

            # 循环处理工具调用，直到没有更多工具调用
            current_message = response_message
            while True:
                if current_message.tool_calls:
                    # 处理所有工具调用
                    for tool_call in current_message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)

                        print(f"🤖 Kimi wants to use tool: {tool_name}({json.dumps(tool_args, indent=2)})")
                        # 自动执行工具，无需用户确认
                        if tool_name in self.tools:
                            # 1. 找到对应的工具函数
                            tool_function = self.tools[tool_name]["function"]
                            # 2. 验证并解析输入参数
                            pydantic_model = self.tools[tool_name]["pydantic_model"]
                            try:
                                validated_input = pydantic_model(**tool_args)
                                # 3. 执行工具
                                tool_result = tool_function(validated_input)
                            except Exception as e:
                                tool_result = f"Validation Error: {e}"
                            
                            # 4. 把工具执行结果告诉Kimi
                            self.conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": str(tool_result),
                            })
                        else:
                            print(f"Tool {tool_name} not found!")
                    
                    # 再次调用Kimi，让它根据所有工具结果进行下一步思考，启用工具调用
                    next_response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=self.conversation_history,
                        tools=self._get_tool_definitions(),
                        tool_choice="auto"
                    )
                    current_message = next_response.choices[0].message
                    self.conversation_history.append(current_message)
                    
                else:
                    # 没有更多工具调用，输出最终回复
                    print(f"🤖 Kimi: {current_message.content}")
                    break

if __name__ == "__main__":
    agent = KimiAgent()
    agent.run()