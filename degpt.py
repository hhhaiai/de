"""
update time: 2025.01.09
verson: 0.1.125
"""

import time
import requests
import asyncio
from playwright.async_api import async_playwright
import json
import logging
import re
from typing import List, Dict

# 全局变量
last_request_time = 0  # 上次请求的时间戳
cache_duration = 14400  # 缓存有效期，单位：秒 (4小时)
cached_models = {
    "object": "list",
    "data": [],
    "version": "",
    "provider": "",
    "time": 0
}  # 用于存储缓存的模型数据

addrs = [{
    "name": "America",
    "url": "https://usa-chat.degpt.ai/api"
}, {
    "name": "Singapore",
    "url": "https://singapore-chat.degpt.ai/api"
}, {
    "name": "Korea",
    "url": "https://korea-chat.degpt.ai/api"
}]


def reload_check():
    """ reload model for this project"""
    get_models()


def get_models():
    """获取所有模型的 JSON 数据"""
    global cached_models, last_request_time

    current_time = time.time()

    # 确保cached_models已初始化
    if cached_models is None:
        cached_models = {
            "object": "list",
            "data": [],
            "version": "",
            "provider": "",
            "time": 0
        }

    # 检查缓存是否过期
    if (current_time - last_request_time) > cache_duration:
        try:
            asyncio.run(get_model_names_from_js())
            get_alive_models()
            last_request_time = current_time
        except Exception as e:
            print(f"更新模型数据异常: {e}", exc_info=True)
    return json.dumps(cached_models)


def get_alive_models():
    """
    获取活的模型版本，并更新全局缓存
    """
    global cached_models, last_request_time

    # 发送 GET 请求
    url = 'https://www.degpt.ai/api/config'
    headers = {'Content-Type': 'application/json'}

    response = requests.get(url, headers=headers)

    # 检查响应是否成功
    if response.status_code == 200:
        try:
            data = response.json()  # 解析响应 JSON 数据
            default_models = data.get("default_models", "").split(",")  # 获取默认模型并分割成列表

            # 获取当前时间戳（以秒为单位）
            timestamp_in_seconds = time.time()
            # 转换为毫秒（乘以 1000）
            timestamp_in_milliseconds = int(timestamp_in_seconds * 1000)

            # 根据 default_models 生成 models 数据结构
            # models = {
            #     "object": "list",
            #     "version": data.get("version", ""),
            #     "provider": data.get("name", ""),
            #     "time": timestamp_in_milliseconds,
            #     "data": []
            # }
            #
            # for model in default_models:
            #     models["data"].append({
            #         "id": model.strip(),
            #         "object": "model",
            #         "created": 0,
            #         "owned_by": model.split("-")[0]  # 假设所有模型的所有者是模型名的前缀
            #     })
            if default_models:
                # print("\n提取的模型列表:")
                existing_ids = {m.get('id') for m in cached_models["data"]}
                for model_id in default_models:

                    if model_id and model_id not in existing_ids:
                        model_data = {
                            "id": model_id,
                            "object": "model",
                            "model": model_id,
                            "created": timestamp_in_milliseconds,
                            "owned_by": model_id.split("-")[0] if "-" in model_id else "unknown",
                            "name": model_id,
                            "description": '',
                            "support": '',
                            "tip": ''
                        }
                        cached_models["data"].append(model_data)
            # 更新全局缓存
            last_request_time = timestamp_in_seconds  # 更新缓存时间戳

            # print("获取新的模型数据:", models)
        except json.JSONDecodeError as e:
            print("JSON 解码错误:", e)
    else:
        print(f"请求失败，状态码: {response.status_code}")


def parse_models_from_js(js_content: str) -> List[Dict]:
    """解析JS内容中的模型信息"""
    try:
        pattern = r'models\s*:\s*\[([^\]]+)\]'
        match = re.search(pattern, js_content)
        if match:
            models_data = match.group(1)
            models_data = re.sub(r'(\w+):', r'"\1":', models_data)
            models_data = models_data.replace("'", '"')
            models_data = f"[{models_data}]"

            try:
                models = json.loads(models_data)
                # print(f"成功解析到 {len(models)} 个模型信息")
                return models
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {str(e)}")
                return []
        return []
    except Exception as e:
        print(f"解析模型信息时发生错误: {str(e)}")
        return []


