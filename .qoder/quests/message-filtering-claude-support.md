# 消息过滤与Claude支持功能设计

## 概述

本设计文档描述了对现有de-github项目进行消息过滤增强和Claude协议支持完善的技术方案。

### 核心问题
1. 无效消息过滤（缺少role/content的消息）
2. 空内容消息处理  
3. Claude协议响应格式修复
4. **关键原则**：只修改`more_core.py`，不触及`degpt.py`，确保稳定性

### 设计原则
- **精简优先**：使用最简单的代码实现功能
- **稳定可信**：最小化修改范围，避免破坏性变更
- **上层处理**：所有逻辑在`more_core.py`中处理
- **零依赖**：不修改`degpt.py`的任何逻辑

## 技术架构

### 核心理念
在`more_core.py`中实现所有增强功能，保持`degpt.py`不变：

1. **消息过滤**：在`_generate_response_optimized`中加入简单的过滤逻辑
2. **Claude协议**：在`claude_messages`端点中完善响应转换
3. **参数处理**：在`more_core.py`中过滤thinking等参数，不传递给后端

### 简化数据流
```
客户端请求 -> more_core.py(过滤+转换) -> degpt.py(保持不变) -> 响应转换 -> 客户端
```

## 消息过滤机制

### 过滤规则
1. 消息必须是字典，包含role和content字段
2. role必须是"system"/"user"/"assistant"
3. content不能为空（字符串或有效数组）

### 实现方式
在`more_core.py`的`_generate_response_optimized`方法中添加过滤逻辑，确保只处理有效消息。

## Claude协议支持完善

### 核心原则
1. **thinking参数**：仅记录，不透传给degpt.py
2. **响应格式**：所有Claude请求返回Claude格式
3. **最大兼容**：忽略未知参数，不报错
4. **精简处理**：在现有`claude_messages`端点基础上增强

### 实现要点
- 在`claude_messages`端点中过滤消息
- thinking等Claude特有参数仅记录，不透传
- 确保流式和非流式响应都转换为Claude格式
- 利用现有的`_convert_claude_to_openai`和`_convert_openai_to_claude`方法
    
    # 确保stream参数正确传递
    if "stream" in claude_data:
        openai_data["stream"] = claude_data["stream"]
    
    # anthropic相关参数仅记录，不影响处理流程
    anthropic_headers = {
        "anthropic-beta": headers.get("anthropic-beta"),
        "anthropic-version": headers.get("anthropic-version"), 
        "anthropic-dangerous-direct-browser-access": headers.get("anthropic-dangerous-direct-browser-access")
    }
    
    if debug and any(anthropic_headers.values()):
        print(f"Claude协议头信息: {anthropic_headers}（仅记录，不透传）")
    
    return openai_data

def safe_parameter_extraction(self, claude_data: Dict) -> Dict:
    """安全的参数提取，最大化兼容性"""
    safe_params = {}
    
    # 核心必需参数
    core_params = ["model", "messages", "max_tokens"]
    for param in core_params:
        if param in claude_data:
            safe_params[param] = claude_data[param]
    
    # 标准可选参数 - 有则处理，无则忽略
    optional_params = {
        # 忽略
        "temperature": lambda x: float(x) if isinstance(x, (int, float)) else 0.7,
        "top_p": lambda x: float(x) if isinstance(x, (int, float)) else 1.0,
        "stop_sequences": lambda x: x if isinstance(x, list) else [],
        "tools": lambda x: x if isinstance(x, list) else [],
        "tool_choice": lambda x: x,
        # 有泽处理，无不处理
        "stream": lambda x: bool(x),
        "system": lambda x: x,  # 支持字符串和数组格式
        "session_id": lambda x: str(x) if x else None,
        "user_id": lambda x: str(x) if x else None
        
    }
    
    for param, converter in optional_params.items():
        if param in claude_data:
            try:
                safe_params[param] = converter(claude_data[param])
            except Exception as e:
                if debug:
                    print(f"参数 {param} 转换失败，使用默认值: {e}")
                # 忽略转换失败的参数，不影响整体处理
    
    # Claude特有参数处理（但不透传给degpt）
    claude_specific = {
        "thinking": lambda x: x,  # 保留原始格式用于后续处理
        "anthropic_beta": lambda x: str(x) if x else None,
        "anthropic_version": lambda x: str(x) if x else None
    }
    
    for param, converter in claude_specific.items():
        if param in claude_data:
            try:
                safe_params[param] = converter(claude_data[param])
            except Exception as e:
                if debug:
                    print(f"Claude参数 {param} 处理失败: {e}")
    
    # 对于完全不认识的参数，直接忽略
    known_params = set(core_params) | set(optional_params.keys()) | set(claude_specific.keys())
    unknown_params = set(claude_data.keys()) - known_params
    if unknown_params and debug:
        print(f"忽略未识别的参数: {unknown_params}")
    
    return safe_params
