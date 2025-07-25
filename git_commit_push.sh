#\!/bin/bash

# MCP项目Git提交和推送脚本
# 执行前请确保已安装git并配置了SSH key

echo "🚀 开始提交MCP项目最新代码..."

# 检查git状态
echo "📊 当前git状态:"
git status

# 添加所有变更
echo "📥 添加文件到暂存区..."
git add .

# 提交更改
echo "📝 提交更改..."
git commit -m "feat: 添加完整的MCP文件操作服务套件

- 新增 file_reader.py: 安全的文件读取服务，支持编码检测
- 新增 file_writer.py: 安全的文件写入、编辑和创建服务  
- 新增 directory_lister.py: 安全的目录浏览和文件信息获取服务
- 更新 .gitignore: 添加Python项目标准忽略规则
- 所有服务都集成MCP服务发现机制，支持安全路径验证

这些服务提供了完整的文件系统操作能力，同时确保安全性：
- 防止路径遍历攻击
- 文件大小限制
- 编码自动检测
- 权限检查"

# 推送到远程仓库
echo "🌐 推送到远程仓库..."
git push origin MCP

# 显示最新状态
echo "✅ 推送完成！"
echo "📈 最新提交记录:"
git log --oneline -5

echo "🎉 所有更改已成功提交并推送到远程仓库！"
