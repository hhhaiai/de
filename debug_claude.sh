#!/bin/bash

API_URL="http://localhost:7860"
ANTHROPIC_API_KEY="test_anthropic_key"
MODEL="deepseek-chat"

echo "🔍 调试Claude流式响应问题"
echo "==============================================="

echo "1. 测试健康检查"
curl -s $API_URL/health
echo -e "\n"

echo "2. 测试Claude非流式响应"
curl -s -X POST $API_URL/v1/messages \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: '$ANTHROPIC_API_KEY \
  -H 'anthropic-version: 2023-06-01' \
  -d '{
    "model": "'$MODEL'",
    "max_tokens": 1000,
    "messages": [
      {
        "role": "user",
        "content": "请说你好并简单介绍你自己"
      }
    ]
  }' | jq .
echo -e "\n"

echo "3. 测试Claude流式响应（完整输出）"
curl -s -X POST $API_URL/v1/messages \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: '$ANTHROPIC_API_KEY \
  -H 'anthropic-version: 2023-06-01' \
  -d '{
    "model": "claude-opus-4-20250514",
    "max_tokens": 1000,
    "stream": true,
    "messages": [
      {
        "role": "user",
        "content": "请说你好并简单介绍你自己"
      }
    ]
  }'
echo -e "\n"

echo "4. 测试Claude流式响应（只显示content）"
curl -s -X POST $API_URL/v1/messages \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: '$ANTHROPIC_API_KEY \
  -H 'anthropic-version: 2023-06-01' \
  -d '{
    "model": "claude-opus-4-20250514",
    "max_tokens": 1000,
    "stream": true,
    "messages": [
      {
        "role": "user",
        "content": "请说你好并简单介绍你自己"
      }
    ]
  }' | grep -E 'data:.*content.*text'
echo -e "\n"

echo "5. 测试不同的Claude模型"
curl -s -X POST $API_URL/v1/messages \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: '$ANTHROPIC_API_KEY \
  -H 'anthropic-version: 2023-06-01' \
  -d '{
    "model": "claude-opus-4-20250514",
    "max_tokens": 1000,
    "stream": true,
    "messages": [
      {
        "role": "user",
        "content": "请说你好"
      }
    ]
  }' | head -20
echo -e "\n"

echo "6. 测试OpenAI流式作为对比"
curl -s -X POST $API_URL/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer test_openai_key' \
  -d '{
    "model": "'$MODEL'",
    "messages": [{"role": "user", "content": "请说你好"}],
    "stream": true
  }' | head -10
echo -e "\n"

echo "调试完成"