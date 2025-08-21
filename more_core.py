import json
import multiprocessing
import os
import random
import string
import time
from typing import Dict, Any, List

import tiktoken
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.responses import HTMLResponse
# 禁用 SSL 警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import degpt as dg

# debug for Log
debug = False

app = FastAPI(
    title="ones",
    description="High-performance API service",
    version="1.2.3|2025.08.21"
)


class APIServer:
    """High-performance API server implementation"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self._setup_routes()
        self._setup_scheduler()

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

        @self.app.get("/web", name="web")
        def web():
            return HTMLResponse(content="<h1>hello. It's web page.</h1>")

        @self.app.get("/health", name="health")
        def health():
            return JSONResponse(content={"status": "working"})


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

        @self.app.get("/api/v1/models", name="apimodels")
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
                if debug:
                    print("Claude protocol request received...")
                headers = dict(request.headers)
                data = await request.json()
                if debug:
                    print(f"Claude request data: {data}")
                
                # 转换Claude格式到OpenAI格式
                openai_data = self._convert_claude_to_openai(data, headers)
                
                # 使用现有的OpenAI处理逻辑
                response = self._generate_response(headers, openai_data)
                
                # 转换回Claude格式
                claude_response = self._convert_openai_to_claude(response)
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

        return [default_path]

    def _register_route(self, path: str) -> None:
        """Register a single API route"""
        global debug

        async def chat_endpoint(request: Request) -> Dict[str, Any]:
            try:
                if debug:
                    print(f"Request chat_endpoint...")
                headers = dict(request.headers)
                data = await request.json()
                if debug:
                    print(f"Request received...\r\n\tHeaders: {headers},\r\n\tData: {data}")
                return self._generate_response(headers, data)
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
        """Convert Claude format to OpenAI format"""
        # Claude格式示例:
        # {
        #   "model": "claude-3-sonnet-20240229",
        #   "messages": [{"role": "user", "content": "Hello"}],
        #   "max_tokens": 1024,
        #   "stream": false
        # }
        
        openai_data = {
            "model": claude_data.get("model", "gpt-4o-mini"),
            "messages": claude_data.get("messages", []),
            "stream": claude_data.get("stream", False)
        }
        
        # 处理session_id和user_id
        session_id = claude_data.get("session_id")
        user_id = claude_data.get("user_id")
        if session_id:
            openai_data["session_id"] = session_id
        if user_id:
            openai_data["user_id"] = user_id
        
        # 处理max_tokens
        max_tokens = claude_data.get("max_tokens")
        if max_tokens:
            openai_data["max_tokens"] = max_tokens
            
        return openai_data

    def _convert_openai_to_claude(self, openai_response: Dict) -> Dict:
        """Convert OpenAI format to Claude format"""
        # OpenAI格式:
        # {
        #   "id": "chatcmpl-123",
        #   "object": "chat.completion",
        #   "created": 1677652288,
        #   "model": "gpt-4o-mini",
        #   "choices": [{
        #     "index": 0,
        #     "message": {
        #       "role": "assistant",
        #       "content": "Hello! How can I help you?"
        #     },
        #     "finish_reason": "stop"
        #   }],
        #   "usage": {"prompt_tokens": 9, "completion_tokens": 12, "total_tokens": 21}
        # }
        
        # Claude格式:
        # {
        #   "id": "msg_123",
        #   "type": "message",
        #   "role": "assistant",
        #   "content": [{"type": "text", "text": "Hello! How can I help you?"}],
        #   "model": "claude-3-sonnet-20240229",
        #   "stop_reason": "end_turn",
        #   "stop_sequence": null,
        #   "usage": {"input_tokens": 9, "output_tokens": 12}
        # }
        
        if not isinstance(openai_response, dict):
            return {
                "id": f"msg_{int(time.time() * 1000)}",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": str(openai_response)}],
                "model": "claude-3-sonnet-20240229",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 0, "output_tokens": 0}
            }
        
        # 提取消息内容
        content = ""
        if "choices" in openai_response and openai_response["choices"]:
            choice = openai_response["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                content = choice["message"]["content"]
        
        # 提取使用情况
        input_tokens = 0
        output_tokens = 0
        if "usage" in openai_response:
            input_tokens = openai_response["usage"].get("prompt_tokens", 0)
            output_tokens = openai_response["usage"].get("completion_tokens", 0)
        
        # 构建Claude响应
        claude_response = {
            "id": openai_response.get("id", f"msg_{int(time.time() * 1000)}"),
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": content}],
            "model": openai_response.get("model", "claude-3-sonnet-20240229"),
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }
        }
        
        return claude_response

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

    def _generate_response(self, headers: Dict[str, str], data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate API response"""
        global debug
        if debug:
            print("inside _generate_response")
        try:
            # check model
            model = data.get("model")
            # print(f"model: {model}")
            # just auto will check
            if "auto" == model:
                model = dg.get_auto_model()
            else:
                model = dg.get_model_by_autoupdate(model)
            # must has token ? token check
            authorization = headers.get('Authorization')
            token = os.getenv("TOKEN", "")
            if token and token not in authorization:
                raise HTTPException(status_code=401, detail="无效的Token")

            # call ai
            msgs = data.get("messages")
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
                print(f"request model: {model}")
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
                    model=model,
                    session_id=session_id,
                    stream=True
                )
                
                # 返回流式响应
                return StreamingResponse(
                    self._stream_response(response),
                    media_type="text/event-stream"
                )
            else:
                # 非流式响应处理
                result = dg.chat_completion_messages(
                    messages=msgs,
                    model=model,
                    session_id=session_id,
                    stream=False
                )
                if debug:
                    print(f"result: {result}---- {self.is_chatgpt_format(result)}")

                # If the request body data already matches ChatGPT format, return it directly
                if self.is_chatgpt_format(result):
                    # If data already follows ChatGPT format, use it directly
                    response_data = self.process_result(result, model)
                else:
                    # Calculate the current timestamp
                    current_timestamp = int(time.time() * 1000)
                    # Otherwise, calculate the tokens and return a structured response
                    prompt_tokens = self._calculate_tokens(str(data))
                    completion_tokens = self._calculate_tokens(result)
                    total_tokens = prompt_tokens + completion_tokens

                    response_data = {
                        "id": self._generate_id(),
                        "object": "chat.completion",
                        "created": current_timestamp,
                        "model": data.get("model", "gpt-4o"),
                        "usage": {
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": total_tokens
                        },
                        "choices": [{
                            "message": {
                                "role": "assistant",
                                "content": result
                            },
                            "finish_reason": "stop",
                            "index": 0
                        }]
                    }

                # Print the response for debugging (you may remove this in production)
                if debug:
                    print(f"Response Data: {response_data}")

                return response_data
        except Exception as e:
            dg.record_call(model,False)
            if debug:
                print(f"Response generation error: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def _stream_response(self, response):
        """流式传输响应数据"""
        try:
            # 直接转发来自后端API的SSE流
            for chunk in response.iter_lines():
                if chunk:
                    yield chunk.decode('utf-8') + "\n"
        except Exception as e:
            yield f"data: {{\"error\": \"Stream error: {str(e)}\"}}\n\n"

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

        return uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            workers=workers,
            loop="uvloop",
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
        if [route.path for route in current_routes] != new_routes:
            if debug:
                print("Routes changed, reloading...")
            self._reload_routes(new_routes)

    # def _reload_routes(self, new_routes: List[str]) -> None:
    #     """Reload the routes based on the updated configuration"""
    #     # Clear existing routes
    #     self.app.routes.clear()
    #     # Register new routes
    #     for path in new_routes:
    #         self._register_route(path)

    def _reload_routes(self, new_routes: List[str]) -> None:
        """Reload only dynamic routes while preserving static ones"""
        # Define static route names
        static_routes = {"root", "web", "health", "models", "apimodels", "clear_session", "claude_messages"}

        # Remove only dynamic routes
        self.app.routes[:] = [
            route for route in self.app.routes
            if not hasattr(route, 'name') or route.name in static_routes
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
