import base64
import json
import multiprocessing
import os
import random
import re
import string
import time
from typing import Dict, Any, List, Union, Optional, Tuple

import tiktoken
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.responses import HTMLResponse
# 禁用 SSL 警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import asyncio
import sys

import degpt as dg

# debug for Log
debug = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

app = FastAPI(
    title="ones",
    description="High-performance API service",
    version="1.2.5|2025.08.26"
)


class APIServer:
    """High-performance API server implementation"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self._setup_routes()
        self._setup_scheduler()
    
    def validate_image_url(self, url: str) -> None:
        """验证图片URL和格式"""
        if not url:
            raise ValueError("图片URL不能为空")
        
        # Base64格式验证
        if url.startswith("data:image/"):
            try:
                # 提取MIME类型和数据
                if ',' not in url:
                    raise ValueError("Base64图片格式无效")
                header, data = url.split(',', 1)
                mime_type = header.split(';')[0].split(':')[1]
                
                # 验证支持的图片格式
                if mime_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
                    raise ValueError(f"不支持的图片格式: {mime_type}")
                
                # 验证文件大小（Base64解码后）
                try:
                    decoded_data = base64.b64decode(data)
                    if len(decoded_data) > 20 * 1024 * 1024:  # 20MB
                        raise ValueError("图片大小超出限制: 20MB")
                except Exception as e:
                    raise ValueError(f"Base64解码失败: {str(e)}")
            except Exception as e:
                raise ValueError(f"Base64图片验证失败: {str(e)}")
        
        # HTTP/HTTPS URL格式验证
        elif url.startswith(("http://", "https://")):
            # URL格式基本验证
            url_pattern = re.compile(
                r'^https?://'  # http:// 或 https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'  # 域名
                r'[A-Z]{2,6}\.?|'  # 顶级域名
                r'localhost|'  # localhost
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP地址
                r'(?::\d+)?'  # 可选端口
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
            if not url_pattern.match(url):
                raise ValueError("无效的图片URL格式")
        else:
            raise ValueError("不支持的图片URL格式，请使用Base64或HTTP/HTTPS URL")
    
    def validate_multimodal_content(self, content: Union[str, List[Dict[str, Any]]]) -> Tuple[bool, str, str]:
        """验证多模态内容格式
        
        返回:
            (验证通过, 内容类型, 合并的文本内容)
        """
        # 支持字符串格式（向后兼容）
        if isinstance(content, str):
            return True, "text", content
        
        # 支持数组格式（多模态）
        if isinstance(content, list):
            has_image = False
            text_parts = []
            
            for item in content:
                if not isinstance(item, dict) or "type" not in item:
                    raise ValueError("内容项必须是包含type字段的字典")
                
                item_type = item.get("type")
                if item_type == "text":
                    if "text" not in item:
                        raise ValueError("文本内容项必须包含text字段")
                    text_parts.append(item.get("text", ""))
                elif item_type == "image_url":
                    has_image = True
                    if "image_url" not in item or "url" not in item["image_url"]:
                        raise ValueError("图片内容项必须包含image_url.url字段")
                    # 验证图片URL格式和大小
                    try:
                        self.validate_image_url(item["image_url"]["url"])
                    except ValueError as e:
                        raise ValueError(f"图片验证失败: {str(e)}")
                else:
                    raise ValueError(f"不支持的内容类型: {item_type}")
            
            content_type = "multimodal" if has_image else "text"
            combined_text = "\n".join(text_parts)
            
            return True, content_type, combined_text
        
        raise ValueError("content必须是字符串或内容数组")
    
    def select_model_for_content(self, model_name: str, content_type: str) -> str:
        """基于内容类型智能选择模型"""
        # 如果是纯文本，使用原有逻辑
        if content_type == "text":
            if model_name == "auto":
                return dg.get_auto_model()
            return dg.get_model_by_autoupdate(model_name)
        
        # 如果包含图片，需要检查模型是否支持图片
        if content_type == "multimodal":
            # 获取可用模型列表
            try:
                models_str = dg.get_models()
                models_data = json.loads(models_str)
                available_models = models_data.get("data", [])
                
                # 筛选支持图片的模型
                image_models = [
                    model for model in available_models 
                    if model.get("support") == "image"
                ]
                
                if not image_models:
                    raise ValueError("当前无可用的图片支持模型，请使用纯文本请求")
                
                # 如果指定的模型支持图片，使用指定模型
                if model_name != "auto":
                    for model in image_models:
                        if model.get("name") == model_name or model.get("id") == model_name:
                            return dg.get_model_by_autoupdate(model_name)
                
                # 否则自动选择第一个可用的图片模型
                best_model = image_models[0]
                model_id = best_model.get("name") or best_model.get("id")
                return dg.get_model_by_autoupdate(model_id)
                
            except Exception as e:
                if debug:
                    print(f"模型选择错误: {e}")
                # 降级处理：如果无法获取模型列表，使用原有逻辑
                if model_name == "auto":
                    return dg.get_auto_model()
                return dg.get_model_by_autoupdate(model_name)
        
        # 默认情况
        if model_name == "auto":
            return dg.get_auto_model()
        return dg.get_model_by_autoupdate(model_name)

    def _setup_scheduler(self):
        """ Schedule tasks to check and reload routes and models at regular intervals. """
        self.scheduler = BackgroundScheduler()
        # Scheduled Task 1: Check and reload routes every 30 seconds. Calls _reload_routes_if_needed method to check if routes need to be updated
        self.scheduler.add_job(self._reload_routes_if_needed, 'interval', seconds=30)

        # Scheduled Task 2: Reload models every 30 minutes (1800 seconds). This task will check and update the model data periodically
        self.scheduler.add_job(self._reload_check, 'interval', seconds=60 * 30)
        self.scheduler.start()

    def _setup_routes(self) -> None:
        """Initialize API routes"""
        self.routes = """Initialize API routes"""

        # Static routes with names for filtering
        @self.app.get("/", name="root", include_in_schema=False)
        def root():
            return HTMLResponse(content="<h1>hello. It's home page.</h1>")

        @self.app.get("/health", name="health")
        def health():
            return JSONResponse(content={"status": "working"})

        @self.app.get("/api/v1/models", name="models")
        @self.app.get("/v1/models", name="models")
        def models():
            if debug:
                print("Fetching models...")
            models_str = dg.get_models()
            try:
                models_json = json.loads(models_str)
                return JSONResponse(content=models_json)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=500,
                                    detail=f"Invalid models data: {str(e)}")

        @self.app.post("/api/v1/session/clear", name="clear_session")
        async def clear_session(request: Request):
            """清除特定会话"""
            try:
                data = await request.json()
                session_id = data.get("session_id")
                if session_id:
                    dg.clear_session(session_id)
                    return JSONResponse(content={"status": "success", "message": f"Session {session_id} cleared"})
                else:
                    raise HTTPException(status_code=400, detail="session_id is required")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        # Claude协议支持
        @self.app.post("/api/v1/messages", name="claude_messages")
        async def claude_messages(request: Request):
            """Claude协议消息端点"""
            try:
                # print("---"*20)
                # print("--- 捕获到 Beta 请求 (/api/v1/messages?beta=true) ---")
                # # --- 新增调试逻辑：检查 beta=true 查询参数 ---
                # from urllib.parse import parse_qs
                # # 获取查询参数字符串 (e.g., "beta=true&other=value")
                # query_string = request.url.query
                # # 解析查询参数
                # query_params = parse_qs(query_string)
                # # 检查 beta 参数是否存在且其第一个值为 'true' (忽略大小写)
                # is_beta_request = 'beta' in query_params and query_params['beta'][0].lower() == 'true'

                # if is_beta_request:
                #     # 1. 获取并打印请求头 (Headers)
                #     headers = dict(request.headers)
                #     print("请求 Headers:")
                #     for key, value in headers.items():
                #         # 注意：Authorization 头部可能包含敏感信息，打印时请注意
                #         print(f"  {key}: {value}")
                #     # 2. 获取并打印请求体 (Body)
                #     # 注意：await request.body() 只能调用一次
                #     raw_body_bytes = await request.body()
                #     try:
                #         # 尝试将 body 解析为 JSON
                #         body_data = json.loads(raw_body_bytes.decode('utf-8'))
                #         print("请求 Body (JSON):")
                #         print(json.dumps(body_data, indent=2, ensure_ascii=False)) # 格式化打印
                #     except json.JSONDecodeError:
                #         # 如果不是 JSON，就打印原始字符串
                #         raw_body_str = raw_body_bytes.decode('utf-8')
                #         print("请求 Body (Raw):")
                #         print(raw_body_str)

                #     print("--- Beta 请求信息打印完毕 ---")
                #     print("==="*20)

                headers = dict(request.headers)
                data = await request.json()
                # 检查流式请求
                stream = data.get("stream", False)

                # 转换Claude格式到OpenAI格式
                openai_data = self._convert_claude_to_openai(data, headers)

                # 使用现有的OpenAI处理逻辑
                response = self._generate_response_optimized(headers, openai_data)

                if stream and isinstance(response, StreamingResponse):
                    # 流式响应 - 转换为Claude格式的SSE流
                    return StreamingResponse(
                        self._stream_claude_response(response),
                        media_type="text/event-stream"
                    )
                else:
                    # 非流式响应
                    if isinstance(response, StreamingResponse):
                        # 收集流式响应数据
                        content = b""
                        async for chunk in response.body_iterator:
                            content += chunk
                        response_data = json.loads(content.decode())
                    else:
                        response_data = response

                    # 转换回Claude格式
                    claude_response = self._convert_openai_to_claude(response_data)
                    return JSONResponse(content=claude_response)

            except Exception as e:
                if debug:
                    print(f"Claude request processing error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error") from e

        # Register dynamic chat completion routes
        routes = self._get_routes()
        if debug:
            print(f"Registering routes: {routes}")
        for path in routes:
            self._register_route(path)
        existing_routes = [route.path for route in self.app.routes if hasattr(route, 'path')]
        if debug:
            print(f"All routes now: {existing_routes}")

    def _get_routes(self) -> List[str]:
        """Get configured API routes"""
        default_path = "/api/v1/chat/completions"
        replace_chat = os.getenv("REPLACE_CHAT", "")
        prefix_chat = os.getenv("PREFIX_CHAT", "")
        append_chat = os.getenv("APPEND_CHAT", "")

        if replace_chat:
            return [path.strip() for path in replace_chat.split(",") if path.strip()]

        routes = []
        if prefix_chat:
            routes.extend(f"{prefix.rstrip('/')}{default_path}"
                          for prefix in prefix_chat.split(","))
            return routes

        if append_chat:
            append_paths = [path.strip() for path in append_chat.split(",") if path.strip()]
            routes = [default_path] + append_paths
            return routes

        # 默认情况下，同时支持/api/v1/chat/completions和/v1/chat/completions
        return [default_path, "/v1/chat/completions"]

    def _register_route(self, path: str) -> None:
        """Register a single API route"""
        global debug

        async def chat_endpoint(request: Request):
            try:
                if debug:
                    print(f"Request chat_endpoint...")
                headers = dict(request.headers)
                data = await request.json()
                if debug:
                    print(f"Request received...\r\n\tHeaders: {headers},\r\n\tData: {data}")
                return self._generate_response_optimized(headers, data)
            except Exception as e:
                if debug:
                    print(f"Request processing error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error") from e

        self.app.post(path)(chat_endpoint)

    def _calculate_tokens(self, text: str) -> int:
        """Calculate token count for text"""
        return len(self.encoding.encode(text))

    def _generate_id(self, letters: int = 4, numbers: int = 6) -> str:
        """Generate unique chat completion ID"""
        letters_str = ''.join(random.choices(string.ascii_lowercase, k=letters))
        numbers_str = ''.join(random.choices(string.digits, k=numbers))
        return f"chatcmpl-{letters_str}{numbers_str}"

    def _generate_session_id(self) -> str:
        """Generate unique session ID for single conversation"""
        letters_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        numbers_str = ''.join(random.choices(string.digits, k=4))
        return f"session_{letters_str}{numbers_str}"

    def _convert_claude_to_openai(self, claude_data: Dict, headers: Dict) -> Dict:
        """Convert Claude format to OpenAI format with complete field mapping"""
        # Claude格式完整示例:
        # {
        #   "model": "claude-3-sonnet-20240229",
        #   "messages": [{"role": "user", "content": [{"type": "text", "text": "Hello"}]}],
        #   "max_tokens": 1024,
        #   "stream": false,
        #   "temperature": 0.7,
        #   "top_p": 0.9,
        #   "top_k": 5,
        #   "stop_sequences": ["\n\nHuman:"],
        #   "system": "You are a helpful assistant."
        # }

        openai_data = {
            "model": claude_data.get("model", "gpt-4o-mini"),
            "messages": self._convert_claude_messages(claude_data.get("messages", [])),
            "stream": claude_data.get("stream", False)
        }

        # 映射所有标准参数
        parameter_mapping = {
            "max_tokens": "max_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
            "stop_sequences": "stop",
            "top_k": "top_k",
            "frequency_penalty": "frequency_penalty",
            "presence_penalty": "presence_penalty"
        }

        for claude_key, openai_key in parameter_mapping.items():
            if claude_key in claude_data:
                openai_data[openai_key] = claude_data[claude_key]

        # 处理system提示
        if "system" in claude_data:
            openai_data["messages"].insert(0, {
                "role": "system",
                "content": claude_data["system"]
            })

        # 处理session_id和user_id
        session_id = claude_data.get("session_id")
        user_id = claude_data.get("user_id")
        if session_id:
            openai_data["session_id"] = session_id
        if user_id:
            openai_data["user_id"] = user_id

        # 处理tools参数（如果存在）
        if "tools" in claude_data:
            openai_data["tools"] = claude_data["tools"]
        if "tool_choice" in claude_data:
            openai_data["tool_choice"] = claude_data["tool_choice"]

        return openai_data

    def _convert_claude_messages(self, claude_messages: List[Dict]) -> List[Dict]:
        """Convert Claude message format to OpenAI format"""
        openai_messages = []

        for message in claude_messages:
            if not isinstance(message, dict):
                continue

            role = message.get("role")
            content = message.get("content", [])

            # 转换内容格式
            if isinstance(content, list):
                # Claude格式: [{"type": "text", "text": "Hello"}]
                text_content = ""
                for content_item in content:
                    if isinstance(content_item, dict) and content_item.get("type") == "text":
                        text_content += content_item.get("text", "") + "\n"
                openai_messages.append({
                    "role": role,
                    "content": text_content.strip()
                })
            else:
                # 直接使用字符串内容
                openai_messages.append({
                    "role": role,
                    "content": str(content)
                })

        return openai_messages

    def _convert_openai_to_claude(self, openai_response: Dict) -> Dict:
        """Convert OpenAI format to Claude format with complete field mapping"""
        if not isinstance(openai_response, dict):
            return self._create_error_claude_response(str(openai_response))

        try:
            # 提取消息内容
            content = ""
            thinking_content = None
            finish_reason = "stop"

            if "choices" in openai_response and openai_response["choices"]:
                choice = openai_response["choices"][0]
                if "message" in choice:
                    message = choice["message"]
                    if "content" in message:
                        content = message.get("content", "")

                    # 提取thinking内容（如果存在）
                    if "thinking" in message:
                        thinking_content = message["thinking"]

                # 映射finish_reason到Claude的stop_reason
                finish_reason_map = {
                    "stop": "end_turn",
                    "length": "max_tokens",
                    "tool_calls": "tool_use",
                    "content_filter": "content_filter"
                }
                finish_reason = finish_reason_map.get(
                    choice.get("finish_reason", "stop"),
                    "end_turn"
                )

            # 提取使用情况
            input_tokens = 0
            output_tokens = 0
            if "usage" in openai_response:
                input_tokens = openai_response["usage"].get("prompt_tokens", 0)
                output_tokens = openai_response["usage"].get("completion_tokens", 0)

            # 构建完整的Claude响应
            claude_response = {
                "id": openai_response.get("id", f"msg_{int(time.time() * 1000)}"),
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": content}],
                "model": openai_response.get("model", "claude-3-sonnet-20240229"),
                "stop_reason": finish_reason,
                "stop_sequence": None,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                }
            }

            # 添加thinking内容（如果存在）
            if thinking_content:
                claude_response["thinking"] = thinking_content

            # 添加tool_use内容（如果存在）
            if "tool_calls" in openai_response.get("choices", [{}])[0].get("message", {}):
                tool_calls = openai_response["choices"][0]["message"]["tool_calls"]
                if tool_calls:
                    claude_response["content"].extend(
                        self._convert_tool_calls_to_claude(tool_calls)
                    )

            return claude_response

        except Exception as e:
            return self._create_error_claude_response(f"Conversion error: {str(e)}")

    def _convert_tool_calls_to_claude(self, tool_calls: List[Dict]) -> List[Dict]:
        """Convert OpenAI tool calls to Claude format"""
        claude_tools = []
        for tool_call in tool_calls:
            if isinstance(tool_call, dict):
                claude_tools.append({
                    "type": "tool_use",
                    "id": tool_call.get("id", f"tool_{int(time.time() * 1000)}"),
                    "name": tool_call.get("function", {}).get("name", ""),
                    "input": tool_call.get("function", {}).get("arguments", {})
                })
        return claude_tools

    def _convert_openai_stream_to_claude(self, openai_data: Dict) -> Optional[Dict]:
        """Convert OpenAI streaming response to Claude format"""
        if not isinstance(openai_data, dict):
            return None

        claude_chunk = {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "text_delta", "text": ""}
        }

        # 提取OpenAI流式数据中的内容
        if "choices" in openai_data and openai_data["choices"]:
            choice = openai_data["choices"][0]
            if "delta" in choice and "content" in choice["delta"]:
                claude_chunk["delta"]["text"] = choice["delta"]["content"]
                return claude_chunk

        return None

    def _create_error_claude_response(self, error_message: str) -> Dict:
        """Create error response in Claude format"""
        return {
            "id": f"msg_{int(time.time() * 1000)}",
            "type": "error",
            "error": {
                "type": "server_error",
                "message": error_message
            },
            "model": "claude-3-sonnet-20240229",
            "usage": {"input_tokens": 0, "output_tokens": 0}
        }

    def is_chatgpt_format(self, data):
        """Check if the data is in the expected ChatGPT format"""
        try:
            # If the data is a string, try to parse it as JSON
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    return False  # If the string can't be parsed, it's not in the expected format

            # Now check if data is a dictionary and contains the necessary structure
            if isinstance(data, dict):
                # Ensure 'choices' is a list and the first item has a 'message' field
                if "choices" in data and isinstance(data["choices"], list) and len(data["choices"]) > 0:
                    if "message" in data["choices"][0]:
                        return True
        except Exception as e:
            print(f"Error checking ChatGPT format: {e}")
        return False

    def process_result(self, result, model):
        # 如果result是字符串，尝试将其转换为JSON
        if isinstance(result, str):
            try:
                result = json.loads(result)  # 转换为JSON
            except json.JSONDecodeError:
                return result

        # 确保result是一个字典（JSON对象）
        if isinstance(result, dict):
            # 设置新的id和object值
            result['id'] = self._generate_id()  # 根据需要设置新的ID值
            result['object'] = "chat.completion"  # 根据需要设置新的object值

            # 添加model值
            result['model'] = model  # 根据需要设置model值
        return result

    def _generate_response_optimized(self, headers: Dict[str, str], data: Dict[str, Any]) -> Union[Dict[str, Any], StreamingResponse]:
        """Generate API response with enhanced error handling"""
        global debug
        if debug:
            print("inside _generate_response")
        try:
            # check model
            model_name = data.get("model")
            
            # 验证消息格式并检测内容类型
            msgs = data.get("messages")
            if not msgs:
                raise HTTPException(status_code=400, detail="消息不能为空")
            
            if not isinstance(msgs, list):
                raise HTTPException(status_code=400, detail="消息必须是一个列表")
            
            # 检测是否包含多模态内容
            has_multimodal_content = False
            
            # 验证每条消息的基本结构和内容格式
            for i, message in enumerate(msgs):
                if not isinstance(message, dict):
                    raise HTTPException(status_code=400, detail=f"消息 {i} 必须是一个字典")
                if "role" not in message or "content" not in message:
                    raise HTTPException(status_code=400, detail=f"消息 {i} 必须包含 'role' 和 'content' 字段")
                if message["role"] not in ["system", "user", "assistant"]:
                    raise HTTPException(status_code=400, detail=f"消息 {i} 的 'role' 必须是 'system', 'user' 或 'assistant' 之一")
                
                # 使用新的多模态验证函数
                content = message["content"]
                try:
                    is_valid, content_type, combined_text = self.validate_multimodal_content(content)
                    if content_type == "multimodal":
                        has_multimodal_content = True
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=f"消息 {i} 格式错误: {str(e)}")
            
            # 基于内容类型选择模型
            content_type = "multimodal" if has_multimodal_content else "text"
            
            # 对于所有请求，如果模型不存在则使用auto校准
            if model_name and model_name != "auto" and not dg.is_model_available(model_name):
                model_name = "auto"
            
            # 使用智能模型选择
            try:
                model_name = self.select_model_for_content(model_name or "auto", content_type)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

            model = model_name  # 设置最终的model变量
            # must has token ? token check
            authorization = headers.get('Authorization')
            token = os.getenv("TOKEN", "")
            if token and authorization and token not in authorization:
                raise HTTPException(status_code=401, detail="无效的Token")

            # call ai
            if not msgs:
                raise HTTPException(status_code=400, detail="消息不能为空")

            # 获取会话ID - 支持session_id和user_id参数
            session_id = data.get("session_id")
            user_id = data.get("user_id")

            # 如果没有提供session_id，但提供了user_id，则使用user_id作为session_id
            if not session_id and user_id:
                session_id = f"user_{user_id}"

            # 如果都没有提供，生成一个临时的session_id用于单次对话
            if not session_id:
                session_id = self._generate_session_id()

            # 检查是否需要流式响应
            stream = data.get("stream", False)

            if debug:
                print(f"request model: {model_name}")
                if token:
                    print(f"request token: {token}")
                print(f"request messages: {msgs}")
                print(f"session_id: {session_id}")
                print(f"user_id: {user_id}")
                print(f"stream: {stream}")

            if stream:
                # 流式响应处理
                response = dg.chat_completion_messages(
                    messages=msgs,
                    model=model_name or "gpt-4o-mini",
                    session_id=session_id,
                    stream=True
                )

                # 直接返回流式响应，逐行转发给客户端
                return StreamingResponse(
                    self._stream_response(response),
                    media_type="text/event-stream"
                )
            else:
                # 非流式响应处理
                result = dg.chat_completion_messages(
                    messages=msgs,
                    model=model_name or "gpt-4o-mini",
                    session_id=session_id,
                    stream=False
                )
                if debug:
                    print(f"result: {result}---- {self.is_chatgpt_format(result)}")

                # Ensure result is properly formatted as a dictionary
                if isinstance(result, dict) and self.is_chatgpt_format(result):
                    # If data already follows ChatGPT format, use it directly
                    response_data = self.process_result(result, model_name)
                else:
                    # Calculate the current timestamp
                    current_timestamp = int(time.time() * 1000)
                    # Otherwise, calculate the tokens and return a structured response
                    result_content = str(result) if not isinstance(result, dict) else result.get("content", str(result))
                    prompt_tokens = self._calculate_tokens(str(data))
                    completion_tokens = self._calculate_tokens(result_content)
                    total_tokens = prompt_tokens + completion_tokens

                    response_data = {
                        "id": self._generate_id(),
                        "object": "chat.completion",
                        "created": current_timestamp,
                        "model": data.get("model", "gpt-4o"),
                        "choices": [{
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": result_content
                            },
                            "logprobs": None,
                            "finish_reason": "stop"
                        }],
                        "usage": {
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": total_tokens
                        },
                        "system_fingerprint": None
                    }

                # Print the response for debugging (you may remove this in production)
                if debug:
                    print(f"Response Data: {response_data}")

                # Ensure we always return a dictionary for non-streaming responses
                if isinstance(response_data, dict):
                    return response_data
                else:
                    # Fallback: return error response
                    return {
                        "error": "Invalid response format",
                        "message": str(response_data)[:200]
                    }
        except HTTPException:
            # 重新抛出HTTPException
            raise
        except Exception as e:
            # 安全地记录模型调用失败
            try:
                if 'model' in locals():
                    dg.record_call(model, False)
            except:
                pass  # 忽略记录错误

            if debug:
                print(f"Response generation error: {e}")
            # 提供更详细的错误信息
            error_detail = f"内部服务器错误: {str(e)}"
            # 如果是流式响应，我们需要返回一个流式的错误响应
            if data.get("stream", False):
                async def error_stream():
                    error_message = f'{{"error": "{error_detail}"}}'
                    yield f"data: {error_message}\n\n"
                return StreamingResponse(error_stream(), media_type="text/event-stream")
            else:
                raise HTTPException(status_code=500, detail=error_detail) from e

    async def _stream_response(self, response):
        """流式传输响应数据，确保每行正确格式化以便 SSE"""
        # 如果response是StreamingResponseWithSession对象，直接使用其iter_lines方法
        if hasattr(response, 'iter_lines'):
            # 使用 StreamingResponseWithSession 的 iter_lines 方法来累积内容并保存会话
            try:
                # iter_lines() 内部处理了累积和会话保存
                async for chunk in self._iter_lines_with_newline(response):
                    yield chunk
            except Exception as e:
                if debug:
                    print(f"Error in _stream_response (StreamingResponseWithSession): {e}")
                yield f"data: {{\"error\": \"Stream processing error: {str(e)}\"}}\n\n"
            finally:
                # 确保即使出错也能正确关闭原始响应
                response.__exit__(None, None, None) # 调用 __exit__ 触发会话保存等逻辑

        else:
            # 备用处理逻辑：如果传入的不是 StreamingResponseWithSession
            # （虽然根据当前代码逻辑，不太可能走到这里）
            try:
                # 直接转发来自后端API的SSE流，确保每行末尾有 \n
                for chunk in response.iter_lines():
                    if chunk:
                        decoded_chunk = chunk.decode('utf-8')
                        # 确保每行以 \n\n 结尾，符合 SSE 格式
                        if not decoded_chunk.endswith('\n'):
                            decoded_chunk += '\n'
                        yield decoded_chunk
            except Exception as e:
                if debug:
                    print(f"Error in _stream_response (fallback): {e}")
                yield f"data: {{\"error\": \"Stream error: {str(e)}\"}}\n\n"

    async def _iter_lines_with_newline(self, response_wrapper):
        """
        异步包装 StreamingResponseWithSession.iter_lines，
        确保每次 yield 的数据块以 \n\n 结尾，符合 SSE 规范。
        """
        loop = asyncio.get_event_loop()
        # 在线程中运行同步的 iter_lines 以避免阻塞事件循环
        iterator = await loop.run_in_executor(None, response_wrapper.iter_lines)
        try:
            for chunk in iterator:
                if chunk:
                    decoded_chunk = chunk.decode('utf-8')
                    # 确保符合 SSE 格式：每条消息以 \n\n 结尾
                    # degpt.py 返回的已经是 data: ... 或 data: [DONE] 格式
                    if not decoded_chunk.endswith('\n'):
                        decoded_chunk += '\n'
                    yield decoded_chunk
        except Exception as e:
            # 重新抛出异常，让调用者处理
            raise e
        finally:
            # 确保迭代器（如果需要）被正确关闭
            # requests 的 iter_lines 通常不需要显式关闭，但保持谨慎
            pass


    async def _stream_claude_response(self, response):
        """转换OpenAI流式响应为Claude格式"""
        try:
            async for chunk in self._stream_response(response):
                if chunk.startswith("data:") and chunk.strip() != "data: [DONE]":
                    # 解析OpenAI格式的SSE数据
                    data_str = chunk[len("data:"):].strip()
                    if data_str:
                        try:
                            openai_data = json.loads(data_str)
                            # 转换为Claude格式
                            claude_data = self._convert_openai_stream_to_claude(openai_data)
                            if claude_data:
                                yield f"event: completion\ndata: {json.dumps(claude_data, ensure_ascii=False)}\n\n"
                        except json.JSONDecodeError:
                            continue
                elif "error" in chunk:
                    # 转发错误信息
                    yield chunk
            # 流结束标记
            yield "event: done\ndata: {}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {{\"error\": \"Stream processing error: {str(e)}\"}}\n\n"

    def _get_workers_count(self) -> int:
        """Calculate optimal worker count"""
        try:
            cpu_cores = multiprocessing.cpu_count()
            recommended_workers = (2 * cpu_cores) + 1
            return min(max(4, recommended_workers), 8)
        except Exception as e:
            if debug:
                print(f"Worker count calculation failed: {e}, using default 4")
            return 4

    def get_server_config(self, host: str = "0.0.0.0", port: int = 7860) -> uvicorn.Config:
        """Get server configuration"""
        workers = self._get_workers_count()
        if debug:
            print(f"Configuring server with {workers} workers")
        # 检测平台，Windows不使用uvloop
        if sys.platform == "win32":
            loop_type = "asyncio" # <-- 关键修改：使用 "asyncio" 而不是 None
        else:
            loop_type = "uvloop"

        return uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            workers=workers,
            loop=loop_type,
            limit_concurrency=1000,
            timeout_keep_alive=30,
            access_log=True,
            log_level="info",
            http="httptools"
        )

    def run(self, host: str = "0.0.0.0", port: int = 7860) -> None:
        """Run the API server"""
        config = self.get_server_config(host, port)
        server = uvicorn.Server(config)
        server.run()

    def _reload_check(self) -> None:
        dg.reload_check()

    def _reload_routes_if_needed(self) -> None:
        """Check if routes need to be reloaded based on environment variables"""
        # reload Debug
        global debug
        debug = os.getenv("DEBUG", "False").lower() in ["true", "1", "t"]
        # relaod routes
        new_routes = self._get_routes()
        current_routes = [route for route in self.app.routes if hasattr(route, 'path')]

        # Check if the current routes are different from the new routes
        current_paths = [getattr(route, 'path', '') for route in current_routes]
        if current_paths != new_routes:
            if debug:
                print("Routes changed, reloading...")
            self._reload_routes(new_routes)

    def _reload_routes(self, new_routes: List[str]) -> None:
        """Reload only dynamic routes while preserving static ones"""
        # Define static route names
        static_routes = {"root", "health", "models", "clear_session", "claude_messages"}

        # Remove only dynamic routes
        self.app.routes[:] = [
            route for route in self.app.routes
            if not hasattr(route, 'name') or getattr(route, 'name', '') in static_routes
        ]

        # Register new dynamic routes
        for path in new_routes:
            self._register_route(path)


def create_server() -> APIServer:
    """Factory function to create server instance"""
    return APIServer(app)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    server = create_server()
    server.run(port=port)
