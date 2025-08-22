#!/usr/bin/env python3
"""
Claude协议转换测试脚本
用于验证more_core.py中的Claude协议转换功能
"""

import json
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from more_core import APIServer
from fastapi import FastAPI

def test_claude_to_openai_conversion():
    """测试Claude到OpenAI格式转换"""
    print("🧪 测试Claude到OpenAI格式转换...")
    
    app = FastAPI()
    server = APIServer(app)
    
    # 测试用例1: 基本Claude请求
    claude_request = {
        "model": "claude-3-sonnet-20240229",
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": "Hello, how are you?"}]
            }
        ],
        "max_tokens": 1024,
        "temperature": 0.7,
        "stream": False,
        "system": "You are a helpful assistant."
    }
    
    result = server._convert_claude_to_openai(claude_request, {})
    print("✅ 基本Claude请求转换成功")
    print(f"   转换结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 测试用例2: 包含session_id和user_id
    claude_request_with_ids = {
        "model": "claude-3-opus-20240229",
        "messages": [
            {
                "role": "user", 
                "content": [{"type": "text", "text": "What's the weather like?"}]
            }
        ],
        "session_id": "test_session_123",
        "user_id": "user_456",
        "max_tokens": 500
    }
    
    result2 = server._convert_claude_to_openai(claude_request_with_ids, {})
    print("✅ 包含session_id和user_id的Claude请求转换成功")
    assert result2.get("session_id") == "test_session_123"
    assert result2.get("user_id") == "user_456"
    
    # 测试用例3: 流式请求
    claude_stream_request = {
        "model": "claude-3-haiku-20240307",
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": "Stream test"}]
            }
        ],
        "stream": True,
        "temperature": 0.5,
        "top_p": 0.9
    }
    
    result3 = server._convert_claude_to_openai(claude_stream_request, {})
    print("✅ 流式Claude请求转换成功")
    assert result3.get("stream") == True
    
    print("🎉 所有Claude到OpenAI转换测试通过！")

def test_openai_to_claude_conversion():
    """测试OpenAI到Claude格式转换"""
    print("\n🧪 测试OpenAI到Claude格式转换...")
    
    app = FastAPI()
    server = APIServer(app)
    
    # 测试用例1: 基本OpenAI响应
    openai_response = {
        "id": "chatcmpl-123456",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello! I'm doing well, thank you for asking!"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 12,
            "total_tokens": 22
        }
    }
    
    result = server._convert_openai_to_claude(openai_response)
    print("✅ 基本OpenAI响应转换成功")
    print(f"   转换结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 验证必要字段存在
    assert "id" in result
    assert "type" in result
    assert "role" in result
    assert "content" in result
    assert "model" in result
    assert "stop_reason" in result
    assert "usage" in result
    
    # 测试用例2: 包含tool_calls的响应
    openai_with_tools = {
        "id": "chatcmpl-789012",
        "object": "chat.completion",
        "created": 1677652290,
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "I'll use a tool to get the weather",
                    "tool_calls": [
                        {
                            "id": "call_123",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"location": "San Francisco"}'
                            }
                        }
                    ]
                },
                "finish_reason": "tool_calls"
            }
        ],
        "usage": {
            "prompt_tokens": 15,
            "completion_tokens": 8,
            "total_tokens": 23
        }
    }
    
    result2 = server._convert_openai_to_claude(openai_with_tools)
    print("✅ 包含tool_calls的OpenAI响应转换成功")
    
    # 测试用例3: 错误响应
    error_response = "Internal server error"
    result3 = server._convert_openai_to_claude(error_response)
    print("✅ 错误响应转换成功")
    assert result3["type"] == "error"
    
    print("🎉 所有OpenAI到Claude转换测试通过！")

def test_message_conversion():
    """测试消息格式转换"""
    print("\n🧪 测试消息格式转换...")
    
    app = FastAPI()
    server = APIServer(app)
    
    # 测试Claude消息格式转换
    claude_messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": "Hello world"}]
        },
        {
            "role": "assistant", 
            "content": [{"type": "text", "text": "Hi there!"}]
        }
    ]
    
    result = server._convert_claude_messages(claude_messages)
    print("✅ Claude消息格式转换成功")
    print(f"   转换结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 验证转换结果
    assert len(result) == 2
    assert result[0]["role"] == "user"
    assert result[0]["content"] == "Hello world"
    assert result[1]["role"] == "assistant"
    assert result[1]["content"] == "Hi there!"
    
    print("🎉 消息格式转换测试通过！")

if __name__ == "__main__":
    print("🚀 开始Claude协议转换测试...\n")
    
    try:
        test_claude_to_openai_conversion()
        test_openai_to_claude_conversion() 
        test_message_conversion()
        
        print("\n🎊 所有Claude协议转换测试通过！")
        print("✅ Claude协议转换功能完整且正确")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)