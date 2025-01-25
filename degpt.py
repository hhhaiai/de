"""
update time: 2025.01.09
verson: 0.1.125
"""
import json
import re
import time
from datetime import datetime, timedelta
import aiohttp
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Set, Optional, List, Dict

# 禁用 SSL 警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


debug = False
# 全局变量
last_request_time = 0  # 上次请求的时间戳
cache_duration = 14400  # 缓存有效期，单位：秒 (4小时)
'''用于存储缓存的模型数据'''
cached_models = {
    "object": "list",
    "data": [],
    "version": "0.1.125",
    "provider": "DeGPT",
    "name": "DeGPT",
    "default_locale": "en-US",
    "status": True,
    "time": 0
}

'''基础请求地址'''
base_addrs = [
    # "America"
    "https://usa-chat.degpt.ai/api",
    # "Singapore"
    "https://singapore-chat.degpt.ai/api",
    # "Korea"
    "https://korea-chat.degpt.ai/api"
]
'''基础域名'''
base_url = 'https://singapore-chat.degpt.ai/api'

'''基础模型'''
base_model = "Pixtral-124B"
# 全局变量：存储所有模型的统计信息
# 格式：{model_name: {"calls": 调用次数, "fails": 失败次数, "last_fail": 最后失败时间}}
MODEL_STATS: Dict[str, Dict] = {}

def record_call(model_name: str, success: bool = True) -> None:
    """
    记录模型调用情况
    Args:
        model_name: 模型名称
        success: 调用是否成功
    """
    global MODEL_STATS
    if model_name not in MODEL_STATS:
        MODEL_STATS[model_name] = {"calls": 0, "fails": 0, "last_fail": None}

    stats = MODEL_STATS[model_name]
    stats["calls"] += 1
    if not success:
        stats["fails"] += 1
        stats["last_fail"] = datetime.now()


def get_auto_model(cooldown_seconds: int = 300) -> str:
    """异步获取最优模型"""
    try:
        if not MODEL_STATS:
            get_models()

        best_model = None
        best_rate = -1.0
        now = datetime.now()

        for name, stats in MODEL_STATS.items():
            if stats.get("last_fail") and (now - stats["last_fail"]) < timedelta(seconds=cooldown_seconds):
                continue

            total_calls = stats["calls"]
            if total_calls > 0:
                success_rate = (total_calls - stats["fails"]) / total_calls
                if success_rate > best_rate:
                    best_rate = success_rate
                    best_model = name

        default_model = best_model or base_model
        if debug:
            print(f"选择模型: {default_model}")
        return default_model
    except Exception as e:
        if debug:
            print(f"模型选择错误: {e}")
        return base_model


def reload_check():
    """检查并更新系统状态
    1. 如果模型数据为空，更新模型数据
    2. 测试当前base_url是否可用，不可用则切换
    """
    global base_url, cached_models

    try:
        # 检查模型数据
        if not cached_models["data"]:
            if debug:
                print("模型数据为空，开始更新...")
            get_models()

        # 测试用例 - 平衡效率和功能验证
        test_payload = {
            "model": base_model,
            "messages": [{
                "role": "user",
                "content": [{"type": "text", "text": "test"}]
            }],
            "temperature": 0.7,
            "max_tokens": 50,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "project": "DecentralGPT",
            "stream": True
        }

        headers = {
            'Accept': '*/*',
            'Content-Type': 'application/json'
        }

        with aiohttp.ClientSession() as session:
            # 测试当前URL
            try:
                with session.post(
                        f"{base_url}/v0/chat/completion/proxy",
                        headers=headers,
                        json=test_payload,
                        timeout=5  # 较短的超时时间提高效率
                ) as response:
                    if response.status == 200:
                        # 验证响应格式
                        if response.read():
                            if debug:
                                print(f"当前URL可用: {base_url}")
                            return
            except Exception as e:
                if debug:
                    print(f"当前URL不可用: {e}")

            # 测试其他URL
            for url in base_addrs:
                if url == base_url:
                    continue
                try:
                    with session.post(
                            f"{url}/v0/chat/completion/proxy",
                            headers=headers,
                            json=test_payload,
                            timeout=5
                    ) as response:
                        if response.status == 200 and response.read():
                            base_url = url
                            if debug:
                                print(f"切换到新URL: {base_url}")
                            return
                except Exception as e:
                    if debug:
                        print(f"URL {url} 测试失败: {e}")
                    continue

            if debug:
                print("所有URL不可用，保持当前URL")

    except Exception as e:
        if debug:
            print(f"系统检查失败: {e}")


