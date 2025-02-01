"""
update time: 2025.01.09
version: 0.1.126
"""
import json
import re
import time
from datetime import datetime
import aiohttp
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Set, Optional, List, Dict, Any

import asyncio
from aiohttp import ClientSession, ClientTimeout

# 禁用 SSL 警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import multiprocessing
from multiprocessing.managers import DictProxy
from multiprocessing import Value


class DeGPTClient:
    def __init__(
        self,
        debug: bool = False,
        MODEL_STATS: Optional[DictProxy] = None,
        cached_models: Optional[DictProxy] = None,
        models_found: Optional[Value] = None,
        lock: Optional[multiprocessing.Lock] = None
    ):
        self.debug = debug
        # 全局变量
        self.last_request_time = 0  # 上次请求的时间戳
        self.cache_duration = 14400  # 缓存有效期，单位：秒 (4小时)
        '''用于存储缓存的模型数据'''
        self.cached_models_initial = {
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
        self.base_addrs = [
            # "America"
            "https://usa-chat.degpt.ai/api",
            # "Singapore"
            "https://singapore-chat.degpt.ai/api",
            # "Korea"
            "https://korea-chat.degpt.ai/api"
        ]
        '''基础域名'''
        self.base_url_initial = 'https://singapore-chat.degpt.ai/api'

        '''基础模型'''
        self.base_model = "Pixtral-124B"
        # 全局变量：存储所有模型的统计信息
        # 格式：{model_name: {"calls": 调用次数, "fails": 失败次数, "last_fail": 最后失败时间}}
        self.MODEL_STATS_initial: Dict[str, Dict] = {}

        # 使用传入的共享资源或自行创建
        if MODEL_STATS is not None and cached_models is not None and models_found is not None and lock is not None:
            self.MODEL_STATS = MODEL_STATS
            self.cached_models = cached_models
            self.models_found = models_found
            self.lock = lock
        else:
            # 初始化多进程共享管理器（仅在未提供共享资源时）
            manager = multiprocessing.Manager()
            self.MODEL_STATS = manager.dict(self.MODEL_STATS_initial)
            self.cached_models = manager.dict(self.cached_models_initial)
            self.lock = manager.Lock()
            self.models_found = manager.Value('b', False)  # 共享布尔标志

        # 设置初始 base_url
        self.base_url = self.base_url_initial

    def record_call(self, model_name: str, success: bool = True) -> None:
        """
        记录模型调用情况
        Args:
            model_name: 模型名称
            success: 调用是否成功
        """
        with self.lock:  # 使用锁保护共享资源
            if model_name not in self.MODEL_STATS:
                self.MODEL_STATS[model_name] = {"calls": 0, "fails": 0, "last_fail": None}

            stats = self.MODEL_STATS[model_name]
            stats["calls"] += 1
            if not success:
                stats["fails"] += 1
                stats["last_fail"] = datetime.now().timestamp()
            self.MODEL_STATS[model_name] = stats  # 更新共享字典

    def get_auto_model(self, cooldown_seconds: int = 300) -> str:
        """获取最优模型"""
        try:
            if not self.MODEL_STATS:
                self.get_models()

            best_model = None
            best_rate = -1.0
            now = datetime.now().timestamp()

            with self.lock:
                for name, stats in self.MODEL_STATS.items():
                    if stats.get("last_fail") and (now - stats["last_fail"]) < cooldown_seconds:
                        continue

                    total_calls = stats["calls"]
                    if total_calls > 0:
                        success_rate = (total_calls - stats["fails"]) / total_calls
                        if success_rate > best_rate:
                            best_rate = success_rate
                            best_model = name

            default_model = best_model or self.base_model
            if self.debug:
                print(f"选择模型: {default_model}")
            return default_model
        except Exception as e:
            if self.debug:
                print(f"模型选择错误: {e}")
            return self.base_model

    def reload_check(self):
        """检查并更新系统状态
        1. 如果模型数据为空，更新模型数据
        2. 测试当前base_url是否可用，不可用则切换
        """
        try:
            # 检查模型数据
            if not self.cached_models.get("data"):
                if self.debug:
                    print("模型数据为空，开始更新...")
                self.get_models()

            # 测试用例 - 平衡效率和功能验证
            test_payload = {
                "model": self.base_model,
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

            async def test_url(session, url):
                try:
                    async with session.post(
                        f"{url}/v0/chat/completion/proxy",
                        headers=headers,
                        json=test_payload,
                        timeout=5  # 较短的超时时间提高效率
                    ) as response:
                        if response.status == 200:
                            content = await response.read()
                            if content:
                                return True
                except Exception as e:
                    if self.debug:
                        print(f"测试URL {url} 失败: {e}")
                return False

            async def run_checks():
                async with aiohttp.ClientSession() as session:
                    # 测试当前URL
                    if await test_url(session, self.base_url):
                        if self.debug:
                            print(f"当前URL可用: {self.base_url}")
                        return

                    # 测试其他URL
                    for url in self.base_addrs:
                        if url == self.base_url:
                            continue
                        if await test_url(session, url):
                            self.base_url = url
                            if self.debug:
                                print(f"切换到新URL: {self.base_url}")
                            return

                    if self.debug:
                        print("所有URL不可用，保持当前URL")

            asyncio.run(run_checks())

        except Exception as e:
            if self.debug:
                print(f"系统检查失败: {e}")

    def _fetch_and_update_models(self):
        """线程安全的模型获取和缓存更新"""
        try:
            self.get_from_js_v3()
        except Exception as e:
            print(f"获取模型时出错: {e}")
        try:
            self.get_alive_models()
        except Exception as e:
            print(f"获取活跃模型时出错: {e}")

    def get_models(self):
        """获取模型数据，具有线程安全性"""
        current_time = time.time()
        with self.lock:
            if (current_time - self.last_request_time) > self.cache_duration:
                try:
                    # 更新请求时间戳
                    self.last_request_time = current_time
                    self._fetch_and_update_models()
                except Exception as e:
                    print(f"获取模型时出错: {e}")

            # 将 DictProxy 转换为普通字典再序列化
            return json.dumps(dict(self.cached_models))

    def get_alive_models(self):
        """
        获取活跃的模型版本，并更新全局缓存
        """
        try:
            # 发送 GET 请求
            url = 'https://www.degpt.ai/api/config'
            headers = {'Content-Type': 'application/json'}

            response = requests.get(url, headers=headers, timeout=10)

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
                    self.cached_models['version'] = data.get('version', 'unknown')
                    self.cached_models['provider'] = data.get('provider', 'unknown')
                    self.cached_models['name'] = data.get('provider', 'unknown')
                    self.cached_models['time'] = timestamp_in_milliseconds

                    if default_models:
                        existing_ids = {m.get('id') for m in self.cached_models["data"]}
                        for model_id in default_models:
                            if model_id:  # 确保 model_id 不为空
                                self.record_call(model_id)
                                if model_id not in existing_ids:
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
                                    self.cached_models["data"].append(model_data)
                    # 更新全局缓存
                    self.last_request_time = timestamp_in_seconds  # 更新缓存时间戳

                except json.JSONDecodeError as e:
                    print("JSON 解码错误:", e)
            else:
                print(f"请求失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"获取活跃模型时出错: {e}")

    def get_from_js_v3(self):
        models = self.analyze()
        if models:
            # 获取已经存在的ID
            existing_ids = {m.get('id') for m in self.cached_models["data"]}
            for model in models:
                model_id = model.get('model', '').strip()
                if model_id and model_id not in existing_ids:
                    timestamp_ms = int(time.time()) * 1000
                    model_data = {
                        "id": model_id,
                        "object": "model",
                        "model": model_id,
                        "created": timestamp_ms,
                        "owned_by": model_id.split("-")[0] if "-" in model_id else "unknown",
                        "name": model.get('name', ''),
                        "description": model.get('desc', ''),
                        "support": model.get('support', 'text'),
                        "tip": model.get('tip', '')
                    }
                    self.cached_models["data"].append(model_data)
                    self.record_call(model_id)
                    if self.debug:
                        print(f"添加新模型: {model_id}")
            # 设置模型已找到标志
            with self.lock:
                self.models_found.value = True
            if self.debug:
                print("模型已找到，停止进一步的遍历。")
        pass

    def fetch_content(self, url: str) -> Optional[str]:
        """获取页面内容"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            if self.debug:
                print(f"获取页面失败 {url}: {e}")
            return None

    def parse_models_from_js(self, content: str, url: str) -> List[Dict]:
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
                    return models
            except json.JSONDecodeError:
                # 尝试修复JSON
                fixed_data = self._fix_json_errors(models_data)
                try:
                    return json.loads(fixed_data)
                except json.JSONDecodeError as e:
                    if self.debug:
                        print(f"JSON解析失败 {url}: {e}")

            return []
        except Exception as e:
            if self.debug:
                print(f"解析模型失败 {url}: {e}")
            return []

    def _fix_json_errors(self, json_str: str) -> str:
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

    def extract_links(self, content: str, url: str) -> Set[str]:
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
                            if self.debug:
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
            if url.endswith('.js') and not self.models_found.value:
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
            if self.debug:
                print(f"提取链接失败 {url}: {e}")

        return links

    def analyze(self, _bb_url="https://www.degpt.ai/") -> List[Dict]:
        """分析网站内容"""
        visited_urls = set()
        found_models = []

        def _analyze(url: str) -> bool:
            if self.models_found.value:
                return False  # 已经找到模型，停止进一步遍历

            if url in visited_urls:
                return False

            visited_urls.add(url)
            if self.debug:
                print(f"正在分析: {url}")

            content = self.fetch_content(url)
            if not content:
                return False

            models = self.parse_models_from_js(content, url)
            if models:
                with self.lock:
                    found_models.extend(models)
                self.models_found.value = True  # 设置模型已找到标志
                if self.debug:
                    print("模型已找到，停止进一步的遍历。")
                return True

            for link in self.extract_links(content, url):
                if self.models_found.value:
                    return True  # 已经找到模型，停止进一步的遍历
                if _analyze(link):
                    return True

            return False

        _analyze(_bb_url)
        return found_models

    def is_model_available(self, model_id: str, cooldown_seconds: int = 300) -> bool:
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
        # 如果MODEL_STATS为空，加载模型数据
        with self.lock:
            if not self.MODEL_STATS:
                self.get_models()

            # 检查模型是否在统计信息中
            if model_id not in self.MODEL_STATS:
                return False

            # 检查是否在冷却期内
            stats = self.MODEL_STATS[model_id]
            if stats.get("last_fail"):
                time_since_failure = datetime.now().timestamp() - stats["last_fail"]
                if time_since_failure < cooldown_seconds:
                    return False

            return True

    def get_model_by_autoupdate(self, model_id: Optional[str] = None, cooldown_seconds: int = 300) -> Optional[str]:
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
        # 如果MODEL_STATS为空，加载模型数据
        with self.lock:
            if not self.MODEL_STATS:
                self.get_models()

        # 如果提供了model_id且可用，直接返回
        if model_id and self.is_model_available(model_id, cooldown_seconds):
            return model_id

        # 否则返回成功率最高的可用模型
        return self.get_auto_model(cooldown_seconds=cooldown_seconds)

    def is_chatgpt_format(self, data):
        """检查数据是否符合预期的ChatGPT格式"""
        try:
            # 如果数据是字符串，尝试解析为JSON
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    return False  # 如果字符串无法解析，则不符合预期格式

            # 现在检查数据是否是字典并包含必要的结构
            if isinstance(data, dict):
                # 确保 'choices' 是一个列表，且第一个项目具有 'message' 字段
                if "choices" in data and isinstance(data["choices"], list) and len(data["choices"]) > 0:
                    if "message" in data["choices"][0]:
                        return True
        except Exception as e:
            if self.debug:
                print(f"检查ChatGPT格式时出错: {e}")

        return False

    def chat_completion_message(
            self,
            user_prompt,
            user_id: str = None,
            session_id: str = None,
            system_prompt="You are a helpful assistant.",
            model=None,
            project="DecentralGPT", stream=False,
            temperature=0.3, max_tokens=1024, top_p=0.5,
            frequency_penalty=0, presence_penalty=0):
        """处理单个用户提示的聊天补全"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self.chat_completion_messages(messages, user_id, session_id, model, project, stream, temperature, max_tokens,
                                           top_p, frequency_penalty,
                                           presence_penalty)

    def chat_completion_messages(
            self,
            messages,
            model=None,
            user_id: str = None,
            session_id: str = None,
            project="DecentralGPT", stream=False, temperature=0.3, max_tokens=1024, top_p=0.5,
            frequency_penalty=0, presence_penalty=0):
        # 确保model有效
        if not model or model == "auto":
            model = self.get_auto_model()
        else:
            model = self.get_model_by_autoupdate(model)
        if self.debug:
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
            # 确保数据格式正确
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
        return self.chat_completion(model, headers, payload)

    def chat_completion(self, model, headers, payload):
        """处理用户请求并保留上下文"""
        try:
            url = f'{self.base_url}/v0/chat/completion/proxy'
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.encoding = 'utf-8'
            if response.status_code != 200:
                self.record_call(model, False)
            else:
                self.record_call(model, True)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.record_call(model, False)
            if self.debug:
                print(f"请求失败: {e}")
            return "请求失败，请检查网络或参数配置。"
        except (KeyError, IndexError) as e:
            self.record_call(model, False)
            if self.debug:
                print(f"解析响应时出错: {e}")
            return "解析响应内容失败。"
        except Exception as e:
            self.record_call(model, False)
            if self.debug:
                print(f"未知错误: {e}")
            return "发生未知错误。"

    def get_model_stats(self):
        """获取模型统计信息"""
        with self.lock:
            return dict(self.MODEL_STATS)

    def get_cached_models(self):
        """获取缓存的模型信息"""
        with self.lock:
            return dict(self.cached_models)

    # 这里可以添加更多的方法或功能，根据需求扩展


def worker_process(shared_MODEL_STATS: DictProxy, shared_cached_models: DictProxy, shared_models_found: Value, lock: multiprocessing.Lock, debug: bool, user_prompt: str, model: str, result_queue: multiprocessing.Queue):
    """
    子进程工作函数

    Args:
        shared_MODEL_STATS: multiprocessing.Manager().dict, 共享的模型统计信息
        shared_cached_models: multiprocessing.Manager().dict, 共享的缓存模型信息
        shared_models_found: multiprocessing.Manager().Value, 共享的模型找到标志
        lock: multiprocessing.Lock, 共享的锁
        debug: bool, 是否开启调试
        user_prompt: str, 用户提示
        model: str, 模型名称
        result_queue: multiprocessing.Queue, 用于返回结果
    """
    try:
        # 创建客户端实例，并加载共享数据
        client = DeGPTClient(
            debug=debug,
            MODEL_STATS=shared_MODEL_STATS,
            cached_models=shared_cached_models,
            models_found=shared_models_found,
            lock=lock
        )

        # 执行请求
        result = client.chat_completion_message(user_prompt=user_prompt, model=model)
        result_queue.put((multiprocessing.current_process().name, result))
    except Exception as e:
        result_queue.put((multiprocessing.current_process().name, f"错误: {e}"))


if __name__ == '__main__':
    # 初始化多进程管理器
    manager = multiprocessing.Manager()
    shared_MODEL_STATS = manager.dict()
    shared_cached_models = manager.dict({
        "object": "list",
        "data": [],
        "version": "0.1.125",
        "provider": "DeGPT",
        "name": "DeGPT",
        "default_locale": "en-US",
        "status": True,
        "time": 0
    })
    shared_models_found = manager.Value('b', False)
    lock = manager.Lock()

    # 初始化客户端
    client = DeGPTClient(
        debug=True,
        MODEL_STATS=shared_MODEL_STATS,
        cached_models=shared_cached_models,
        models_found=shared_models_found,
        lock=lock
    )

    # 获取模型数据
    client.get_from_js_v3()
    try:
        models_json = client.get_models()
        print("get_models: ", models_json)
    except TypeError as e:
        print(f"序列化 cached_models 时出错: {e}")
    print("cached_models:", client.get_cached_models())
    print("base_url: ", client.base_url)
    print("MODEL_STATS:", client.get_model_stats())

    # 准备多进程工作
    processes = []
    result_queue = multiprocessing.Queue()

    # 共享数据已经通过共享变量传递，不需要额外包装
    for i in range(5):  # 例如，启动5个进程
        user_prompt = f"测试输入 {i}"
        p = multiprocessing.Process(
            target=worker_process,
            args=(
                shared_MODEL_STATS,
                shared_cached_models,
                shared_models_found,
                lock,
                client.debug,
                user_prompt,
                "Pixtral-124B",
                result_queue
            ),
            name=f"Worker-{i}"
        )
        p.start()
        processes.append(p)

    # 等待所有进程完成
    for p in processes:
        p.join()

    # 收集结果
    while not result_queue.empty():
        process_name, result = result_queue.get()
        print(f"进程 {process_name} 的结果: {result}")

    # 单次对话
    result1 = client.chat_completion_message(
        user_prompt="你好，请介绍下你自己",
        model="Pixtral-124B",
        temperature=0.3
    )
    print(f"单次对话结果: {result1}")

    # 多轮对话
    messages = [
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "你好"}
    ]
    result2 = client.chat_completion_messages(messages)
    print(f"多轮对话结果: {result2}")