```

### 流式响应修复

#### 1. Claude SSE格式规范

Claude API使用特定的SSE事件格式：

```
event: message_start
data: {"type": "message_start", "message": {...}}

event: content_block_start  
data: {"type": "content_block_start", "index": 0, "content_block": {...}}

event: content_block_delta
data: {"type": "content_block_delta", "index": 0, "delta": {...}}

event: content_block_stop
data: {"type": "content_block_stop", "index": 0}

event: message_stop
data: {"type": "message_stop"}
```

#### 2. 响应流修复策略

```python
async def _stream_claude_response_fixed(self, response):
    """修复的Claude流式响应处理器 - 完全兼容Claude SSE格式"""
    message_id = f"msg_{int(time.time() * 1000)}"
    model_name = "claude-opus-4-1-20250805"  # 默认模型名
    input_tokens = 0
    output_tokens = 0
    
    try:
        # 发送message_start事件
        message_start = {
            "type": "message_start",
            "message": {
                "id": message_id,
                "type": "message",
                "role": "assistant", 
                "content": [],
                "model": model_name,
                "stop_reason": None,
                "stop_sequence": None,
                "usage": {"input_tokens": input_tokens, "output_tokens": 1}
            }
        }
        yield f"event: message_start\ndata: {json.dumps(message_start, ensure_ascii=False)}\n\n"
        
        # 发送content_block_start事件
        block_start = {
            "type": "content_block_start",
            "index": 0,
            "content_block": {"type": "text", "text": ""}
        }
        yield f"event: content_block_start\ndata: {json.dumps(block_start, ensure_ascii=False)}\n\n"
        
        # 发送ping事件（保持连接活跃）
        ping_event = {"type": "ping"}
        yield f"event: ping\ndata: {json.dumps(ping_event, ensure_ascii=False)}\n\n"
        
        # 处理流式内容
        accumulated_text = ""
        async for chunk in self._stream_response(response):
            if chunk.startswith("data:") and "content" in chunk:
                try:
                    data_str = chunk[5:].strip()  # 移除"data:"前缀
                    if data_str and data_str != "[DONE]":
                        openai_data = json.loads(data_str)
                        
                        # 提取内容增量
                        if "choices" in openai_data and openai_data["choices"]:
                            choice = openai_data["choices"][0]
                            if "delta" in choice and "content" in choice["delta"]:
                                content_delta = choice["delta"]["content"]
                                accumulated_text += content_delta
                                
                                # 构造Claude格式的增量事件
                                claude_delta = {
                                    "type": "content_block_delta",
                                    "index": 0,
                                    "delta": {
                                        "type": "text_delta",
                                        "text": content_delta
                                    }
                                }
                                yield f"event: content_block_delta\ndata: {json.dumps(claude_delta, ensure_ascii=False)}\n\n"
                        
                        # 提取模型信息
                        if "model" in openai_data:
                            model_name = openai_data["model"]
                            
                except json.JSONDecodeError:
                    continue
        
        # 发送content_block_stop事件
        block_stop = {"type": "content_block_stop", "index": 0}
        yield f"event: content_block_stop\ndata: {json.dumps(block_stop, ensure_ascii=False)}\n\n"
        
        # 计算输出token数
        if accumulated_text:
            try:
                import tiktoken
                enc = tiktoken.get_encoding("cl100k_base")
                output_tokens = len(enc.encode(accumulated_text))
            except:
                output_tokens = len(accumulated_text.split())  # 简单估算
        
        # 发送message_delta事件
        message_delta = {
            "type": "message_delta",
            "delta": {
                "stop_reason": "end_turn",
                "stop_sequence": None
            },
            "usage": {"output_tokens": output_tokens}
        }
        yield f"event: message_delta\ndata: {json.dumps(message_delta, ensure_ascii=False)}\n\n"
        
        # 发送message_stop事件
        message_stop = {"type": "message_stop"}
        yield f"event: message_stop\ndata: {json.dumps(message_stop, ensure_ascii=False)}\n\n"
        
    except Exception as e:
        # 错误处理 - 发送标准Claude错误事件
        error_event = {
            "type": "error",
            "error": {
                "type": "server_error", 
                "message": f"流处理错误: {str(e)}"
            }
        }
        yield f"event: error\ndata: {json.dumps(error_event, ensure_ascii=False)}\n\n"
