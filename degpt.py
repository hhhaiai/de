"""
update time: 2025.06.30


curl 'https://www.degpt.ai/api/v1/auths/printSignIn' \
  -H 'accept: */*' \
  -H 'accept-language: en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7' \
  -H 'content-type: application/json' \
  -b '_ga=GA1.1.761121180.1732095521; _ga_ELT9ER83T2=GS2.1.s1751282755$o102$g1$t1751282770$j45$l0$h0' \
  -H 'dnt: 1' \
  -H 'origin: https://www.degpt.ai' \
  -H 'priority: u=1, i' \
  -H 'referer: https://www.degpt.ai/' \
  -H 'sec-ch-ua: "Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36' \
  --data-raw '{"id":"a831158117fd7a6fbb7da40cce1e27e9","channel":""}'

curl 'https://www.degpt.ai/api/v1/chat/completion/proxy' \
  -H 'accept: */*' \
  -H 'accept-language: en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7' \
  -H 'authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImE2ZmZhMjMxMGY3NzQ5MDBhZWM0OWZhOWQxZTllNzBjIiwiZXhwIjoxNzU2NDQ4MzczfQ.4ZJ3_rFGMlCUDiPF2ocyIzazkG4BJALUowOm_isp83E' \
  -H 'content-type: application/json' \
  -b '_ga=GA1.1.761121180.1732095521; _ga_ELT9ER83T2=GS2.1.s1755843574$o114$g0$t1755843574$j60$l0$h0' \
  -H 'dnt: 1' \
  -H 'origin: https://www.degpt.ai' \
  -H 'priority: u=1, i' \
  -H 'referer: https://www.degpt.ai/' \
  -H 'sec-ch-ua: "Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36' \
  --data-raw '{"model":"qwen3-235b-a22b","messages":[{"role":"user","content":"你说隔壁是什么房子"}],"enable_thinking":true,"project":"DecentralGPT","stream":true}'

"""
import json
import os
import re
import time
from datetime import datetime, timedelta
from typing import Set, Optional, List, Dict
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import aiohttp
import requests
# 禁用 SSL 警告
import urllib3
from urllib3.exceptions import InsecureRequestWarning


urllib3.disable_warnings(InsecureRequestWarning)
urllib3.disable_warnings()

debug = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

# 全局变量
last_request_time = 0  # 上次请求的时间戳
cache_duration = int(os.getenv("CACHE_DURATION", "3600"))  # 缓存有效期，单位：秒 (1小时)

# 会话存储配置
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "1800"))  # 会话超时时间30分钟
SESSION_STORAGE_TYPE = os.getenv("SESSION_STORAGE_TYPE", "memory")  # 存储类型: memory 或 redis


# 初始化会话存储
SESSION_STORAGE_TYPE = "memory"
SESSION_STORAGE = {}

if SESSION_STORAGE_TYPE == "memory":
    if debug:
        print("使用内存存储会话")
elif SESSION_STORAGE_TYPE == "redis":
    if debug:
        print("使用 Redis 存储会话")

'''用于存储缓存的模型数据'''
cached_models = {
    "object": "list",
    "data": [],
    "version": "1.2.3",
    "provider": "DeGPT",
    "name": "DeGPT",
    "default_locale": "en-US",
    "status": True,
    "time": 20250821
}


'''基础域名'''
base_url = os.getenv("DEGPT_BASE_URL", 'https://www.degpt.ai/api')

'''基础模型'''
base_model = os.getenv("DEGPT_BASE_MODEL", "gpt-4o-mini")

# 认证配置
auth_id = os.getenv("DEGPT_AUTH_ID", "b39fdee47a6bdbab5bc6827ac954c422")
auth_cookie = os.getenv("DEGPT_AUTH_COOKIE", "_ga=GA1.1.486456891.1750229584; _ga_ELT9ER83T2=GS2.1.s1750229583$o1$g1$t1750229594$j49$l0$h0")

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


def get_session(session_id: str) -> List[Dict]:
    """获取或创建会话上下文"""
    global SESSION_STORAGE
    
    # 清理过期会话
    cleanup_sessions()
    
    if SESSION_STORAGE_TYPE == "memory":
        if session_id not in SESSION_STORAGE:
            SESSION_STORAGE[session_id] = {
                "messages": [],
                "last_activity": datetime.now()
            }
        else:
            SESSION_STORAGE[session_id]["last_activity"] = datetime.now()
        
        return SESSION_STORAGE[session_id]["messages"]



