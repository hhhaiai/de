"""
update time: 2025.01.07
verson: 0.1.125
"""

import json
import time

import requests

# 全局变量
last_request_time = 0  # 上次请求的时间戳
cache_duration = 14400  # 缓存有效期，单位：秒 (4小时)
cached_models = None  # 用于存储缓存的模型数据

addrs=[{
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
    """
    获取所有模型的 JSON 数据
    """
    # 如果缓存有效，直接返回缓存的数据
    global cached_models, last_request_time

    # 获取当前时间戳（以秒为单位）
    current_time = time.time()

    # 判断缓存是否过期（4小时）
    if cached_models is None or (current_time - last_request_time) > cache_duration:
        # 如果缓存过期或为空，重新获取模型数据
        get_alive_models()

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
        data = response.json()  # 解析响应 JSON 数据
        default_models = data.get("default_models", "").split(",")  # 获取默认模型并分割成列表

        # 获取当前时间戳（以秒为单位）
        timestamp_in_seconds = time.time()
        # 转换为毫秒（乘以 1000）
        timestamp_in_milliseconds = int(timestamp_in_seconds * 1000)

        # 根据 default_models 生成 models 数据结构
        models = {
            "object": "list",
            "version": data.get("version", ""),
            "provider": data.get("name", ""),
            "time": timestamp_in_milliseconds,
            "data": []
        }

        for model in default_models:
            models["data"].append({
                "id": model.strip(),
                "object": "model",
                "created": 0,
                "owned_by": model.split("-")[0]  # 假设所有模型的所有者是模型名的前缀
            })

        # 更新全局缓存
        cached_models = models
        last_request_time = timestamp_in_seconds  # 更新缓存时间戳

        print("获取新的模型数据:", models)
    else:
        print(f"请求失败，状态码: {response.status_code}")


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
        model="Llama3.3-70B",
        project="DecentralGPT", stream=False,
        temperature=0.3, max_tokens=1024, top_p=0.5,
        frequency_penalty=0, presence_penalty=0):
    """未来会增加回话隔离: 单人对话,单次会话"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    return chat_completion_messages(messages,user_id,session_id, model, project, stream, temperature, max_tokens, top_p, frequency_penalty,
                                    presence_penalty)


def chat_completion_messages(
        messages,
        model="Llama3.3-70B",
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
        "model": get_model_by_autoupdate(model),
        "messages": messages,
        "project": project,
        "stream": stream,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty

    }
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



    # # support Chinese
    # if isinstance(response_content, str):  # 如果已经是 JSON 字符串
    #     return Response(response_content, content_type="application/json; charset=utf-8")
