# MemoryChain - 智能记忆链插件

[![AstrBot Plugin](https://img.shields.io/badge/AstrBot-Plugin-blue.svg)]()
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)]()

## 📖 简介

MemoryChain 是一个基于 AstrBot 框架的智能记忆链插件，用于管理聊天历史记录的压缩、存储和检索。通过动态压缩长对话历史，将重要信息保存到向量数据库中，实现持久的上下文记忆功能。

## ✨ 特性

- **智能对话压缩**：自动压缩长对话历史，提取关键信息
- **向量存储支持**：将压缩后的记忆存入向量数据库
- **多会话管理**：支持群聊和私聊的独立记忆管理
- **知识库集成**：与 AstrBot 知识库系统深度集成
- **持久化存储**：配置信息自动保存，重启后恢复
- **动态配置**：支持运行时配置调整

## 🔧 安装

1. 确保已安装 AstrBot 框架
2. 将插件文件放入 AstrBot 的插件目录
3. 重启 AstrBot 服务

## ⚙️ 配置

在插件配置文件中添加以下配置项：

```yaml
memorychain:
  enabled: 1  # 是否启用插件（1启用，0禁用）
  max_history: 60  # 最大保留消息数
  compress_threshold: 50  # 压缩阈值（达到多少条消息后压缩）
  chunk_size: 512  # 文本分块大小
  chunk_overlap: 50  # 文本分块重叠大小
  batch_size: 32  # 批量处理大小
  tasks_limit: 3  # 并发任务限制
  max_retries: 3  # 最大重试次数
```

## 📚 命令列表

### 基本设置
- `memorychain sbn <sender_id> <bot_name>` - 为指定ID设置bot名称
- `memorychain sbnf <bot_name>` - 为当前会话设置bot名称
- `memorychain sllm <llm_name>` - 设置上下文压缩使用的LLM
- `memorychain llm` - 获取所有可用的LLM提供商
- `memorychain sep <ep_name>` - 设置Embedding Provider
- `memorychain kbep` - 获取所有可用的Embedding Provider

### 知识库管理
- `memorychain kbn` - 获取所有数据库
- `memorychain kbnep` - 获取所有数据库及其对应的编码器
- `memorychain kbco <kb_name>` - 统计数据库的文档数量
- `memorychain kbcr <kb_name> <ep_names>` - 创建数据库
- `memorychain kbcr_cs <kb_name>` - 创建数据库（测试版）
- `memorychain kbdb` - 获取所有kb_db里面的数据库
- `memorychain dkbdb <db_name>` - 删除kb_db数据库
- `memorychain dkb <kb_name>` - 直接清理知识库
- `memorychain reloadkbs` - 重新加载所有数据库

## 🔍 工作原理

### 1. 对话管理
- 监控LLM请求和响应
- 按会话（群聊/私聊）分别管理对话历史
- 使用滚动窗口保留最近N条消息

### 2. 智能压缩
- 当对话达到压缩阈值时，触发压缩
- 调用配置的LLM生成对话摘要
- 清除已压缩的原始消息，保留摘要

### 3. 记忆存储
- 将压缩后的摘要存入向量数据库
- 按日期和会话类型组织存储
- 支持后续的语义检索

### 4. 上下文增强
- 在LLM请求前检索相关记忆
- 将相关记忆作为上下文提示加入请求
- 提升对话的连续性和相关性

## 🗂️ 数据结构

### 持久化数据 (`memorychain_data.json`)
```json
{
  "bot_name": {
    "123456": "助手",
    "789012": "小助手"
  },
  "llm_name": "gpt-3.5-turbo",
  "ep_name": "text-embedding-ada-002",
  "last_updated": 1672531200
}
```

### 数据库命名规则
- 群聊记忆：`群{group_id}记忆链`
- 私聊记忆：`私聊{user_id}记忆链`
- 文件命名：`群{group_id}_{YYYY年MM月DD日}.txt`

## 🔄 工作流程

```
用户消息 → 添加到对话历史 → 检查压缩阈值 → 触发压缩
     ↓                             ↓
调用LLM ← 添加相关记忆 ← 检索向量库 ← 存储压缩摘要
     ↓
返回响应 → 添加到助手历史 → 检查压缩阈值 → ...
```

## 📊 性能优化

### 配置建议
- **压缩阈值**：根据对话频率调整，高频对话可适当提高
- **分块大小**：根据Embedding模型限制调整
- **批量大小**：根据系统性能调整，提升处理效率

### 内存管理
- 定期清理内存中的对话历史
- 使用LRU策略管理活跃会话
- 异步保存持久化数据

## 🚨 注意事项

1. **LLM配置**：必须正确配置LLM才能使用压缩功能
2. **Embedding Provider**：确保至少有一个可用的Embedding Provider
3. **存储空间**：定期清理不需要的记忆数据库
4. **隐私保护**：敏感对话请谨慎启用记忆功能

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进这个项目。

## 📧 联系

- 作者：Lishining
- 版本：1.0.0
- 插件ID：memorychain

---

**让对话拥有记忆，让智能更加持久**