def _fetch_and_update_models():
    """Thread-safe model fetching and cache updating"""
    global cached_models
    try:
        get_from_js_v3()
    except Exception as e:
       print(f"{e}")
    try:
        get_alive_models()
    except Exception as e:
       print(f"{e}")


def get_models():
    """model data retrieval with thread safety"""
    global cached_models, last_request_time
    current_time = time.time()
    if (current_time - last_request_time) > cache_duration:
        try:
            # Update timestamp before awaiting to prevent concurrent updates
            last_request_time = current_time
            _fetch_and_update_models()
        except Exception as e:
            print(f"{e}")

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
            ## config
            cached_models['version']=data['version']
            cached_models['provider']=data['provider']
            cached_models['name']=data['provider']
            cached_models['time']=timestamp_in_milliseconds

            if default_models:
                # print("\n提取的模型列表:")
                existing_ids = {m.get('id') for m in cached_models["data"]}
                for model_id in default_models:
                    record_call(model_id)
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


###############


def get_from_js_v3():
    global cached_models
    models = analyze()
    # print(models)
    if models:
        # 获取已经存在的ID
        existing_ids = {m.get('id') for m in cached_models["data"]}
        for model in models:
            # {'name': 'Llama3.3', 'model': 'Llama3.3-70B', 'tip': 'Llama3.3', 'support': 'text', 'desc': 'Suitable for most tasks'}
            if debug:
                print(model)
            model_id = model.get('model', '').strip()
            if model_id and model_id not in existing_ids:
                model_data = {
                    "id": model_id,
                    "object": "model",
                    "model": model_id,
                    "created": int(time.time())*1000,
                    "owned_by": model_id.split("-")[0] if "-" in model_id else "unknown",
                    "name": model.get('name', ''),
                    "description": model.get('desc', ''),
                    "support": model.get('support', 'text'),
                    "tip": model.get('tip', '')
                }
                cached_models["data"].append(model_data)
                record_call(model_id)
                if debug:
                    print(f"添加新模型: {model_id}")
    pass


