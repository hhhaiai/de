#!/usr/bin/env python3
"""
测试认证功能
"""

import requests
import json
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# 禁用SSL警告
urllib3.disable_warnings(InsecureRequestWarning)

def test_auth():
    """测试认证接口"""
    print("=== 测试认证接口 ===")
    
    url = 'https://www.degpt.ai/api/v1/auths/printSignIn'
    
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    }
    
    data = {
        "id": "b39fdee47a6bdbab5bc6827ac954c422",
        "channel": ""
    }
    
    try:
        response = requests.post(url=url, headers=headers, json=data, verify=False, timeout=10)
        response.encoding = "utf-8"
        
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            try:
                result = json.loads(response.text)
                if "token" in result:
                    print(f"✅ 认证成功，获取到token: {result['token'][:20]}...")
                    return True
                else:
                    print("❌ 响应中没有token字段")
                    return False
            except json.JSONDecodeError:
                print("❌ 响应不是有效的JSON")
                return False
        else:
            print("❌ 认证请求失败")
            return False
            
    except Exception as e:
        print(f"❌ 认证请求异常: {e}")
        return False

def test_chat_completion():
    """测试聊天完成接口"""
    print("\n=== 测试聊天完成接口 ===")
    
    # 先获取token
    auth_url = 'https://www.degpt.ai/api/v1/auths/printSignIn'
    auth_headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    }
    auth_data = {
        "id": "b39fdee47a6bdbab5bc6827ac954c422",
        "channel": ""
    }
    
    try:
        auth_response = requests.post(auth_url, headers=auth_headers, json=auth_data, verify=False, timeout=10)
        auth_response.encoding = "utf-8"
        
        if auth_response.status_code != 200:
            print("❌ 认证失败")
            return
            
        token = json.loads(auth_response.text)["token"]
        print(f"获取到token: {token[:20]}...")
        
        # 测试聊天接口
        chat_url = 'https://www.degpt.ai/api/v1/chat/completion/proxy'
        chat_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        }
        
        chat_data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "你好"}],
            "stream": False,
            "project": "DecentralGPT",
            "enable_thinking": False
        }
        
        chat_response = requests.post(chat_url, headers=chat_headers, json=chat_data, verify=False, timeout=30)
        print(f"聊天接口状态码: {chat_response.status_code}")
        print(f"聊天接口响应: {chat_response.text}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    print("开始测试认证功能...")
    
    # 测试认证
    auth_success = test_auth()
    
    if auth_success:
        # 测试完整流程
        test_chat_completion()
    else:
        print("认证失败，无法继续测试聊天接口")