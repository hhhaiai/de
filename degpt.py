"""
update time: 2025.01.07
verson: 0.1.125
"""

import json
import time
import requests
import re
import ast

# 全局变量
last_request_time = 0  # 上次请求的时间戳
cache_duration = 14400  # 缓存有效期，单位：秒 (4小时)
cached_models = None  # 用于存储缓存的模型数据

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
        get_model_names_from_js()

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

            # print("获取新的模型数据:", models)
        except json.JSONDecodeError as e:
            print("JSON 解码错误:", e)
    else:
        print(f"请求失败，状态码: {response.status_code}")


def get_model_names_from_js():
    global cached_models

    # 获取 JavaScript 文件内容
    url = "https://www.degpt.ai/_app/immutable/chunks/index.4aecf75a.js"
    response = requests.get(url)

    # 检查请求是否成功
    if response.status_code == 200:
        js_content = response.text

        # 查找 'models' 的部分
        pattern = r'models\s*:\s*\[([^\]]+)\]'
        match = re.search(pattern, js_content)

        if match:
            # 提取到的 models 部分
            models_data = match.group(1)

            # 添加双引号到键名上
            models_data = re.sub(r'(\w+):', r'"\1":', models_data)

            # 将所有单引号替换为双引号（防止 JSON 格式错误）
            models_data = models_data.replace("'", '"')

            # 将字符串转换为有效的 JSON 数组格式
            models_data = f"[{models_data}]"

            try:
                # 解析为 Python 数据结构（列表）
                models = json.loads(models_data)

                # 提取模型名称
                model_names = [model['model'] for model in models]

                # 获取现有模型 ID 列表
                existing_ids = {model["id"] for model in cached_models["data"]}

                # 仅添加新的模型
                for model_name in model_names:
                    model_id = model_name.strip()
                    if model_id not in existing_ids:
                        cached_models["data"].append({
                            "id": model_id,
                            "object": "model",
                            "created": 0,  # 假设创建时间为0，实际情况请根据需要调整
                            "owned_by": model_id.split("-")[0]  # 假设所有模型的所有者是模型名的前缀
                        })
                # # 打印更新后的 cached_models
                # print(json.dumps(cached_models, indent=4))
            except json.JSONDecodeError as e:
                print("JSON 解码错误:", e)


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


# if __name__ == '__main__':
#     print(get_models())
#     mgs = [{"role": "system",
#             "content": "### Role\n\n你是一个专业的政治专家，请根据以下标准对输入的图片进行分类识别文章是否有政治风险，并给出相应的分类结果。\n在输出相关程度后，请根据图片内容，给出图片的相关描述，简单描述图片中提到的政治相关内容；\n\n### Workflow\n\n政治 内容包括但不仅限于以下内容\n所在国和敏感地区 中华人民共和国、中国、台湾、新疆、西藏相关的地图、标语、旗帜；\n以及政治人物和他们的照片头像 如：习近平、毛泽东、江泽民、曾庆红、常委、政治委员、总书记、军委主席、国家主席的照片、头像和漫画形象；\n以及政党、军队的照片、文字、旗帜、徽章和标志 如：共产党党徽、党旗、国徽、国旗、中南海正门、解放军军旗等；\n以及已经明确的内部反对势力和他们的特殊称呼 如：疆独、藏独、港独、台独、东突、法轮功、邪教、游行、示威、8964、白纸运动的图片、标语、旗帜；\n以及一些含有政治文字的图片 如：分裂国家、煽动颠覆、颠覆国家政权、政变等文字的图片；\n相关程度分为以下4种：\n1. **高度风险**：这张图片明显涉及政治。\n2. **有风险**：这张图片明有较大概率涉及政治。\n3. **涉及**：这张图片可能含有与政治有关的内容，但是无法明确定性。\n4. **无关**：这张图片没有任何与政治相关的内容。\n请根据以上标准对图片进行分析，并给出相应的相关性评级；如果相关请总结出图片中涉及的中国政治相关内容，并给出相关描述；\n\n### Example\n\n相关程度：**高度风险**\n\n涉及内容：台独，未吧台湾标记为中国领土。"},
#            {"role": "user", "content": [{"type": "text", "text": "这个图片是什么？"}, {"type": "image_url",
#                                                                                       "image_url": {
#                                                                                           "url": "https://dcdn.simitalk.com/n/cnv0rhttwcqq/b/bucket-im-test/o/community/im-images/2025-01-08/rgwqu-1736334050250-17E7748A-8DE2-47E6-BC44-1D65C8EAAEE6.jpg"}}]}]
#     res = chat_completion_messages(messages=mgs, model="Pixtral-124B")
#     # res = chat_completion_messages(messages=mgs,model="QVQ-72B-Preview")
#     print(res)
