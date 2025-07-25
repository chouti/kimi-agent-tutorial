# Kimi Agent Tutorial / Kimi 智能体教程

一个教授如何构建 Kimi AI 智能体的教程项目，展示了如何创建具有文件操作能力的 AI 助手。

A tutorial project that teaches how to build Kimi AI agents, demonstrating how to create AI assistants with file operation capabilities.

## 项目概述 / Project Overview

这个项目展示了如何使用 Moonshot AI (Kimi) 的 API 来构建一个功能完整的智能体，该智能体能够：

This project demonstrates how to use Moonshot AI (Kimi) API to build a fully functional agent that can:

- 📁 读取文件内容 / Read file contents
- 📋 列出目录文件 / List directory files  
- ✏️ 编辑和创建文件 / Edit and create files
- 🤖 与用户进行自然语言交互 / Interact with users in natural language

## 文件说明 / File Description

### 核心文件 / Core Files

- **`main.py`** - 主要的 Kimi 智能体实现，包含文件操作工具和对话循环
  - Main Kimi agent implementation with file operation tools and conversation loop
  
- **`congrats.js`** - ROT13 解码演示脚本，解码隐藏的祝贺消息
  - ROT13 decoder demo script that reveals a hidden congratulations message
  
- **`fizzbuzz.js`** - 经典的 FizzBuzz 程序实现
  - Classic FizzBuzz program implementation
  
- **`riddle.txt`** - 包含一个有趣的谜语
  - Contains an interesting riddle

### 配置文件 / Configuration Files

- **`.github/workflows/`** - GitHub Actions 工作流，包含 Claude 代码审查集成
  - GitHub Actions workflows including Claude code review integration

## 快速开始 / Quick Start

### 环境要求 / Prerequisites

- Python 3.7+
- Node.js (用于运行 JavaScript 演示 / for JavaScript demos)
- Moonshot AI API 密钥 / Moonshot AI API key

### 安装步骤 / Installation

1. **克隆仓库 / Clone the repository**
   ```bash
   git clone https://github.com/chouti/kimi-agent-tutorial.git
   cd kimi-agent-tutorial
   ```

2. **安装 Python 依赖 / Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   或者手动安装 / Or install manually:
   ```bash
   pip install openai pydantic
   ```

3. **设置环境变量 / Set environment variables**
   ```bash
   export MOONSHOT_API_KEY="your_moonshot_api_key"
   export MOONSHOT_API_BASE="https://api.moonshot.cn/v1"
   ```

### 使用方法 / Usage

#### 运行 Kimi 智能体 / Run Kimi Agent

```bash
python main.py
```

启动后，你可以：
- 询问文件内容
- 请求编辑文件
- 探索项目结构
- 与智能体进行自然语言对话

After starting, you can:
- Ask about file contents
- Request file edits
- Explore project structure  
- Have natural language conversations with the agent

#### 运行演示脚本 / Run Demo Scripts

**ROT13 解码器 / ROT13 Decoder:**
```bash
node congrats.js
```

**FizzBuzz 程序 / FizzBuzz Program:**
```bash
node fizzbuzz.js
```

## 功能特性 / Features

### 🔧 智能体工具 / Agent Tools

1. **read_file** - 读取指定路径的文件内容
   - Read content from a specified file path

2. **list_files** - 列出目录中的所有文件和子目录
   - List all files and subdirectories in a directory

3. **edit_file** - 编辑现有文件或创建新文件
   - Edit existing files or create new files

### 🤖 智能对话 / Intelligent Conversation

智能体能够：
- 自动理解用户意图
- 主动使用工具获取信息
- 提供详细的文件分析和建议
- 支持中文和英文交互

The agent can:
- Automatically understand user intent
- Proactively use tools to gather information
- Provide detailed file analysis and suggestions
- Support both Chinese and English interactions

## 项目结构 / Project Structure

```
kimi-agent-tutorial/
├── main.py              # Kimi 智能体主程序
├── congrats.js          # ROT13 解码演示
├── fizzbuzz.js          # FizzBuzz 演示程序
├── riddle.txt           # 谜语文件
├── requirements.txt     # Python 依赖列表
├── README.md           # 项目说明文档
└── .github/
    └── workflows/       # GitHub Actions 配置
```

## 技术栈 / Tech Stack

- **Python** - 主要编程语言 / Main programming language
- **OpenAI API** - 通过 Moonshot 兼容接口 / Via Moonshot compatible interface
- **Pydantic** - 数据验证和设置管理 / Data validation and settings management
- **JavaScript** - 演示脚本 / Demo scripts
- **GitHub Actions** - CI/CD 和代码审查 / CI/CD and code review

## 贡献指南 / Contributing

欢迎提交 Issue 和 Pull Request！请确保：
- 代码符合项目风格
- 添加适当的注释
- 测试新功能

Welcome to submit Issues and Pull Requests! Please ensure:
- Code follows project style
- Add appropriate comments
- Test new features

## 许可证 / License

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 致谢 / Acknowledgments

- [Moonshot AI](https://moonshot.cn/) - 提供强大的 AI 能力
- 所有为这个项目做出贡献的开发者

- [Moonshot AI](https://moonshot.cn/) - For providing powerful AI capabilities
- All developers who contributed to this project