def fetch_content(url: str) -> Optional[str]:
    """获取页面内容"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        if debug:
            print(f"获取页面失败 {url}: {e}")
        return None


def parse_models_from_js(content: str, url: str) -> List[Dict]:
    """解析JS内容中的模型信息"""
    try:
        # 匹配模型数据
        pattern = r'models\s*:\s*\[([^\]]+)\]'
        match = re.search(pattern, content)

        if not match:
            return []

        # 处理JSON数据
        models_data = match.group(1)
        models_data = re.sub(r'(\w+):', r'"\1":', models_data)
        models_data = models_data.replace("'", '"')
        models_data = f"[{models_data}]"

        try:
            models = json.loads(models_data)
            if isinstance(models, list) and models and not (len(models) == 1 and not models[0]):
                # if debug:
                #     print(f"解析到模型数据:\n{json.dumps(models, indent=2)}")
                return models
        except json.JSONDecodeError:
            # 尝试修复JSON
            fixed_data = _fix_json_errors(models_data)
            try:
                return json.loads(fixed_data)
            except json.JSONDecodeError as e:
                if debug:
                    print(f"JSON解析失败 {url}: {e}")

        return []
    except Exception as e:
        if debug:
            print(f"解析模型失败 {url}: {e}")
        return []


def _fix_json_errors(json_str: str) -> str:
    """修复JSON格式错误"""
    # 移除注释
    json_str = re.sub(r'//.*?\n|/\*.*?\*/', '', json_str, flags=re.S)
    # 处理键名和值
    json_str = re.sub(r'(\w+)\s*:', r'"\1":', json_str)
    json_str = re.sub(r':\s*([^",\s\{\}\[\]]+)', r': "\1"', json_str)
    # 处理布尔值和null
    json_str = re.sub(r':\s*true\b', ': true', json_str)
    json_str = re.sub(r':\s*false\b', ': false', json_str)
    json_str = re.sub(r':\s*null\b', ': null', json_str)
    # 处理尾随逗号
    json_str = re.sub(r',(\s*[\]}])', r'\1', json_str)
    return json_str


#"""version2 """
def extract_links(content: str, url: str) -> Set[str]:
    """
    提取页面中的所有有效链接，处理特殊情况和无效URL

    Args:
        content: 页面内容
        url: 当前页面URL

    Returns:
        Set[str]: 提取的有效链接集合
    """
    links = set()
    base_domain = urlparse(url).netloc

    def is_valid_path(path: str) -> bool:
        """
        验证路径是否有效

        Args:
            path: 要验证的路径

        Returns:
            bool: 路径是否有效
        """
        # 排除无效路径模式
        invalid_patterns = [
            r'\$\{.*?\}',  # 模板字面量
            r'\{.*?\}',  # 其他变量
            r'^\(.*?\)',  # 括号开头
            r'^\).*?',  # 右括号开头
            r'^[\s\.,]+$',  # 仅包含空白或标点
            r'^[a-z]+\=',  # 属性赋值
            r'^\w+\(',  # 函数调用
        ]

        if not path or path.isspace():
            return False

        return not any(re.search(pattern, path) for pattern in invalid_patterns)

    def clean_path(path: str) -> Optional[str]:
        """
        清理和规范化路径

        Args:
            path: 原始路径

        Returns:
            Optional[str]: 清理后的路径，无效则返回None
        """
        if not path:
            return None

        # 基础清理
        path = path.strip()
        path = re.sub(r'\s+', '', path)
        path = re.sub(r'[\(\)]', '', path)
        path = re.sub(r',.*$', '', path)

        # 处理相对路径
        if path.startswith('./'):
            path = path[2:]
        elif path.startswith('/'):
            path = path[1:]

        # 验证文件扩展名
        valid_extensions = ('.js', '.css', '.html', '.htm', '.json')
        if not any(path.endswith(ext) for ext in valid_extensions):
            return None

        return path

    try:
        if not content or url.endswith(('.json', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg')):
            return links

        # 处理HTML内容
        soup = BeautifulSoup(content, 'html.parser')

        # 提取href链接
        for tag in soup.find_all(href=True):
            href = tag['href']
            if is_valid_path(href):
                cleaned_href = clean_path(href)
                if cleaned_href:
                    full_url = urljoin(url, cleaned_href)
                    if urlparse(full_url).netloc == base_domain:
                        links.add(full_url)
                        if debug:
                            print(f"添加有效链接: {full_url}")

        # 处理script标签
        for tag in soup.find_all('script', src=True):
            src = tag['src']
            if is_valid_path(src):
                cleaned_src = clean_path(src)
                if cleaned_src:
                    full_url = urljoin(url, cleaned_src)
                    if urlparse(full_url).netloc == base_domain:
                        links.add(full_url)

        # 处理JS文件内容
        if url.endswith('.js'):
            # 处理各种导入模式
            import_patterns = [
                (r'import\s*[^"\']*["\']([^"\']+)["\']', 1),
                (r'from\s+["\']([^"\']+)["\']', 1),
                (r'import\s*\(["\']([^"\']+)["\']\)', 1),
                (r'require\s*\(["\']([^"\']+)["\']\)', 1),
                (r'(?:url|src|href)\s*:\s*["\']([^"\']+)["\']', 1),
                (r'@import\s+["\']([^"\']+)["\']', 1),
                (r'url\(["\']?([^"\'()]+)["\']?\)', 1),
            ]

            for pattern, group in import_patterns:
                for match in re.finditer(pattern, content):
                    path = match.group(group)
                    if is_valid_path(path):
                        cleaned_path = clean_path(path)
                        if cleaned_path:
                            full_url = urljoin(url, cleaned_path)
                            if urlparse(full_url).netloc == base_domain:
                                links.add(full_url)

            # 处理数组形式的导入
            for array_match in re.finditer(r'\[([\s\S]*?)\]', content):
                array_content = array_match.group(1)
                paths = re.findall(r'["\']([^"\']+?\.[a-zA-Z0-9]+)["\']', array_content)
                for path in paths:
                    if is_valid_path(path):
                        cleaned_path = clean_path(path)
                        if cleaned_path and not cleaned_path.startswith(('http:', 'https:', 'data:', 'blob:')):
                            full_url = urljoin(url, cleaned_path)
                            if urlparse(full_url).netloc == base_domain:
                                links.add(full_url)

    except Exception as e:
        if debug:
            print(f"提取链接失败 {url}: {e}")

    return links


def analyze(_bb_url="https://www.degpt.ai/") -> List[Dict]:
    """分析网站内容"""
    visited_urls = set()
    found_models = []

    def _analyze(url: str) -> bool:
        if url in visited_urls:
            return False

        visited_urls.add(url)
        if debug:
            print(f"正在分析: {url}")

        content = fetch_content(url)
        if not content:
            return False

        models = parse_models_from_js(content, url)
        if models:
            found_models.extend(models)
            return True

        for link in extract_links(content, url):
            if _analyze(link):
                return True

        return False

    _analyze(_bb_url)
    return found_models



################

def is_model_available(model_id: str, cooldown_seconds: int = 300) -> bool:
    """
    判断模型是否在模型列表中且非最近失败的模型

    Args:
        model_id: 模型ID，需要检查的模型标识符
        cooldown_seconds: 失败冷却时间（秒），默认300秒

    Returns:
        bool: 如果模型可用返回True，否则返回False

    Note:
        - 当MODEL_STATS为空时会自动调用get_models()更新数据
        - 检查模型是否在冷却期内，如果在冷却期则返回False
    """
    global MODEL_STATS

    # 如果MODEL_STATS为空，加载模型数据
    if not MODEL_STATS:
        get_models()

    # 检查模型是否在统计信息中
    if model_id not in MODEL_STATS:
        return False

    # 检查是否在冷却期内
    stats = MODEL_STATS[model_id]
    if stats["last_fail"]:
        time_since_failure = datetime.now() - stats["last_fail"]
        if time_since_failure < timedelta(seconds=cooldown_seconds):
            return False

    return True


def get_model_by_autoupdate(model_id: Optional[str] = None, cooldown_seconds: int = 300) -> Optional[str]:
    """
    检查提供的model_id是否可用，如果不可用则返回成功率最高的模型

    Args:
        model_id: 指定的模型ID，可选参数
        cooldown_seconds: 失败冷却时间（秒），默认300秒

    Returns:
        str | None: 返回可用的模型ID，如果没有可用模型则返回None

    Note:
        - 当MODEL_STATS为空时会自动调用get_models()更新数据
        - 如果指定的model_id可用，则直接返回
        - 如果指定的model_id不可用，则返回成功率最高的模型
    """
    global MODEL_STATS

    # 如果MODEL_STATS为空，加载模型数据
    if not MODEL_STATS:
        get_models()

    # 如果提供了model_id且可用，直接返回
    if model_id and is_model_available(model_id, cooldown_seconds):
        return model_id

    # 否则返回成功率最高的可用模型
    return get_auto_model(cooldown_seconds=cooldown_seconds)


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


def chat_completion_message(
        user_prompt,
        user_id: str = None,
        session_id: str = None,
        system_prompt="You are a helpful assistant.",
        model=base_model,
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
        model=base_model,
        user_id: str = None,
        session_id: str = None,
        project="DecentralGPT", stream=False, temperature=0.3, max_tokens=1024, top_p=0.5,
        frequency_penalty=0, presence_penalty=0):
    # 确保model有效
    if not model or model == "auto":
        model = get_auto_model()
    else:
        model = get_model_by_autoupdate(model)
    if debug:
        print(f"校准后的model: {model}")
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
    return chat_completion(headers, payload)


def chat_completion(headers, payload):
    """处理用户请求并保留上下文"""
    try:
        url = f'{base_url}/v0/chat/completion/proxy'
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

# if __name__ == '__main__':
#     get_from_js_v3()
#     print("get_models: ",get_models())
#     print("cached_models:",cached_models)
#     print("base_url: ",base_url)
#     print("MODEL_STATS:",MODEL_STATS)
