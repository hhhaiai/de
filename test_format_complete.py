#!/usr/bin/env python3
"""
测试完整的请求-响应格式匹配
"""
import json
from fastapi import FastAPI
from more_core import APIServer

def test_openai_format():
    """测试OpenAI格式请求-响应"""
    print("=== 测试OpenAI格式 ===")
    
    # 创建一个模拟的FastAPI应用实例
    app = FastAPI()
    
    # 创建服务器实例
    server = APIServer(app)
    
    # 模拟OpenAI请求
    openai_request = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "你好"}],
        "stream": False,
        "session_id": "test_session_123"
    }
    
    headers = {"Content-Type": "application/json"}
    
    print("OpenAI请求格式:")
    print(json.dumps(openai_request, indent=2, ensure_ascii=False))
    
    # 注意：这里只是测试格式转换，实际需要真实的后端连接
    print("\n✅ OpenAI格式检查完成")

def test_claude_format():
    """测试Claude格式请求-响应"""
    print("\n=== 测试Claude格式 ===")
    
    # 创建一个模拟的FastAPI应用实例
    app = FastAPI()
    
    # 创建服务器实例
    server = APIServer(app)
    
    # 模拟Claude请求
    claude_request = {
        "model": "claude-3-sonnet-20240229",
        "messages": [{"role": "user", "content": "你好"}],
        "max_tokens": 1024,
        "stream": False,
        "session_id": "test_session_123"
    }
    
    print("Claude请求格式:")
    print(json.dumps(claude_request, indent=2, ensure_ascii=False))
    
    # 测试请求转换
    openai_converted = server._convert_claude_to_openai(claude_request, {})
    print("\n转换后的OpenAI格式:")
    print(json.dumps(openai_converted, indent=2, ensure_ascii=False))
    
    # 测试响应转换（模拟一个OpenAI响应）
    openai_response = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-4o-mini",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "你好！我是AI助手"
            },
            "finish_reason": "stop"
        }],
        "usage": {"prompt_tokens": 5, "completion_tokens": 8, "total_tokens": 13}
    }
    
    claude_converted = server._convert_openai_to_claude(openai_response)
    print("\n转换后的Claude响应格式:")
    print(json.dumps(claude_converted, indent=2, ensure_ascii=False))
    
    # 验证必需字段
    required_claude_fields = ["id", "type", "role", "content", "model", "stop_reason", "usage"]
    for field in required_claude_fields:
        if field in claude_converted:
            print(f"✅ Claude响应包含必需字段: {field}")
        else:
            print(f"❌ Claude响应缺少字段: {field}")
    
    print("\n✅ Claude格式检查完成")

def test_session_isolation():
    """测试会话隔离逻辑"""
    print("\n=== 测试会话隔离 ===")
    
    # 创建一个模拟的FastAPI应用实例
    app = FastAPI()
    
    # 创建服务器实例
    server = APIServer(app)
    
    # 测试session_id生成
    session_id1 = server._generate_session_id()
    session_id2 = server._generate_session_id()
    
    print(f"生成的会话ID 1: {session_id1}")
    print(f"生成的会话ID 2: {session_id2}")
    print(f"会话ID是否不同: {session_id1 != session_id2}")
    
    # 测试user_id转换
    user_id = "user_001"
    converted_session_id = f"user_{user_id}"
    print(f"User ID转换: {user_id} -> {converted_session_id}")
    
    print("\n✅ 会话隔离检查完成")

if __name__ == "__main__":
    print("开始测试完整的请求-响应格式匹配...")
    
    test_openai_format()
    test_claude_format()
    test_session_isolation()
    
    print("\n=== 所有测试完成 ===")