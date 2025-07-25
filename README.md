# Kimi Agent - MCP服务化重构版本

一个基于MCP（Model Context Protocol）服务发现架构重构的Kimi AI Agent，实现业务逻辑与服务管理的完全解耦。

## 🎯 项目最新进展

### ✅ 已实现的核心功能
- **MCP服务发现系统** - 完整的服务注册与发现机制
- **Git版本控制服务** - 新增git_service，支持完整的Git操作
- **模块化架构** - 业务逻辑与服务操作完全分离
- **动态服务加载** - 运行时服务发现，无需重启Agent

### 🆕 新增MCP服务
1. **git_service** - Git版本控制操作
   - ✅ 仓库状态检查
   - ✅ 文件提交管理
   - ✅ 分支操作
   - ✅ 远程推送/拉取
   - ✅ 日志查看
   - ✅ 差异比较

2. **shell_executor** - 安全shell执行
   - ✅ 智能LLM安全分析
   - ✅ 多层级安全策略
   - ✅ 风险评分和解释
   - ✅ 安全替代方案推荐
   - ✅ 系统信息获取
   - ✅ 文件和目录操作

3. **内置基础服务**
   - ✅ file_reader - 文件读取
   - ✅ file_writer - 文件写入/编辑
   - ✅ directory_lister - 目录列表

## 🏗️ 架构设计

### 原始架构 vs MCP架构对比

| 特性 | 原始架构 | MCP架构 |
|---|---|---|
| 服务管理 | 硬编码，单体应用 | 动态发现，服务注册 |
| 扩展性 | 需要修改核心代码 | 插件式服务添加 |
| 维护性 | 高耦合，难测试 | 低耦合，独立测试 |
| 运行时 | 静态工具集 | 动态服务发现 |

### 📁 核心文件结构
```
kimi-agent/
├── 📄 main.py                    # 原始单体版本（保留兼容）
├── 📄 refactored_agent.py        # MCP重构版本
├── 📄 mcp_service_discovery.py   # MCP服务发现核心
├── 📄 git_service.py             # Git版本控制服务
├── 📄 shell_executor.py          # 安全shell执行服务
├── 📄 llm_security_analyzer.py   # LLM安全分析器
├── 📄 .mcp_registry.json         # 服务注册表
└── 📄 requirements.txt           # 依赖管理
```

## 🚀 快速开始

### 环境准备
```bash
# 安装依赖
pip install -r requirements.txt
pip install aiohttp  # LLM安全分析需要

# 设置环境变量
export MOONSHOT_API_KEY="你的API密钥"
export MOONSHOT_API_BASE="https://api.moonshot.cn/v1"
```

### 运行方式
```bash
# 方式1：使用MCP重构版本（推荐）
python refactored_agent.py

# 方式2：使用原始版本（兼容）
python main.py
```

### 🎯 交互命令
- `quit` - 退出Agent
- `services` - 查看可用MCP服务列表
- 直接对话 - Agent会自动选择合适的服务

## 🔧 开发指南

### 添加新MCP服务
```python
from mcp_service_discovery import get_service_manager

# 注册自定义服务
manager = get_service_manager()
manager.register_custom_service(
    name="your_service",
    description="你的服务描述",
    capabilities=["capability1", "capability2"],
    metadata={"version": "1.0", "author": "你的名字"}
)
```

### 服务发现示例
```python
# 获取所有服务
manager = get_service_manager()
services = manager.discovery.list_services()

# 按能力查找服务
git_services = manager.get_services_by_capability("commit")
shell_services = manager.get_services_by_capability("execute")
```

## 🧪 实际使用示例

### Git操作示例
```python
from git_service import get_git_service

git = get_git_service()

# 检查状态
status = git.get_status()
print(f"当前分支: {status['branch']}")

# 提交变更
git.add_files()
git.commit_changes("feat: 新增功能描述")
git.push_changes()
```

### Shell安全执行示例
```python
from shell_executor import ShellExecutor

# 创建支持LLM的shell执行器
executor = ShellExecutor(enable_llm_security=True)

# 分析命令安全性
analysis = executor.analyze_command_security("rm -rf /tmp/test")
print(f"安全等级: {analysis['final_security_level']}")
print(f"风险评分: {analysis['risk_score']}")

# 执行安全命令
result = executor.execute_command("ls -la")
print(f"执行结果: {result.status.value}")

# 获取系统信息
info = executor.get_system_info()
print(f"系统: {info['os'][:50]}...")
```

### 服务列表查看
```bash
$ python -c "from mcp_service_discovery import get_service_manager; [print(f'{s.name}: {s.description}') for s in get_service_manager().discovery.list_services()]"

file_reader: Read file contents
file_writer: Write or edit file contents
directory_lister: List directory contents
git_service: Git版本控制操作包括状态、提交、推送、拉取、分支管理等
shell_executor: 安全shell执行包括LLM智能安全分析、风险评分、系统信息获取等
```

## 🎨 架构优势

### 1. 服务解耦
- 每个服务独立运行
- 可单独更新和测试
- 互不影响

### 2. 动态扩展
- 新服务无需重启Agent
- 基于能力的服务发现
- 支持多种后端存储

### 3. 易于维护
- 清晰的职责分离
- 标准化服务接口
- 完善的错误处理

### 4. 云原生就绪
- 支持HTTP服务发现
- 适配微服务架构
- 容器化部署友好
- AI安全分析能力（LLM集成）

## 🛠️ 扩展计划

### 已添加的服务 ✅
- [x] **git_service** - Git版本控制
- [x] **shell_executor** - 安全shell执行（含LLM安全分析）

### 即将添加的服务
- [ ] **web_fetcher** - HTTP请求和网页抓取
- [ ] **code_analyzer** - 代码分析和语法检查
- [ ] **image_processor** - 图像处理和分析
- [ ] **config_manager** - 配置和环境管理

## 🔒 LLM安全分析特性

### 智能安全分析
- **大语言模型支持**: 集成Moonshot API进行智能命令分析
- **多维度风险评估**: 系统修改、数据破坏、权限提升、网络操作等
- **风险评分系统**: 0-100分量化风险等级
- **安全替代方案**: 为危险命令提供安全替代建议
- **上下文感知**: 基于工作环境智能判断命令安全性

### 使用示例
```bash
# 启用LLM安全分析
export MOONSHOT_API_KEY="your-api-key"

# 测试命令安全分析
python3 -c "
from shell_executor import ShellExecutor
executor = ShellExecutor(enable_llm_security=True)
analysis = executor.analyze_command_security('rm -rf /tmp/test')
print(f'安全等级: {analysis[\"final_security_level\"]}')
print(f'风险评分: {analysis[\"risk_score\"]}/100')
"
```

### 安全等级分类
- **SAFE**: 安全命令，直接执行
- **CAUTION**: 需要确认，低风险
- **DANGEROUS**: 高风险，需要明确确认
- **CRITICAL**: 极高风险，建议阻止
- **BLOCKED**: 危险命令，强制阻止

### 部署选项
- [ ] Docker容器化
- [ ] Kubernetes服务发现
- [ ] 云端服务注册
- [ ] 多环境配置管理

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 添加新的MCP服务
4. 测试服务注册和发现
5. 提交Pull Request

## 📄 许可证

MIT License - 详见LICENSE文件