```

## 错误处理增强

### 最大兼容性策略

#### 1. 参数容错处理
- **未知参数**：直接忽略，不报错
- **格式错误参数**：使用默认值替代
- **版本不兼容参数**：智能跳过

#### 2. Claude流式响应支持
Claude API完全支持流式响应，当`stream=true`时使用SSE格式：

**标准流式响应格式**：
```
event: message_start
data: {"type": "message_start", "message": {"id": "msg_xxx", "type": "message", "role": "assistant", "content": [], "model": "claude-opus-4-1-20250805", "stop_reason": null, "stop_sequence": null, "usage": {"input_tokens": 25, "output_tokens": 1}}}

event: content_block_start  
data: {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}

event: ping
data: {"type": "ping"}

event: content_block_delta
data: {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "Hello"}}

event: content_block_stop
data: {"type": "content_block_stop", "index": 0}

event: message_delta
data: {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": null}, "usage": {"output_tokens": 15}}

event: message_stop
data: {"type": "message_stop"}
```

**Thinking模式流式响应**（当`thinking.type="enabled"`时）：
```
event: content_block_start
data: {"type": "content_block_start", "index": 0, "content_block": {"type": "thinking", "thinking": ""}}

event: content_block_delta
data: {"type": "content_block_delta", "index": 0, "delta": {"type": "thinking_delta", "thinking": "Let me solve this step by step..."}}

event: content_block_stop
data: {"type": "content_block_stop", "index": 0}

event: content_block_start
data: {"type": "content_block_start", "index": 1, "content_block": {"type": "text", "text": ""}}

event: content_block_delta
data: {"type": "content_block_delta", "index": 1, "delta": {"type": "text_delta", "text": "The answer is..."}}
```

**工具调用流式响应**：
```
event: content_block_start
data: {"type": "content_block_start", "index": 1, "content_block": {"type": "tool_use", "id": "toolu_xxx", "name": "get_weather", "input": {}}}

event: content_block_delta
data: {"type": "content_block_delta", "index": 1, "delta": {"type": "input_json_delta", "partial_json": "{\"location\":"}}
```

#### 3. 容错处理机制

```python
def graceful_error_handling(self, operation_name: str, func, *args, **kwargs):
    """全局容错处理器"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if debug:
            print(f"{operation_name} 操作失败，将使用默认行为: {e}")
        # 返回安全的默认值，不中断处理流程
        return None

def handle_claude_compatibility(self, request_data: Dict) -> Dict:
    """处理Claude兼容性问题"""
    # 1. 忽略所有不识别的字段
    known_fields = {
        'model', 'messages', 'max_tokens', 'temperature', 'top_p', 
        'stream', 'stop_sequences', 'system', 'session_id', 'user_id',
        'tools', 'tool_choice'
    }
    
    cleaned_data = {}
    for key, value in request_data.items():
        if key in known_fields:
            cleaned_data[key] = value
        elif key == 'thinking':
            # thinking参数仅记录，不透传给degpt
            if debug:
                print(f"Claude thinking参数: {value}（仅记录，不透传）")
        elif debug:
            print(f"忽略未知字段: {key}")
    
    return cleaned_data
```

#### 1. Claude格式错误响应

```python
def create_claude_error_response(self, error_type: str, message: str, status_code: int = 400) -> Dict:
    """创建标准Claude格式错误响应"""
    return {
        "type": "error",
        "error": {
            "type": error_type,
            "message": message
        }
    }

def handle_message_validation_error(self, errors: List[str]) -> HTTPException:
    """处理消息验证错误"""
    error_message = "消息格式错误: " + "; ".join(errors)
    raise HTTPException(
        status_code=400,
        detail=error_message
    )
```

#### 2. 空消息处理

```python
def handle_empty_messages(self) -> HTTPException:
    """处理空消息列表"""
    raise HTTPException(
        status_code=400,
        detail="请求必须包含至少一条有效消息"
    )
```

## 实现方案

### 核心修改点

**文件**: `more_core.py`
**方法**: `_generate_response_optimized` 和 `claude_messages`

#### 1. 消息过滤
在`_generate_response_optimized`方法中，消息验证前添加过滤逻辑：
- 过滤无效消息（缺少role/content）
- 移除空内容消息
- 确保有效消息列表不为空

#### 2. Claude协议增强
在`claude_messages`端点中：
- thinking参数仅记录，不透传给degpt.py
- 确保所有响应都转换为Claude格式
- 支持流式和非流式响应
- 使用现有的协议转换方法

#### 3. 错误处理
- 忽略未知参数，不报错
- 最大兼容性策略
- 保持degpt.py完全不变

## 测试验证

### 关键测试场景
1. 无效消息过滤测试
2. Claude thinking参数测试
3. 流式响应格式测试
4. 最大兼容性测试