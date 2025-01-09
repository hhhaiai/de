import json
import multiprocessing
import os
import random
import string
import time
from json.decoder import JSONDecodeError
from typing import Dict, Any, List

import tiktoken
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.responses import HTMLResponse

import degpt as dg

app = FastAPI(
    title="ones",
    description="High-performance API service",
    version="1.0.0|2025.1.6"
)
# debug for Log
debug = False


class APIServer:
    """High-performance API server implementation"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self._setup_routes()
        self.scheduler = BackgroundScheduler()
        self._schedule_route_check()
        self.scheduler.start()

    def _setup_routes(self) -> None:
        """Initialize API routes"""

        # 修改根路由的重定向实现
        @self.app.get("/", include_in_schema=False)
        async def root():
            # # 添加状态码和确保完整URL
            # return RedirectResponse(
            #     url="/web",
            #     status_code=302  # 添加明确的重定向状态码
            # )
            return HTMLResponse(content="<h1>hello. It's home page.</h1>")

        # 修改 web 路由的返回类型
        @self.app.get("/web")
        async def web():
            # # 返回 JSONResponse 或 HTML 内容
            # return JSONResponse(content={"message": "hello. It's web page."})
            ## 或者返回HTML内容
            return HTMLResponse(content="<h1>hello. It's web page.</h1>")

        @self.app.get("/api/v1/models")
        async def models() -> str:
            models_str = dg.get_models()  # Get the JSON string
            models_json = json.loads(models_str)  # Convert it back to a Python object
            return JSONResponse(content=models_json)  # Return as JSON response

        routes = self._get_routes()
        for path in routes:
            self._register_route(path)

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
                headers = dict(request.headers)
                data = await request.json()
                if debug:
                    print(f"Request received...\r\n\tHeaders: {headers},\r\n\tData: {data}")
                return await self._generate_response(headers, data)
            except JSONDecodeError as e:
                if debug:
                    print(f"JSON decode error: {e}")
                raise HTTPException(status_code=400, detail="Invalid JSON format") from e
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

    async def _generate_response(self, headers: Dict[str, str], data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate API response"""
        global debug
        try:
            # check model
            model = data.get("model")
            # print(f"model: {model}")
            # just auto will check
            if "auto" == model:
                model = dg.get_auto_model(model)
            # else:
            #     if not dg.is_model_available(model):
            #         raise HTTPException(status_code=400, detail="Invalid Model")
            # ## kuan
            # model = dg.get_model_by_autoupdate(model)

            # must has token ? token check
            authorization = headers.get('Authorization')
            token = os.getenv("TOKEN", "")
            # Check if the token exists and is not in the Authorization header.
            if token and token not in authorization:
                return "Token not in authorization header"

            # call ai
            msgs = data.get("messages")
            if debug:
                print(f"req messages: {msgs}")
            result = dg.chat_completion_messages(messages=msgs, model=model)
            if debug:
                print(f"result: {result}---- {self.is_chatgpt_format(result)}")

            # # Assuming this 'result' comes from your model or some other logic
            # result = "This is a test result."

            # If the request body data already matches ChatGPT format, return it directly
            if self.is_chatgpt_format(result):
                response_data = self.process_result(result,
                                                    model)  # If data already follows ChatGPT format, use it directly
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
            if debug:
                print(f"Response generation error: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

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

    def _schedule_route_check(self) -> None:
        """
        Schedule tasks to check and reload routes and models at regular intervals.
        - Reload routes every 30 seconds.
        - Reload models every 30 minutes.
        """
        # Scheduled Task 1: Check and reload routes every 30 seconds
        # Calls _reload_routes_if_needed method to check if routes need to be updated
        self.scheduler.add_job(self._reload_routes_if_needed, 'interval', seconds=30)

        # Scheduled Task 2: Reload models every 30 minutes (1800 seconds)
        # This task will check and update the model data periodically
        self.scheduler.add_job(self._reload_check, 'interval', seconds=60 * 30)
        pass

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

    def _reload_routes(self, new_routes: List[str]) -> None:
        """Reload the routes based on the updated configuration"""
        # Clear existing routes
        self.app.routes.clear()
        # Register new routes
        for path in new_routes:
            self._register_route(path)


def create_server() -> APIServer:
    """Factory function to create server instance"""
    return APIServer(app)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    server = create_server()
    server.run(port=port)
