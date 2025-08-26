#!/bin/bash

# API配置
API_URL="http://localhost:7860"
OPENAI_API_KEY="YOUR_API_KEY"
ANTHROPIC_API_KEY="ANTHROPIC_API_KEY"

IMAGE_URL="https://img0.baidu.com/it/u=337102486,1971914968&fm=253&app=138&f=JPEG?w=800&h=1062"
# 测试图片数据（示例图片）data:image/png;base64,。。。
IMAGE_DATA="iV"

# 测试函数
run_test() {
    echo "==============================================="
    echo "测试 $1"
    echo "==============================================="
    eval "$2"
    echo -e "\n\n"
}

# 1. 测试获取模型
run_test "获取模型列表" \
    "curl -s $API_URL/api/v1/models -H 'Authorization: Bearer $OPENAI_API_KEY' | jq ."

# 2. 测试OpenAI文字非流式对话
run_test "OpenAI文字非流式对话" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [{\"role\": \"user\", \"content\": \"你是什么模型?\"}],
        \"stream\": false
      }' | jq ."

# 3. 测试Claude对话
run_test "Claude对话" \
    "curl -s -X POST $API_URL/api/v1/messages \
      -H 'Content-Type: application/json' \
      -H 'x-api-key: $ANTHROPIC_API_KEY' \
      -H 'anthropic-version: 2023-06-01' \
      -d '{
        \"model\": \"claude-opus-4-20250514\",
        \"max_tokens\": 1000,
        \"messages\": [
          {
            \"role\": \"user\",
            \"content\": \"你是什么模型?\"
          }
        ]
      }' | jq ."

# 4. 测试OpenAI多模态文字非流式
run_test "OpenAI多模态文字非流式" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"deepseek-chat\",
        \"messages\": [{\"role\": \"user\", \"content\": [{\"type\":\"text\",\"text\":\"你是什么模型？\"}]}],
        \"stream\": false
      }' | jq ."

# # 5. 测试OpenAI多模态文字+图片非流式
# run_test "OpenAI多模态文字+图片非流式" \
#     "curl -s -X POST $API_URL/api/v1/chat/completions \
#       -H 'Content-Type: application/json' \
#       -H 'Authorization: Bearer $OPENAI_API_KEY' \
#       -d '{
#         \"model\": \"deepseek-chat\",
#         \"messages\": [{\"role\": \"user\", \"content\": [
#           {\"type\":\"text\",\"text\":\"图片是啥\"},
#           {\"type\":\"image_url\",\"image_url\":{\"url\":\"$IMAGE_DATA\"}}
#         ]}],
#         \"stream\": false
#       }' | jq ."

# 6. 测试OpenAI文字流式对话
run_test "OpenAI文字流式对话" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [{\"role\": \"user\", \"content\": \"你是什么模型?\"}],
        \"stream\": true
      }'"

# 7. 测试OpenAI多模态文字流式
run_test "OpenAI多模态文字流式" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"deepseek-chat\",
        \"messages\": [{\"role\": \"user\", \"content\": [{\"type\":\"text\",\"text\":\"你是什么模型？\"}]}],
        \"stream\": true
      }'"


# # 8. 测试OpenAI多模态文字+图片流式
# run_test "OpenAI多模态文字+图片流式" \
#     "curl -s -X POST $API_URL/api/v1/chat/completions \
#       -H 'Content-Type: application/json' \
#       -H 'Authorization: Bearer $OPENAI_API_KEY' \
#       -d '{
#         \"model\": \"deepseek-chat\",
#         \"messages\": [{\"role\": \"user\", \"content\": [
#           {\"type\":\"text\",\"text\":\"图片是啥\"},
#           {\"type\":\"image_url\",\"image_url\":{\"url\":\"$IMAGE_DATA\"}}
#         ]}],
#         \"stream\": true
#       }'"
    

# 9. 测试OpenAI多模态文字+图片非流式
run_test "OpenAI多模态文字+网络图片非流式" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"deepseek-chat\",
        \"messages\": [{\"role\": \"user\", \"content\": [
          {\"type\":\"text\",\"text\":\"图片是啥\"},
          {\"type\":\"image_url\",\"image_url\":{\"url\":\"$IMAGE_URL\"}}
        ]}],
        \"stream\": false
      }' | jq ."

# 10. 测试OpenAI多模态文字+图片流式
run_test "OpenAI多模态文字+网络图片流式" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"deepseek-chat\",
        \"messages\": [{\"role\": \"user\", \"content\": [
          {\"type\":\"text\",\"text\":\"图片是啥\"},
          {\"type\":\"image_url\",\"image_url\":{\"url\":\"$IMAGE_URL\"}}
        ]}],
        \"stream\": true
      }'"