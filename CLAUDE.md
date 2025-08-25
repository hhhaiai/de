# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在处理此仓库代码时提供指导。

## 项目概述

这是一个名为 "ones" 的高性能 API 服务，为多个 AI 模型提供商提供代理层。该项目通过统一接口支持 OpenAI 和 Claude API 协议，具备智能模型路由和会话管理功能。

## 架构

### 核心组件

1. **API 服务器** (`more_core.py`): 基于 FastAPI 的服务器，使用 uvicorn 并支持自动工作进程扩展
2. **核心逻辑** (`degpt.py`): 处理模型集成、身份验证和响应处理
3. **Docker 支持** (`Dockerfile`): 使用 Python 3.11-slim-bullseye 的多阶段构建

### 主要特性

- **多协议支持**: 兼容 OpenAI 的 `/api/v1/chat/completions` 和 Claude 的 `/api/v1/messages` 端点
- **智能模型选择**: 基于成功率的自动模型路由，具备失败冷却机制
- **会话管理**: 内存中的会话存储，支持可配置超时（默认 30 分钟）
- **流式支持**: 为两种协议提供完整的流式响应处理
- **动态配置**: 通过环境变量进行路由配置，支持热重载
- **负载均衡**: 最优工作进程数计算（2×CPU 核心数 + 1，最大为 8）

## 开发命令

### 构建和运行
```bash
# 开发服务器（支持热重载）
python more_core.py

# 使用 Docker 进行生产构建
docker build --no-cache --compress -t de .
docker run -p 7860:7860 -m 2g -e DEBUG=false de

# 使用 --no-cache 进行 Docker 构建和运行
docker build --no-cache --compress -t de .
docker run -p 7860:7860 -m 2g -e DEBUG=false de
```

### API 测试
```bash
# OpenAI 协议（流式）
curl -X POST http://localhost:7860/api/v1/chat/completions \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H "Content-Type: application/json" \
  -d '{"model": "auto", "messages": [{"role": "user", "content": "Hello"}], "stream":true}'

# OpenAI 协议（非流式）
curl -X POST http://localhost:7860/api/v1/chat/completions \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H "Content-Type: application/json" \
  -d '{"model": "auto", "messages": [{"role": "user", "content": "Hello"}], "stream":false}'

# Claude 协议
curl -X POST http://localhost:7860/api/v1/messages \
  -H "x-api-key: ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model": "claude-opus-4-20250514", "max_tokens": 1000, "messages": [{"role": "user", "content": "Hello"}]}'

# 健康检查
curl http://localhost:7860/health
```

## 环境变量

### 核心配置
- `PORT`: 服务器端口（默认: 7860）
- `DEBUG`: 启用调试日志（默认: false）
- `TOKEN`: API 令牌用于身份验证（可选，设置后限制访问）

### 模型配置
- `REPLACE_CHAT`: 覆盖默认聊天完成端点，逗号分隔（以 / 开头）
- `PREFIX_CHAT`: 为默认端点添加前缀，逗号分隔（以 / 开头）
- `APPEND_CHAT`: 添加额外的聊天端点，逗号分隔（以 / 开头）

### DeGPT 配置
- `DEGPT_BASE_URL`: DeGPT API 基础 URL（默认: https://www.degpt.ai/api）
- `DEGPT_BASE_MODEL`: 后备模型（默认: gpt-4o-mini）
- `DEGPT_AUTH_ID`: 身份验证 ID（默认: b39fdee47a6bdbab5bc6827ac954c422）
- `DEGPT_AUTH_COOKIE`: 身份验证 Cookie
- `CACHE_DURATION`: 模型缓存持续时间，单位秒（默认: 3600）
- `SESSION_TIMEOUT`: 会话超时时间，单位秒（默认: 1800）
- `SESSION_STORAGE_TYPE`: 存储类型（memory 或 redis，默认: memory）

### 性能配置
- `DEGPT_PROXY_*`: 自定义代理头和用户代理

## 文件结构

```
├── more_core.py      # FastAPI 服务器，包含路由管理
├── degpt.py          # 模型集成和 API 调用的核心逻辑
├── Dockerfile        # 多阶段 Docker 构建配置
├── requirements.txt  # Python 依赖
├── README.md         # 中文文档，包含使用示例
└── CLAUDE.md         # 本文件（为 Claude Code 指导而添加）
```

## 模型路由逻辑

系统使用了复杂的模型选择算法：

1. **自动模式**: 当指定 "auto" 时，系统从历史数据中选择成功率最高的模型
2. **固定模型**: 特定模型名称会与可用模型进行验证，如果不可用则自动回退到 "auto"
3. **失败冷却**: 最近失败的模型会被临时排除（默认 5 分钟冷却）
4. **性能跟踪**: 所有模型调用都会被跟踪，记录成功/失败统计信息

## 会话管理

- **会话 ID**: 可以提供或使用 `session_id` 或 `user_id` 参数自动生成
- **上下文保持**: 每个会话维护对话历史
- **超时**: 会话在配置的超时时间后过期（默认 30 分钟）
- **清理**: 自动会话清理在后台调度器上运行

## 安全考虑

- SSL 警告在开发中被禁用，但在生产环境中应该启用
- API 令牌身份验证是可选的，但建议在生产环境中使用
- 所有 API 端点都实现了用户输入验证
- 会话数据默认存储在内存中（支持 Redis）

## 开发注意事项

- 系统在 Unix 系统上使用 uvloop，在 Windows 上使用 asyncio 以获得最佳性能
- 后台调度器每 30 分钟运行模型健康检查
- 路由配置可以通过环境变量重新加载，无需重启服务
- 调试模式提供详细的日志记录用于故障排除