def cleanup_sessions() -> None:
    """清理过期会话"""
    global SESSION_STORAGE
    now = datetime.now()
    
    if SESSION_STORAGE_TYPE == "memory":
        expired_sessions = []
        for session_id, session_data in SESSION_STORAGE.items():
            if (now - session_data["last_activity"]).total_seconds() > SESSION_TIMEOUT:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del SESSION_STORAGE[session_id]
            if debug:
                print(f"清理过期会话: {session_id}")
    
    elif SESSION_STORAGE_TYPE == "redis":
        # Redis 会自动过期，这里不需要手动清理
        pass


def clear_session(session_id: str) -> None:
    """清除特定会话"""
    global SESSION_STORAGE
    if SESSION_STORAGE_TYPE == "memory":
        if session_id in SESSION_STORAGE:
            del SESSION_STORAGE[session_id]
            if debug:
                print(f"清除会话: {session_id}")


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

    except Exception as e:
        if debug:
            print(f"系统检查失败: {e}")


def _fetch_and_update_models():
    """Thread-safe model fetching and cache updating"""
    global cached_models
    success = False
    
    try:
        get_from_js_v3()
        success = True
    except Exception as e:
        if debug:
            print(f"从JS获取模型数据失败: {e}")
    
    try:
        get_alive_models()
        success = True
    except Exception as e:
        if debug:
            print(f"从API获取模型数据失败: {e}")
    
    # 如果两个方法都失败了，抛出异常
    if not success:
        raise Exception("无法获取模型数据")


def get_models():
    """model data retrieval with thread safety"""
    global cached_models, last_request_time, base_model, MODEL_STATS
    current_time = time.time()
    if (current_time - last_request_time) > cache_duration:
        try:
            # Update timestamp before awaiting to prevent concurrent updates
            last_request_time = current_time
            _fetch_and_update_models()
        except Exception as e:
            if debug:
                print(f"获取模型数据时出错: {e}")
            # 如果获取模型数据失败，但缓存中有数据，继续使用缓存数据
            if not cached_models["data"]:
                raise e

     # 根据MODEL_STATS判断高成功率的模型并更新base_model
    if MODEL_STATS:
        best_model = None
        best_rate = -1.0

        for name, stats in MODEL_STATS.items():
            total_calls = stats["calls"]
            if total_calls > 0:
                success_rate = (total_calls - stats["fails"]) / total_calls
                if success_rate > best_rate:
                    best_rate = success_rate
                    best_model = name

        if best_model:
            base_model = best_model
            if debug:
                print(f"更新基础模型为: {base_model}")

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
            cached_models['version'] = data['version']
            cached_models['provider'] = data['provider']
            cached_models['name'] = data['provider']
            cached_models['time'] = timestamp_in_milliseconds

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
            model_id = model.get('textmodel', '').strip()
            if not model_id:
                model_id = model.get('model', '').strip()
            if model_id and model_id not in existing_ids:
                model_data = {
                    "id": model_id,
                    "object": "model",
                    "model": model_id,
                    "created": int(time.time()) * 1000,
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
        model: str = None,
        project="DecentralGPT", stream=True,
        temperature=0.3, max_tokens=1024, top_p=0.5,
        frequency_penalty=0, presence_penalty=0):
    """未来会增加回话隔离: 单人对话,单次会话"""
    messages = [
        # {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    return chat_completion_messages(messages, user_id=user_id, session_id=session_id,
                                    model=model, project=project, stream=stream, temperature=temperature,
                                    max_tokens=max_tokens, top_p=top_p, frequency_penalty=frequency_penalty,
                                    presence_penalty=presence_penalty)