async def get_model_names_from_js(url="https://www.degpt.ai/", timeout: int = 60):
    global cached_models
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox']
            )
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0 Safari/537.36'
            )
            page = await context.new_page()

            async def handle_response(response):
                try:
                    if response.request.resource_type == "script":
                        content_type = response.headers.get('content-type', '').lower()
                        if 'javascript' in content_type:
                            js_content = await response.text()
                            if 'models' in js_content and 'DeepSeek' in js_content:
                                # print(f"找到包含模型信息的JS文件: {response.url}")
                                models = parse_models_from_js(js_content)
                                if models:
                                    # print("\n提取的模型列表:")
                                    existing_ids = {m.get('id') for m in cached_models["data"]}
                                    for model in models:
                                        model_id = model.get('model', '').strip()
                                        # print(f"- 名称: {model.get('name', '')}")
                                        # print(f"  模型: {model.get('model', '')}")
                                        # print(f"  描述: {model.get('desc', '')}")

                                        if model_id and model_id not in existing_ids:
                                            model_data = {
                                                "id": model_id,
                                                "object": "model",
                                                "model": model_id,
                                                "created": int(time.time()),
                                                "owned_by": model_id.split("-")[0] if "-" in model_id else "unknown",
                                                "name": model.get('name', ''),
                                                "description": model.get('desc', ''),
                                                "support": model.get('support', 'text'),
                                                "tip": model.get('tip', '')
                                            }
                                            cached_models["data"].append(model_data)
                                            # print(f"添加新模型: {model_id}")
                except Exception as e:
                    print(f"处理响应时发生错误: {str(e)}")
                    logging.error(f"Response处理异常: {e}", exc_info=True)

            page.on("response", handle_response)

            try:
                await page.goto(url, timeout=timeout * 1000, wait_until='networkidle')
                await page.wait_for_timeout(5000)
            except Exception as e:
                print(f"页面加载错误: {str(e)}")
                logging.error(f"页面加载异常: {e}", exc_info=True)
            finally:
                await browser.close()
    except Exception as e:
        print(f"提取过程发生错误: {str(e)}")
        logging.error(f"提取过程异常: {e}", exc_info=True)
        raise


def is_model_available(model_id):
    # Get the models JSON
    models_json = get_models()

    # Parse the JSON string into a Python dictionary
    models_data = json.loads(models_json)

    # Loop through the model list to check if the model ID exists
    for model in models_data.get("data", []):
        if model["id"] == model_id:
            return True  # Model ID found

    return False  # Model ID not found


def get_auto_model(model=None):
    """
    Get the ID of the first model from the list of default models.
    If model is provided, return that model's ID; otherwise, return the first model in the list.
    """
    models_data = json.loads(get_models())["data"]

    if model:
        # Check if the provided model is valid
        valid_ids = [model["id"] for model in models_data]
        if model in valid_ids:
            return model
        else:
            return models_data[0]["id"]  # If not valid, return the first model as fallback
    else:
        # Return the ID of the first model in the list if no model provided
        return models_data[0]["id"] if models_data else None


def get_model_by_autoupdate(model_id=None):
    """
    Check if the provided model_id is valid.
    If not, return the ID of the first available model as a fallback.

    Args:
        model_id (str): The ID of the model to check. If not provided or invalid, defaults to the first model.

    Returns:
        str: The valid model ID.
    """
    # Get all model data by parsing the models JSON
    models_data = json.loads(get_models())["data"]

    # Extract all valid model IDs from the data
    valid_ids = [model["id"] for model in models_data]

    # If the model_id is invalid or not provided, default to the ID of the first model
    if model_id not in valid_ids:
        model_id = models_data[0]["id"]  # Use the first model ID as the default

    # Get the model data corresponding to the model_id
    model_data = next((model for model in models_data if model["id"] == model_id), None)

    # Return the ID of the found model, or None if the model was not found
    return model_data["id"] if model_data else None


def chat_completion_message(
        user_prompt,
        user_id: str = None,
        session_id: str = None,
        system_prompt="You are a helpful assistant.",
        model="Pixtral-124B",
        project="DecentralGPT", stream=False,
        temperature=0.3, max_tokens=1024, top_p=0.5,
        frequency_penalty=0, presence_penalty=0):
    """未来会增加回话隔离: 单人对话,单次会话"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    return chat_completion_messages(messages, user_id, session_id, model, project, stream, temperature, max_tokens,
                                    top_p, frequency_penalty,
                                    presence_penalty)


def chat_completion_messages(
        messages,
        model="Pixtral-124B",
        user_id: str = None,
        session_id: str = None,
        project="DecentralGPT", stream=False, temperature=0.3, max_tokens=1024, top_p=0.5,
        frequency_penalty=0, presence_penalty=0):
    url = 'https://usa-chat.degpt.ai/api/v0/chat/completion/proxy'
    headers = {
        'sec-ch-ua-platform': '"macOS"',
        'Referer': 'https://www.degpt.ai/',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'sec-ch-ua': 'Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'DNT': '1',
        'Content-Type': 'application/json',
        'sec-ch-ua-mobile': '?0'
    }
    payload = {
        # make sure ok
        "model": model,
        "messages": messages,
        "project": project,
        "stream": stream,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty

    }
    # print(json.dumps(headers, indent=4))
    # print(json.dumps(payload, indent=4))
    return chat_completion(url, headers, payload)


def chat_completion(url, headers, payload):
    """处理用户请求并保留上下文"""
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.encoding = 'utf-8'
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return "请求失败，请检查网络或参数配置。"
    except (KeyError, IndexError) as e:
        print(f"解析响应时出错: {e}")
        return "解析响应内容失败。"
    return {}


def is_chatgpt_format(data):
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


if __name__ == '__main__':
    # asyncio.run(get_model_names_from_js())
    print(get_models())
#
#     # # support Chinese
#     # if isinstance(response_content, str):  # 如果已经是 JSON 字符串
#     #     return Response(response_content, content_type="application/json; charset=utf-8")
