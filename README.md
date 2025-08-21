# DD

## 环境变量

- **REPLACE_CHAT**: 强制替换目标地址,/开头
- **PREFIX_CHAT**:   支持多个,每个都增加前缀，/开头 
- **APPEND_CHAT**:  增加更多的接口, /开头
- **DEBUG**:  是否debug默认，是否可以查看日志
- **TOKEN**:  是否限制token才能访问，设置则限制，不设置则不限制

## down and use

Install from the command line
``` bash
$ docker pull ghcr.io/hhhaiai/de:latest
$ docker run -d \
  --name de \
  --restart always \
  -p 7860:7860 \
  -m 2g \
  -e DEBUG=false \
  ghcr.io/hhhaiai/de:latest
```
Use as base image in Dockerfile:
``` dockerfile
FROM ghcr.io/hhhaiai/de:latest
```

build test use code
``` bash
$ docker build --no-cache --compress -t de .
$ docker run -p 7860:7860 -m 2g -e DEBUG=false de
```


call demo

```

curl http://localhost:7860/v1/models
curl http://localhost:7860/api/v1/models

curl -X POST http://localhost:7860/api/v1/chat/completions \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "你是什么模型?"}],
    "stream":true
  }'

curl -X POST http://localhost:7860/api/v1/chat/completions \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "你是什么模型?"}],
    "stream":false
  }'

```

## 上下文对话测试示例

### 1. 单次对话（无上下文）
```bash
curl -X POST http://localhost:7860/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "你好，我是小明"}],
    "stream": false
  }'
```

### 2. 用户级别隔离（使用 user_id）
```bash
# 第一次对话
curl -X POST http://localhost:7860/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "你好，我是用户1"}],
    "user_id": "user_001",
    "stream": false
  }'

# 第二次对话（会记住上下文）
curl -X POST http://localhost:7860/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "我刚才说了什么？"}],
    "user_id": "user_001",
    "stream": false
  }'
```

### 3. 会话级别隔离（使用 session_id）
```bash
# 创建会话
curl -X POST http://localhost:7860/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "我们来讨论人工智能"}],
    "session_id": "ai_discussion",
    "stream": false
  }'

# 继续会话
curl -X POST http://localhost:7860/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "刚才我们讨论的是什么主题？"}],
    "session_id": "ai_discussion",
    "stream": false
  }'
```

### 4. 流式响应 + 上下文
```bash
curl -X POST http://localhost:7860/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "请介绍Python编程"}],
    "session_id": "python_lesson",
    "stream": true
  }'
```

### 5. 清理会话
```bash
curl -X POST http://localhost:7860/api/v1/session/clear \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "python_lesson"
  }'
```

### 参数说明：
- `user_id`: 可选，用户标识符，会自动转换为 `user_{user_id}` 格式的会话ID
- `session_id`: 可选，自定义会话标识符，用于维持对话上下文
- 如果都不提供：系统自动生成临时会话ID，实现单次对话隔离
- 如果同时提供：优先使用 `session_id`

## Claude协议支持

### Claude协议端点
```bash
# Claude协议消息端点
curl -X POST http://localhost:7860/api/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "model": "claude-3-sonnet-20240229",
    "messages": [{"role": "user", "content": "你好，Claude！"}],
    "max_tokens": 1024,
    "stream": false
  }'
```

### Claude协议 + 上下文支持
```bash
# 使用session_id维持对话上下文
curl -X POST http://localhost:7860/api/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-sonnet-20240229",
    "messages": [{"role": "user", "content": "我们来讨论机器学习"}],
    "session_id": "ml_discussion",
    "max_tokens": 1024
  }'

# 继续对话
curl -X POST http://localhost:7860/api/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-sonnet-20240229",
    "messages": [{"role": "user", "content": "刚才我们讨论的是什么？"}],
    "session_id": "ml_discussion",
    "max_tokens": 1024
  }'
```

### Claude协议参数说明：
- `model`: 模型名称（支持所有可用模型）
- `messages`: 消息数组，格式与OpenAI兼容
- `max_tokens`: 最大生成token数
- `stream`: 是否使用流式响应
- `session_id`: 会话标识符，用于维持对话上下文
- `user_id`: 用户标识符，自动转换为会话ID

### 支持的Claude模型名称：
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229` 
- `claude-3-haiku-20240307`
- `claude-2.1`
- `claude-2.0`
- `claude-instant-1.2`

注意：实际使用后端支持的模型，模型名称主要用于协议兼容性。