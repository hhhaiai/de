#!/usr/bin/env python3
"""
测试上下文功能
"""

import json
import requests
import time

# 测试服务器地址
BASE_URL = "http://localhost:7860"

def test_single_conversation():
    """测试单次对话（无session_id）"""
    print("=== 测试单次对话（无session_id） ===")
    
    # 第一次请求
    payload1 = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "你好，我是小明"}],
        "stream": False
    }
    
    response1 = requests.post(f"{BASE_URL}/api/v1/chat/completions", json=payload1)
    print(f"第一次响应: {response1.status_code}")
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"第一次回复: {result1['choices'][0]['message']['content'][:50]}...")
    
    # 第二次请求（应该没有上下文）
    payload2 = {
        "model": "gpt-4o-mini", 
        "messages": [{"role": "user", "content": "我刚才说了什么？"}],
        "stream": False
    }
    
    response2 = requests.post(f"{BASE_URL}/api/v1/chat/completions", json=payload2)
    print(f"第二次响应: {response2.status_code}")
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"第二次回复: {result2['choices'][0]['message']['content'][:50]}...")

def test_session_context():
    """测试会话上下文"""
    print("\n=== 测试会话上下文 ===")
    
    session_id = "test_session_123"
    
    # 第一次请求
    payload1 = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "你好，我是小明"}],
        "session_id": session_id,
        "stream": False
    }
    
    response1 = requests.post(f"{BASE_URL}/api/v1/chat/completions", json=payload1)
    print(f"第一次响应: {response1.status_code}")
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"第一次回复: {result1['choices'][0]['message']['content'][:50]}...")
    
    # 第二次请求（应该有上下文）
    payload2 = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "我刚才说了什么？"}],
        "session_id": session_id,
        "stream": False
    }
    
    response2 = requests.post(f"{BASE_URL}/api/v1/chat/completions", json=payload2)
    print(f"第二次响应: {response2.status_code}")
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"第二次回复: {result2['choices'][0]['message']['content'][:50]}...")

def test_user_isolation():
    """测试用户隔离"""
    print("\n=== 测试用户隔离 ===")
    
    user_id1 = "user_001"
    user_id2 = "user_002"
    
    # 用户1第一次请求
    payload1 = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "我是用户1"}],
        "user_id": user_id1,
        "stream": False
    }
    
    response1 = requests.post(f"{BASE_URL}/api/v1/chat/completions", json=payload1)
    print(f"用户1第一次响应: {response1.status_code}")
    
    # 用户2第一次请求
    payload2 = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "我是用户2"}],
        "user_id": user_id2,
        "stream": False
    }
    
    response2 = requests.post(f"{BASE_URL}/api/v1/chat/completions", json=payload2)
    print(f"用户2第一次响应: {response2.status_code}")
    
    # 用户1第二次请求（应该只有用户1的上下文）
    payload3 = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "我刚才说了什么？"}],
        "user_id": user_id1,
        "stream": False
    }
    
    response3 = requests.post(f"{BASE_URL}/api/v1/chat/completions", json=payload3)
    print(f"用户1第二次响应: {response3.status_code}")
    if response3.status_code == 200:
        result3 = response3.json()
        print(f"用户1第二次回复: {result3['choices'][0]['message']['content'][:50]}...")

if __name__ == "__main__":
    print("开始测试上下文功能...")
    
    try:
        test_single_conversation()
        time.sleep(1)
        test_session_context()
        time.sleep(1)
        test_user_isolation()
        
        print("\n=== 测试完成 ===")
    except Exception as e:
        print(f"测试出错: {e}")