def chat_completion_messages(
        messages,stream=True,
        model: str = None,
        user_id: str = None,
        session_id: str = None,
        project="DecentralGPT",
        temperature=0.3, max_tokens=1024, top_p=0.5,
        frequency_penalty=0, presence_penalty=0):
    # 输入验证
    if not messages or not isinstance(messages, list):
        raise ValueError("messages 参数必须是一个非空列表")
    
    # 验证每条消息的格式
    for i, message in enumerate(messages):
        if not isinstance(message, dict):
            raise ValueError(f"消息 {i} 必须是一个字典")
        if "role" not in message or "content" not in message:
            raise ValueError(f"消息 {i} 必须包含 'role' 和 'content' 字段")
        if message["role"] not in ["system", "user", "assistant"]:
            raise ValueError(f"消息 {i} 的 'role' 必须是 'system', 'user' 或 'assistant' 之一")
        if not isinstance(message["content"], str):
            raise ValueError(f"消息 {i} 的 'content' 必须是字符串")
    
    # 确保model有效
    if not model or model == "auto":
        model = get_auto_model()
    else:
        model = get_model_by_autoupdate(model)
    if debug:
        print(f"校准后的model: {model}")
    
    # 处理会话上下文
    if session_id:
        session_messages = get_session(session_id)
        # 合并历史消息和当前消息
        combined_messages = session_messages + messages
        if debug:
            print(f"会话 {session_id} 的历史消息: {len(session_messages)} 条")
            print(f"合并后的消息: {len(combined_messages)} 条")
    else:
        combined_messages = messages
    
    # 获取token
    url = f'{base_url}/v1/auths/printSignIn'

    headers = {
        "user-agent": os.getenv("DEGPT_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
    }

    data = {
        "id": auth_id,
        "channel": ""
    }
    res_page = requests.post(url=url, headers=headers, json=data, verify=False, timeout=5)
    res_page.encoding="utf-8"
    token = json.loads(res_page.text)["token"]
    if debug:
        print(f"res_page: {res_page}\r\nres_page.text: {res_page.text}\r\ntoken:{token}")

    headers_proxy = {
        "Host": os.getenv("DEGPT_PROXY_HOST", "www.degpt.ai"),
        "Connection": "keep-alive",
        "Content-Length": os.getenv("DEGPT_PROXY_CONTENT_LENGTH", "1673"),
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "sec-ch-ua-platform": os.getenv("DEGPT_PROXY_SEC_CH_UA_PLATFORM", "\"Windows\""),
        "Authorization": f"Bearer {token}",
        "User-Agent": os.getenv("DEGPT_PROXY_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"),
        "sec-ch-ua": os.getenv("DEGPT_PROXY_SEC_CH_UA", "\"Google Chrome\";v=\"137\", \"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\""),
        "Content-Type": "application/json",
        "sec-ch-ua-mobile": os.getenv("DEGPT_PROXY_SEC_CH_UA_MOBILE", "?0"),
        "Accept": "*/*",
        "Origin": os.getenv("DEGPT_PROXY_ORIGIN", "https://www.degpt.ai"),
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": os.getenv("DEGPT_PROXY_REFERER", "https://www.degpt.ai/c/e850c81f-19ab-4ac1-92ec-ee02c21095c7"),
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": os.getenv("DEGPT_PROXY_ACCEPT_LANGUAGE", "zh-CN,zh;q=0.9"),
        "Cookie": auth_cookie
    }
    # 后端服务只支持流式调用
    data_proxy = {
        "model": model,
        "messages": combined_messages,
        "stream": True,  # 始终使用流式调用后端
        "project": project,
        "enable_thinking": True
    }
    if debug:
        print(json.dumps(headers, indent=4))
        print(json.dumps(data_proxy, indent=4))
    return chat_completion(model=model, headers=headers_proxy, payload=data_proxy, stream=stream, session_id=session_id)


def parse_response(response_text):
    """
    逐行解析SSE流式响应并提取delta.content字段
    包含多层结构校验，确保安全访问嵌套字段
    返回标准API响应格式
    """
    lines = response_text.split('\n')
    result = ""
    created = None
    object_type = None
    
    for line in lines:
        if line.startswith("data:"):
            data_str = line[len("data:"):].strip()
            if not data_str or data_str == "[DONE]":
                continue
            try:
                data = json.loads(data_str)
                # 提取第一个data行的元信息
                if isinstance(data, dict) and not created:
                    created = data.get("created")
                    object_type = data.get("object")
                
                # 安全访问嵌套字段，确保是字典类型
                if isinstance(data, dict):
                    # 检查是否存在choices字段且为列表
                    if "choices" in data and isinstance(data["choices"], list):
                        for choice in data["choices"]:
                            # 检查每个choice是否为字典且包含delta字段
                            if isinstance(choice, dict) and "delta" in choice:
                                delta = choice["delta"]
                                # 确保delta是字典且包含content字段
                                if isinstance(delta, dict) and "content" in delta:
                                    content = delta["content"]
                                    # 确保content是字符串类型
                                    if isinstance(content, str):
                                        result += content
            except json.JSONDecodeError:
                continue
    import tiktoken

    # 计算token数量
    enc = tiktoken.get_encoding("cl100k_base")
    completion_tokens = len(enc.encode(result))
    
    # 组装标准响应数据
    response_data = {
        "id": f"chatcmpl-{datetime.now().timestamp()}",
        "object": object_type or "chat.completion",
        "created": created or int(datetime.now().timestamp()),
        "model": "gpt-4o",  # 可根据需求调整来源
        "usage": {
            "prompt_tokens": 0,  # 需要根据实际prompt内容计算
            "completion_tokens": completion_tokens,
            "total_tokens": completion_tokens
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
    
    return response_data

def chat_completion(model, headers, payload, stream=True, session_id=None):
    """处理用户请求并保留上下文"""
    try:
        url = f'{base_url}/v1/chat/completion/proxy'
        if debug:
            print(f"url: {url}")
        
        # 始终以流式方式调用后端
        response = requests.post(url=url, headers=headers, json=payload, verify=False, timeout=100, stream=True)
        response.encoding = 'utf-8'
        
        # 检查响应状态码
        if response.status_code != 200:
            record_call(model, False)
            error_msg = f"API 请求失败，状态码: {response.status_code}"
            if response.text:
                error_msg += f"，响应内容: {response.text}"
            raise requests.exceptions.RequestException(error_msg)
        
        response.raise_for_status()
        record_call(model, True)
            
        # 根据stream参数决定返回方式
        if stream:
            # 对于流式响应，直接返回response对象
            # 会话上下文的保存将在more_core.py中处理
            return response
        else:
            # 收集所有流数据并解析
            full_response = ""
            for chunk in response.iter_lines():
                if chunk:
                    decoded_chunk = chunk.decode('utf-8')
                    if decoded_chunk.startswith("data:"):
                        full_response += decoded_chunk + "\n"
            
            if debug:
                print("Full response collected")
            
            result = parse_response(full_response)
            
            # 保存助手响应到会话
            if session_id and isinstance(result, dict):
                save_assistant_response(session_id, result)
            
            return result
    except requests.exceptions.Timeout:
        record_call(model, False)
        raise requests.exceptions.RequestException("请求超时，请稍后重试")
    except requests.exceptions.ConnectionError:
        record_call(model, False)
        raise requests.exceptions.RequestException("网络连接错误，请检查网络设置")
    except requests.exceptions.RequestException as e:
        record_call(model, False)
        raise e
    except (KeyError, IndexError) as e:
        record_call(model, False)
        raise Exception(f"解析响应时出错: {e}")
    except Exception as e:
        record_call(model, False)
        raise Exception(f"未知错误: {e}")


def save_assistant_response(session_id: str, response_data: Dict) -> None:
    """保存助手响应到会话"""
    global SESSION_STORAGE
    
    if SESSION_STORAGE_TYPE == "memory":
        if session_id in SESSION_STORAGE:
            # 提取助手消息
            if "choices" in response_data and response_data["choices"]:
                choice = response_data["choices"][0]
                if "message" in choice:
                    assistant_message = choice["message"]
                    SESSION_STORAGE[session_id]["messages"].append(assistant_message)
                    if debug:
                        print(f"保存助手响应到会话 {session_id}")
    

class StreamingResponseWithSession:
    """包装流式响应以支持会话上下文保存"""
    
    def __init__(self, response, session_id, model):
        self.response = response
        self.session_id = session_id
        self.model = model
        self.accumulated_content = ""
    
    def __iter__(self):
        return self
    
    def __next__(self):
        # 这个方法不会被直接调用，但我们实现它以保持兼容性
        raise StopIteration
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        # 这个方法也不会被直接调用，但我们实现它以保持兼容性
        raise StopAsyncIteration
    
    def iter_lines(self):
        for chunk in self.response.iter_lines():
            if chunk:
                decoded_chunk = chunk.decode('utf-8')
                if decoded_chunk.startswith("data:"):
                    # 累积内容用于会话保存
                    data_str = decoded_chunk[len("data:"):].strip()
                    if data_str and data_str != "[DONE]":
                        try:
                            data = json.loads(data_str)
                            if isinstance(data, dict) and "choices" in data:
                                for choice in data["choices"]:
                                    if "delta" in choice and "content" in choice["delta"]:
                                        self.accumulated_content += choice["delta"]["content"]
                        except json.JSONDecodeError:
                            pass
                yield chunk
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        # 会话结束时保存助手响应
        if self.accumulated_content:
            assistant_message = {
                "role": "assistant",
                "content": self.accumulated_content
            }
            global SESSION_STORAGE
            if SESSION_STORAGE_TYPE == "memory":
                if self.session_id in SESSION_STORAGE:
                    SESSION_STORAGE[self.session_id]["messages"].append(assistant_message)
                    if debug:
                        print(f"流式响应保存到会话 {self.session_id}")
        self.response.close()


if __name__ == '__main__':
    # get_from_js_v3()
    # print("get_models: ", get_models())
    # print("cached_models:", cached_models)
    # print("base_url: ", base_url)
    # print("MODEL_STATS:", MODEL_STATS)
    # print("base_model:",base_model)
    # base_model = "QwQ-32B"

    models = [
        base_model,
        "deepseek-chat",
        "doubao-seed-1-6-250615",
        "qwen3-235b-a22b",
        "gpt-4o",
        "deepseek-reasoner",
        "gemini-2.5-flash-preview-05-20",
        "grok-3"
    ]

    for model in models:
        result = chat_completion_message(user_prompt="你是什么模型？", model=model, stream=True)
        print("="*60)
        print(f"模型 {model} 的响应：{result.text}")

