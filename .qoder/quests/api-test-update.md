# API测试用例更新设计

## 概述

本设计文档描述了对现有test.sh测试脚本进行增强的技术方案，基于消息过滤与Claude支持功能的需求，添加相应的测试用例来验证系统的健壮性和兼容性。

### 核心测试目标
1. 验证消息过滤功能的正确性
2. 测试Claude协议的完整支持
3. 验证流式响应的格式兼容性
4. 测试边界条件和错误处理
5. 验证新增功能的稳定性

### 测试原则
- **全面覆盖**：覆盖所有主要功能和边界情况
- **真实场景**：模拟实际客户端的使用模式
- **格式验证**：确保响应格式符合协议规范
- **错误处理**：验证各种异常情况的处理

## 现有测试分析

### 当前test.sh测试覆盖范围
1. 基础模型列表获取
2. OpenAI协议文字对话（流式/非流式）
3. Claude协议基础对话
4. 多模态文字内容测试
5. 网络图片处理测试

### 测试不足之处
1. **缺少消息过滤测试**：无效消息、空消息等边界情况
2. **Claude协议不完整**：缺少thinking参数、流式响应等测试
3. **错误处理验证不足**：缺少各种错误场景的测试
4. **客户端兼容性测试**：缺少真实客户端请求头的测试
5. **参数兼容性测试**：缺少未知参数、格式错误参数的测试

## 新增测试用例设计

### 1. 消息过滤功能测试

#### 1.1 无效消息过滤测试
``bash
# 测试缺少role字段的消息
run_test "消息过滤-缺少role字段" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [
          {\"content\": \"这条消息缺少role字段\"},
          {\"role\": \"user\", \"content\": \"这是有效消息\"}
        ],
        \"stream\": false
      }' | jq ."

# 测试缺少content字段的消息
run_test "消息过滤-缺少content字段" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [
          {\"role\": \"user\"},
          {\"role\": \"user\", \"content\": \"这是有效消息\"}
        ],
        \"stream\": false
      }' | jq ."

# 测试空content的消息
run_test "消息过滤-空content内容" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [
          {\"role\": \"user\", \"content\": \"\"},
          {\"role\": \"user\", \"content\": \"这是有效消息\"}
        ],
        \"stream\": false
      }' | jq ."

# 测试无效role的消息
run_test "消息过滤-无效role值" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [
          {\"role\": \"invalid_role\", \"content\": \"无效角色消息\"},
          {\"role\": \"user\", \"content\": \"这是有效消息\"}
        ],
        \"stream\": false
      }' | jq ."
```

#### 1.2 混合消息类型测试
``bash
# 测试混合有效和无效消息
run_test "消息过滤-混合消息类型" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [
          {\"role\": \"system\", \"content\": \"你是一个有用的助手\"},
          {\"content\": \"无效消息1\"},
          {\"role\": \"user\", \"content\": \"用户消息1\"},
          {\"role\": \"invalid\", \"content\": \"无效消息2\"},
          {\"role\": \"user\", \"content\": \"\"},
          {\"role\": \"user\", \"content\": \"用户消息2\"}
        ],
        \"stream\": false
      }' | jq ."
```

### 2. Claude协议增强测试

#### 2.1 Claude thinking参数测试
```bash
# 测试Claude thinking参数（非流式）
run_test "Claude协议-thinking参数非流式" \
    "curl -s -X POST $API_URL/api/v1/messages \
      -H 'Content-Type: application/json' \
      -H 'x-api-key: $ANTHROPIC_API_KEY' \
      -H 'anthropic-version: 2023-06-01' \
      -d '{
        \"model\": \"claude-opus-4-20250514\",
        \"max_tokens\": 1000,
        \"thinking\": {\"type\": \"enabled\"},
        \"messages\": [
          {
            \"role\": \"user\",
            \"content\": \"请解释量子计算的基本原理\"
          }
        ]
      }' | jq ."

# 测试Claude thinking参数（流式）
run_test "Claude协议-thinking参数流式" \
    "curl -s -X POST $API_URL/api/v1/messages \
      -H 'Content-Type: application/json' \
      -H 'x-api-key: $ANTHROPIC_API_KEY' \
      -H 'anthropic-version: 2023-06-01' \
      -d '{
        \"model\": \"claude-opus-4-20250514\",
        \"max_tokens\": 1000,
        \"thinking\": {\"type\": \"enabled\"},
        \"stream\": true,
        \"messages\": [
          {
            \"role\": \"user\",
            \"content\": \"分析一下市场趋势\"
          }
        ]
      }'"
```

#### 2.2 Claude协议完整性测试
``bash
# 测试Claude协议所有参数
run_test "Claude协议-完整参数测试" \
    "curl -s -X POST $API_URL/api/v1/messages \
      -H 'Content-Type: application/json' \
      -H 'x-api-key: $ANTHROPIC_API_KEY' \
      -H 'anthropic-version: 2023-06-01' \
      -H 'anthropic-beta: claude-3-5-sonnet-20241022' \
      -d '{
        \"model\": \"claude-opus-4-20250514\",
        \"max_tokens\": 1000,
        \"temperature\": 0.7,
        \"top_p\": 0.9,
        \"stream\": false,
        \"stop_sequences\": [\"\\n\\n\"],
        \"system\": \"你是一个专业的AI助手\",
        \"session_id\": \"test_session_123\",
        \"user_id\": \"test_user_456\",
        \"messages\": [
          {
            \"role\": \"user\",
            \"content\": \"介绍一下人工智能的发展历程\"
          }
        ]
      }' | jq ."

# 测试Claude协议未知参数兼容性
run_test "Claude协议-未知参数兼容性" \
    "curl -s -X POST $API_URL/api/v1/messages \
      -H 'Content-Type: application/json' \
      -H 'x-api-key: $ANTHROPIC_API_KEY' \
      -H 'anthropic-version: 2023-06-01' \
      -d '{
        \"model\": \"claude-opus-4-20250514\",
        \"max_tokens\": 1000,
        \"unknown_param1\": \"should_be_ignored\",
        \"custom_setting\": {\"value\": 123},
        \"experimental_flag\": true,
        \"messages\": [
          {
            \"role\": \"user\",
            \"content\": \"你好，测试未知参数\"
          }
        ]
      }' | jq ."
```

### 3. 真实客户端兼容性测试

#### 3.1 Cherry Studio客户端测试
```bash
# 模拟Cherry Studio客户端请求
run_test "客户端兼容-Cherry Studio" \
    "curl -s 'http://localhost:7860/api/v1/chat/completions' \
      -H 'Accept-Language: zh-CN' \
      -H 'Connection: keep-alive' \
      -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) CherryStudio/1.5.7 Chrome/138.0.7204.100 Electron/37.2.3 Safari/537.36' \
      -H 'accept: application/json' \
      -H 'authorization: Bearer $OPENAI_API_KEY' \
      -H 'content-type: application/json' \
      -H 'http-referer: https://cherry-ai.com' \
      -H 'x-api-key: $OPENAI_API_KEY' \
      -H 'x-stainless-retry-count: 0' \
      -H 'x-stainless-timeout: 600' \
      -H 'x-title: Cherry Studio' \
      --data-raw '{
        \"model\":\"deepseek-chat\",
        \"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],
        \"temperature\":1,
        \"top_p\":1,
        \"stream\":true,
        \"stream_options\":{\"include_usage\":true}
      }'"

# 模拟Cherry Studio非流式请求
run_test "客户端兼容-Cherry Studio非流式" \
    "curl -s 'http://localhost:7860/api/v1/chat/completions' \
      -H 'Accept-Language: zh-CN' \
      -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) CherryStudio/1.5.7 Chrome/138.0.7204.100 Electron/37.2.3 Safari/537.36' \
      -H 'authorization: Bearer $OPENAI_API_KEY' \
      -H 'content-type: application/json' \
      -H 'x-api-key: $OPENAI_API_KEY' \
      --data-raw '{
        \"model\":\"deepseek-chat\",
        \"messages\":[{\"role\":\"user\",\"content\":\"你好，请简单介绍一下你自己\"}],
        \"temperature\":0.7,
        \"top_p\":1,
        \"stream\":false,
        \"stream_options\":{\"include_usage\":true}
      }' | jq ."
```

#### 3.2 其他客户端模拟测试
``bash
# 模拟cURL标准客户端
run_test "客户端兼容-标准cURL" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -H 'User-Agent: curl/7.81.0' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [{\"role\": \"user\", \"content\": \"测试标准cURL客户端\"}],
        \"stream\": false
      }' | jq ."

# 模拟Python requests客户端
run_test "客户端兼容-Python requests" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -H 'User-Agent: python-requests/2.28.1' \
      -H 'Accept: application/json' \
      -H 'Accept-Encoding: gzip, deflate' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [{\"role\": \"user\", \"content\": \"测试Python客户端\"}],
        \"stream\": false
      }' | jq ."
```

### 4. 流式响应格式测试

#### 4.1 Claude流式响应格式验证
```bash
# 测试Claude流式响应格式（完整事件序列）
run_test "Claude流式-完整事件序列" \
    "curl -s -X POST $API_URL/api/v1/messages \
      -H 'Content-Type: application/json' \
      -H 'x-api-key: $ANTHROPIC_API_KEY' \
      -H 'anthropic-version: 2023-06-01' \
      -d '{
        \"model\": \"claude-opus-4-20250514\",
        \"max_tokens\": 1000,
        \"stream\": true,
        \"messages\": [
          {
            \"role\": \"user\",
            \"content\": \"请用100字左右介绍机器学习\"
          }
        ]
      }' | head -50"

# 测试Claude流式响应的SSE格式
run_test "Claude流式-SSE格式验证" \
    "curl -s -X POST $API_URL/api/v1/messages \
      -H 'Content-Type: application/json' \
      -H 'x-api-key: $ANTHROPIC_API_KEY' \
      -H 'anthropic-version: 2023-06-01' \
      -d '{
        \"model\": \"claude-opus-4-20250514\",
        \"max_tokens\": 500,
        \"stream\": true,
        \"messages\": [
          {
            \"role\": \"user\",
            \"content\": \"简单说说天气\"
          }
        ]
      }' | grep -E '^(event:|data:)' | head -20"
```

#### 4.2 OpenAI流式响应格式测试
```bash
# 测试OpenAI流式响应与stream_options
run_test "OpenAI流式-stream_options测试" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [{\"role\": \"user\", \"content\": \"测试流式响应格式\"}],
        \"stream\": true,
        \"stream_options\": {\"include_usage\": true}
      }' | head -30"
```

### 5. 错误处理和边界条件测试

#### 5.1 空消息列表测试
```bash
# 测试完全空的消息列表
run_test "错误处理-空消息列表" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [],
        \"stream\": false
      }' | jq ."

# 测试过滤后为空的消息列表
run_test "错误处理-过滤后空消息" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [
          {\"content\": \"无role字段\"},
          {\"role\": \"user\", \"content\": \"\"},
          {\"role\": \"invalid_role\", \"content\": \"无效角色\"}
        ],
        \"stream\": false
      }' | jq ."
```

#### 5.2 参数格式错误测试
```bash
# 测试非法JSON格式
run_test "错误处理-非法JSON" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [{\"role\": \"user\", \"content\": \"测试\"}],
        \"temperature\": \"invalid_number\",
        \"stream\": false
      }' | jq ."

# 测试超大数值参数
run_test "错误处理-超大参数值" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [{\"role\": \"user\", \"content\": \"测试\"}],
        \"temperature\": 999999,
        \"max_tokens\": -1,
        \"stream\": false
      }' | | jq ."
```

#### 5.3 认证错误测试
```bash
# 测试无效的认证Token
run_test "错误处理-无效Token" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer invalid_token_123' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [{\"role\": \"user\", \"content\": \"测试\"}],
        \"stream\": false
      }' | jq ."

# 测试缺少认证头
run_test "错误处理-缺少认证" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [{\"role\": \"user\", \"content\": \"测试\"}],
        \"stream\": false
      }' | jq ."
```

### 6. 性能和稳定性测试

#### 6.1 长消息处理测试
```bash
# 生成长消息内容
LONG_MESSAGE=$(printf "这是一个很长的消息内容，重复1000次。%.0s" {1..100})

# 测试长消息处理
run_test "性能测试-长消息处理" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [{\"role\": \"user\", \"content\": \"$LONG_MESSAGE\"}],
        \"stream\": false,
        \"max_tokens\": 100
      }' | jq '.choices[0].message.content | length'"
```

#### 6.2 并发请求测试
```bash
# 测试多个并发请求
run_test "性能测试-并发请求" \
    "for i in {1..3}; do
      curl -s -X POST $API_URL/api/v1/chat/completions \
        -H 'Content-Type: application/json' \
        -H 'Authorization: Bearer $OPENAI_API_KEY' \
        -d '{
          \"model\": \"auto\",
          \"messages\": [{\"role\": \"user\", \"content\": \"并发测试$i\"}],
          \"stream\": false
        }' &
    done
    wait
    echo '并发请求测试完成'"
```

## 测试脚本结构优化

### 新的测试函数
```bash
# 增强的测试函数，支持更多验证
run_test_advanced() {
    local test_name="$1"
    local test_command="$2"
    local expected_status="$3"  # 可选，预期HTTP状态码
    local validation_script="$4"  # 可选，结果验证脚本
    
    echo "==============================================="
    echo "测试 $test_name"
    echo "==============================================="
    
    # 执行测试命令
    local result=$(eval "$test_command")
    local exit_code=$?
    
    echo "$result"
    
    # 状态码验证
    if [[ -n "$expected_status" ]]; then
        local actual_status=$(echo "$result" | jq -r '.status // 200' 2>/dev/null || echo "200")
        if [[ "$actual_status" != "$expected_status" ]]; then
            echo "❌ 状态码验证失败: 期望 $expected_status, 实际 $actual_status"
        else
            echo "✅ 状态码验证通过: $expected_status"
        fi
    fi
    
    # 自定义验证
    if [[ -n "$validation_script" ]]; then
        if eval "$validation_script" <<< "$result"; then
            echo "✅ 自定义验证通过"
        else
            echo "❌ 自定义验证失败"
        fi
    fi
    
    echo -e "\n\n"
}

# 响应格式验证函数
validate_openai_response() {
    local response="$1"
    echo "$response" | jq -e '.choices[0].message.content' > /dev/null
}

validate_claude_response() {
    local response="$1"
    echo "$response" | jq -e '.content[0].text' > /dev/null
}

# 流式响应验证函数
validate_sse_format() {
    local response="$1"
    echo "$response" | grep -q "^data:" && echo "$response" | grep -q "^event:"
}
```

## 测试执行策略

### 测试分组
1. **基础功能测试**：现有的基本功能验证
2. **增强功能测试**：新增的消息过滤和Claude支持
3. **兼容性测试**：各种客户端和协议的兼容性
4. **错误处理测试**：各种异常情况的处理
5. **性能测试**：系统性能和稳定性验证

### 测试顺序
1. 首先执行基础功能测试，确保系统正常运行
2. 然后执行增强功能测试，验证新功能
3. 接着执行兼容性测试，确保向后兼容
4. 最后执行错误处理和性能测试

### 测试输出格式
```bash
# 测试结果统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 在每个测试结束后更新统计
update_test_stats() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [[ $1 == "pass" ]]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# 最终测试报告
print_test_summary() {
    echo "==============================================="
    echo "测试总结"
    echo "==============================================="
    echo "总测试数: $TOTAL_TESTS"
    echo "通过: $PASSED_TESTS"
    echo "失败: $FAILED_TESTS"
    echo "成功率: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"
    echo "==============================================="
}
```

## test.sh具体更新代码

### 在test.sh文件末尾添加以下测试用例

```bash
# ===============================================
# 新增测试用例 - 基于消息过滤与Claude支持功能
# ===============================================

# 11. 消息过滤功能测试
run_test "消息过滤-缺少role字段" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [
          {\"content\": \"这条消息缺少role字段\"},
          {\"role\": \"user\", \"content\": \"这是有效消息\"}
        ],
        \"stream\": false
      }' | jq ."

# 12. 测试缺少content字段的消息
run_test "消息过滤-缺少content字段" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [
          {\"role\": \"user\"},
          {\"role\": \"user\", \"content\": \"这是有效消息\"}
        ],
        \"stream\": false
      }' | jq ."

# 13. 测试空content的消息
run_test "消息过滤-空content内容" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [
          {\"role\": \"user\", \"content\": \"\"},
          {\"role\": \"user\", \"content\": \"这是有效消息\"}
        ],
        \"stream\": false
      }' | jq ."

# 14. 测试无效role的消息
run_test "消息过滤-无效role值" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [
          {\"role\": \"invalid_role\", \"content\": \"无效角色消息\"},
          {\"role\": \"user\", \"content\": \"这是有效消息\"}
        ],
        \"stream\": false
      }' | jq ."

# 15. 测试混合有效和无效消息
run_test "消息过滤-混合消息类型" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [
          {\"role\": \"system\", \"content\": \"你是一个有用的助手\"},
          {\"content\": \"无效消息1\"},
          {\"role\": \"user\", \"content\": \"用户消息1\"},
          {\"role\": \"invalid\", \"content\": \"无效消息2\"},
          {\"role\": \"user\", \"content\": \"\"},
          {\"role\": \"user\", \"content\": \"用户消息2\"}
        ],
        \"stream\": false
      }' | jq ."

# 16. Claude thinking参数测试（非流式）
run_test "Claude协议-thinking参数非流式" \
    "curl -s -X POST $API_URL/api/v1/messages \
      -H 'Content-Type: application/json' \
      -H 'x-api-key: $ANTHROPIC_API_KEY' \
      -H 'anthropic-version: 2023-06-01' \
      -d '{
        \"model\": \"claude-opus-4-20250514\",
        \"max_tokens\": 1000,
        \"thinking\": {\"type\": \"enabled\"},
        \"messages\": [
          {
            \"role\": \"user\",
            \"content\": \"请简单解释一下机器学习\"
          }
        ]
      }' | jq ."

# 17. Claude thinking参数测试（流式）
run_test "Claude协议-thinking参数流式" \
    "curl -s -X POST $API_URL/api/v1/messages \
      -H 'Content-Type: application/json' \
      -H 'x-api-key: $ANTHROPIC_API_KEY' \
      -H 'anthropic-version: 2023-06-01' \
      -d '{
        \"model\": \"claude-opus-4-20250514\",
        \"max_tokens\": 1000,
        \"thinking\": {\"type\": \"enabled\"},
        \"stream\": true,
        \"messages\": [
          {
            \"role\": \"user\",
            \"content\": \"分析一下AI的发展趋势\"
          }
        ]
      }'"

# 18. Claude协议完整参数测试
run_test "Claude协议-完整参数测试" \
    "curl -s -X POST $API_URL/api/v1/messages \
      -H 'Content-Type: application/json' \
      -H 'x-api-key: $ANTHROPIC_API_KEY' \
      -H 'anthropic-version: 2023-06-01' \
      -H 'anthropic-beta: claude-3-5-sonnet-20241022' \
      -d '{
        \"model\": \"claude-opus-4-20250514\",
        \"max_tokens\": 1000,
        \"temperature\": 0.7,
        \"top_p\": 0.9,
        \"stream\": false,
        \"stop_sequences\": [\"\\n\\n\"],
        \"system\": \"你是一个专业的AI助手\",
        \"session_id\": \"test_session_123\",
        \"user_id\": \"test_user_456\",
        \"messages\": [
          {
            \"role\": \"user\",
            \"content\": \"介绍一下人工智能的发展历程\"
          }
        ]
      }' | jq ."

# 19. Claude协议未知参数兼容性测试
run_test "Claude协议-未知参数兼容性" \
    "curl -s -X POST $API_URL/api/v1/messages \
      -H 'Content-Type: application/json' \
      -H 'x-api-key: $ANTHROPIC_API_KEY' \
      -H 'anthropic-version: 2023-06-01' \
      -d '{
        \"model\": \"claude-opus-4-20250514\",
        \"max_tokens\": 1000,
        \"unknown_param1\": \"should_be_ignored\",
        \"custom_setting\": {\"value\": 123},
        \"experimental_flag\": true,
        \"messages\": [
          {
            \"role\": \"user\",
            \"content\": \"你好，测试未知参数\"
          }
        ]
      }' | jq ."

# 20. Cherry Studio客户端兼容性测试（流式）
run_test "客户端兼容-Cherry Studio流式" \
    "curl -s 'http://localhost:7860/api/v1/chat/completions' \
      -H 'Accept-Language: zh-CN' \
      -H 'Connection: keep-alive' \
      -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) CherryStudio/1.5.7 Chrome/138.0.7204.100 Electron/37.2.3 Safari/537.36' \
      -H 'accept: application/json' \
      -H 'authorization: Bearer $OPENAI_API_KEY' \
      -H 'content-type: application/json' \
      -H 'http-referer: https://cherry-ai.com' \
      -H 'x-api-key: $OPENAI_API_KEY' \
      -H 'x-stainless-retry-count: 0' \
      -H 'x-stainless-timeout: 600' \
      -H 'x-title: Cherry Studio' \
      --data-raw '{
        \"model\":\"deepseek-chat\",
        \"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],
        \"temperature\":1,
        \"top_p\":1,
        \"stream\":true,
        \"stream_options\":{\"include_usage\":true}
      }'"

# 21. Cherry Studio客户端兼容性测试（非流式）
run_test "客户端兼容-Cherry Studio非流式" \
    "curl -s 'http://localhost:7860/api/v1/chat/completions' \
      -H 'Accept-Language: zh-CN' \
      -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) CherryStudio/1.5.7 Chrome/138.0.7204.100 Electron/37.2.3 Safari/537.36' \
      -H 'authorization: Bearer $OPENAI_API_KEY' \
      -H 'content-type: application/json' \
      -H 'x-api-key: $OPENAI_API_KEY' \
      --data-raw '{
        \"model\":\"deepseek-chat\",
        \"messages\":[{\"role\":\"user\",\"content\":\"你好，请简单介绍一下你自己\"}],
        \"temperature\":0.7,
        \"top_p\":1,
        \"stream\":false,
        \"stream_options\":{\"include_usage\":true}
      }' | jq ."

# 22. Claude流式响应格式验证
run_test "Claude流式-完整事件序列" \
    "curl -s -X POST $API_URL/api/v1/messages \
      -H 'Content-Type: application/json' \
      -H 'x-api-key: $ANTHROPIC_API_KEY' \
      -H 'anthropic-version: 2023-06-01' \
      -d '{
        \"model\": \"claude-opus-4-20250514\",
        \"max_tokens\": 1000,
        \"stream\": true,
        \"messages\": [
          {
            \"role\": \"user\",
            \"content\": \"请用100字左右介绍机器学习\"
          }
        ]
      }' | head -50"

# 23. Claude SSE格式验证
run_test "Claude流式-SSE格式验证" \
    "curl -s -X POST $API_URL/api/v1/messages \
      -H 'Content-Type: application/json' \
      -H 'x-api-key: $ANTHROPIC_API_KEY' \
      -H 'anthropic-version: 2023-06-01' \
      -d '{
        \"model\": \"claude-opus-4-20250514\",
        \"max_tokens\": 500,
        \"stream\": true,
        \"messages\": [
          {
            \"role\": \"user\",
            \"content\": \"简单说说天气\"
          }
        ]
      }' | grep -E '^(event:|data:)' | head -20"

# 24. OpenAI流式响应与stream_options测试
run_test "OpenAI流式-stream_options测试" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [{\"role\": \"user\", \"content\": \"测试流式响应格式\"}],
        \"stream\": true,
        \"stream_options\": {\"include_usage\": true}
      }' | head -30"

# 25. 错误处理测试 - 空消息列表
run_test "错误处理-空消息列表" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [],
        \"stream\": false
      }' | jq ."

# 26. 错误处理测试 - 过滤后空消息
run_test "错误处理-过滤后空消息" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [
          {\"content\": \"无role字段\"},
          {\"role\": \"user\", \"content\": \"\"},
          {\"role\": \"invalid_role\", \"content\": \"无效角色\"}
        ],
        \"stream\": false
      }' | jq ."

# 27. 参数兼容性测试 - 超大数值
run_test "错误处理-超大参数值" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [{\"role\": \"user\", \"content\": \"测试\"}],
        \"temperature\": 999999,
        \"max_tokens\": -1,
        \"stream\": false
      }' | jq ."

# 28. 多模态消息过滤测试
run_test "消息过滤-多模态消息" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"deepseek-chat\",
        \"messages\": [
          {\"role\": \"user\", \"content\": []},
          {\"role\": \"user\", \"content\": [{\"type\":\"text\",\"text\":\"有效的多模态消息\"}]}
        ],
        \"stream\": false
      }' | jq ."

# 29. 模型自动选择与消息过滤组合测试
run_test "消息过滤+模型自动选择" \
    "curl -s -X POST $API_URL/api/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [
          {\"role\": \"system\", \"content\": \"你是一个助手\"},
          {\"content\": \"无效消息\"},
          {\"role\": \"user\", \"content\": \"请介绍你自己\"},
          {\"role\": \"user\", \"content\": \"\"}
        ],
        \"stream\": false
      }' | jq ."

# 30. 健康检查测试
run_test "健康检查" \
    "curl -s $API_URL/health | jq ."

echo "==============================================="
echo "测试完成！共执行了30个测试用例"
echo "包括：基础功能测试、消息过滤测试、Claude协议测试、客户端兼容性测试、错误处理测试"
echo "==============================================="
```

## 执行说明

### 1. 更新test.sh文件
将上述代码添加到现有test.sh文件的末尾，替换最后的测试用例10的位置开始。

### 2. 测试前准备
确保以下环境变量正确设置：
- `API_URL`: 指向本地服务器地址
- `OPENAI_API_KEY`: 有效的API密钥
- `ANTHROPIC_API_KEY`: 有效的Anthropic API密钥

### 3. 执行测试
```bash
# 给脚本执行权限
chmod +x test.sh

# 执行测试
./test.sh
```

### 4. 验证重点
测试执行时需要重点关注：
1. **消息过滤效果**：无效消息是否被正确过滤
2. **Claude协议支持**：thinking参数是否被正确处理
3. **客户端兼容性**：真实客户端请求是否正常工作
4. **错误处理**：异常情况是否有合适的错误响应
5. **响应格式**：流式和非流式响应格式是否正确

## 特定问题修复

### Cherry Studio客户端兼容性问题

#### 问题描述
用户提到的Cherry Studio客户端请求现在无法正常运行，具体表现为：
```bash
curl 'http://0.0.0.0:7860/api/v1/chat/completions' \
  -H 'Accept-Language: zh-CN' \
  -H 'Connection: keep-alive' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) CherryStudio/1.5.7 Chrome/138.0.7204.100 Electron/37.2.3 Safari/537.36' \
  -H 'accept: application/json' \
  -H 'authorization: Bearer hf' \
  -H 'content-type: application/json' \
  -H 'http-referer: https://cherry-ai.com' \
  -H 'x-api-key: hf' \
  -H 'x-stainless-retry-count: 0' \
  -H 'x-stainless-timeout: 600' \
  -H 'x-title: Cherry Studio' \
  --data-raw '{"model":"deepseek-chat","messages":[{"role":"user","content":"hi"}],"temperature":1,"top_p":1,"stream":true,"stream_options":{"include_usage":true}}'
```

#### 可能原因分析
1. **认证问题**：可能TOKEN验证逻辑发生变化
2. **参数处理问题**：stream_options参数可能未被正确处理
3. **请求头处理**：大量自定义请求头可能导致问题
4. **流式响应格式**：流式响应的格式可能不兼容

#### 修复策略
1. **增强参数兼容性**：在more_core.py中确保对stream_options等参数的正确处理
2. **请求头过滤**：忽略不相关的请求头，只保留核心认证和内容类型头
3. **流式响应优化**：确保流式响应格式完全符合OpenAI标准
4. **错误日志增强**：添加详细的调试信息帮助定位问题

#### 测试验证
在新的测试用例中专门包含了Cherry Studio的请求格式，用于验证兼容性：
- 测试20：Cherry Studio流式请求
- 测试21：Cherry Studio非流式请求

### 消息过滤功能验证

#### 目标
验证消息过滤功能是否按照设计文档正确实现：
1. 过滤缺少role字段的消息
2. 过滤缺少content字段的消息
3. 过滤空content的消息
4. 过滤无效role值的消息
5. 处理混合有效/无效消息的情况

#### 验证方法
通过测试用例11-15和25-29，模拟各种无效消息场景，验证：
- 系统是否正确过滤无效消息
- 是否保留有效消息进行处理
- 当所有消息都被过滤后是否返回合适的错误
- 过滤逻辑是否影响正常功能

### Claude协议thinking参数支持

#### 目标
验证thinking参数是否按照设计要求正确处理：
1. thinking参数仅记录，不透传给degpt.py
2. 支持流式和非流式两种模式
3. 响应格式符合Claude标准
4. 未知参数能够正确忽略

#### 验证方法
通过测试用例16-19，测试：
- thinking参数在非流式模式下的处理
- thinking参数在流式模式下的处理
- Claude协议的完整参数支持
- 未知参数的兼容性处理

### 流式响应格式修复

#### 目标
确保流式响应格式完全符合各协议标准：
1. OpenAI流式响应格式正确
2. Claude SSE事件格式正确
3. stream_options参数正确处理
4. 事件序列完整性

#### 验证方法
通过测试用例22-24，验证：
- Claude流式响应的完整事件序列
- SSE格式的正确性（event:和data:行）
- OpenAI流式响应与stream_options的配合
- 事件终止和错误处理

## 预期测试结果

### 成功标准
1. **基础功能测试**：所有原有功能正常工作
2. **消息过滤测试**：无效消息被正确过滤，有效消息正常处理
3. **Claude协议测试**：thinking等参数正确处理，响应格式符合标准
4. **客户端兼容性测试**：Cherry Studio等真实客户端能够正常工作
5. **错误处理测试**：各种异常情况返回合适的错误响应

### 失败排查
如果测试失败，按以下顺序排查：
1. 检查服务是否正常启动（health检查）
2. 验证API密钥配置是否正确
3. 检查消息过滤逻辑是否过于严格
4. 验证Claude协议转换是否正确
5. 检查流式响应格式是否标准

### 性能验证
除功能正确性外，还需验证：
1. 响应时间是否在可接受范围内
2. 内存使用是否正常
3. 并发处理能力是否满足需求
4. 长消息处理是否稳定

## 用户需求测试用例校准

### 用户提供的测试用例分析

根据用户提供的测试脚本，我发现以下需要校准的关键问题：

#### 1. API端点路径校准
**问题**：用户脚本中的部分端点路径与项目实际支持的不一致

**校准建议**：
- ✅ **正确**：`/v1/chat/completions` （OpenAI协议）
- ✅ **正确**：`/v1/messages` （Claude协议） 
- ❌ **错误**：用户脚本中使用了 `/v1/messages`，但根据项目知识应该是 `/api/v1/messages`

**修正**：
``bash
# 错误的端点
curl -s -X POST $API_URL/v1/messages

# 正确的端点
curl -s -X POST $API_URL/api/v1/messages
```

#### 2. 模型名称校准
**问题**：用户脚本中使用的模型名称可能与项目实际支持的不完全匹配

**校准建议**：
根据项目知识，实际支持的模型包括：
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229` 
- `claude-3-haiku-20240307`
- `claude-2.1`、`claude-2.0`、`claude-instant-1.2`
- OpenAI模型通过`auto`自动选择或使用具体模型名

**修正**：
``bash
# 用户脚本中的模型名（可能不存在）
"model": "claude-sonnet-4-20250514"
"model": "claude-opus-4-20250514"

# 建议使用的模型名
"model": "claude-3-sonnet-20240229"
"model": "claude-3-opus-20240229"
```

#### 3. 特殊功能支持校准
**问题**：用户脚本中的一些高级功能可能未在当前项目中实现

**校准建议**：

**a) Thinking功能**：
- ✅ **支持**：根据设计文档，thinking参数已被支持但仅记录不透传
- ⚠️ **注意**：响应格式需要验证是否完全符合Claude标准

**b) 工具使用（Tools）**：
- ❓ **待验证**：项目知识中提到了工具相关的转换，但具体实现程度需要测试验证
- 建议先进行简单的工具测试，再进行复杂的工具链测试

**c) 提示缓存（Cache Control）**：
- ❓ **待验证**：项目知识中未明确提及cache_control的支持
- 建议测试时注意观察是否有相关错误或警告

#### 4. 认证方式校准
**问题**：认证配置可能需要根据实际部署环境调整

**校准建议**：
```bash
# 根据项目设置，如果设置了TOKEN环境变量
# OpenAI协议使用
-H 'Authorization: Bearer $OPENAI_API_KEY'

# Claude协议使用  
-H 'x-api-key: $ANTHROPIC_API_KEY'

# 如果未设置TOKEN环境变量，可能不需要认证头
```

### 完善后的校准测试脚本

```
#!/bin/bash

# === API 配置 ===
API_URL="http://localhost:7860"
OPENAI_API_KEY="YOUR_OPENAI_API_KEY"     
ANTHROPIC_API_KEY="YOUR_ANTHROPIC_API_KEY" 

# === 测试图片 URL ===
IMAGE_URL="https://img0.baidu.com/it/u=337102486,1971914968&fm=253&app=138&f=JPEG?w=800&h=1062"

# === 测试函数 ===
run_test() {
    echo "==============================================="
    echo "测试 $1"
    echo "==============================================="
    eval "$2"
    echo -e "\n\n"
}

# === 健康检查（优先执行） ===
run_test "服务健康检查" \
    "curl -s $API_URL/health | jq ."

# === OpenAI 兼容性测试 ===

# 1.1 OpenAI 文本对话 - 非流式
run_test "OpenAI 文本对话 - 非流式" \
    "curl -s -X POST $API_URL/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [{\"role\": \"user\", \"content\": \"你好，你是谁？\"}],
        \"stream\": false
      }' | jq ."

# 1.2 OpenAI 文本对话 - 流式
run_test "OpenAI 文本对话 - 流式" \
    "curl -s -X POST $API_URL/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [{\"role\": \"user\", \"content\": \"你好，你是谁？\"}],
        \"stream\": true
      }' | head -20"

# 2.1 OpenAI 多模态文本 - 非流式
run_test "OpenAI 多模态文本 - 非流式" \
    "curl -s -X POST $API_URL/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [{\"role\": \"user\", \"content\": [{\"type\":\"text\",\"text\":\"你好，你是谁？\"}]}],
        \"stream\": false
      }' | jq ."

# 2.2 OpenAI 多模态文本 - 流式
run_test "OpenAI 多模态文本 - 流式" \
    "curl -s -X POST $API_URL/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [{\"role\": \"user\", \"content\": [{\"type\":\"text\",\"text\":\"你好，你是谁？\"}]}],
        \"stream\": true
      }' | head -20"

# 3.1 OpenAI 多模态识图+文本 - 非流式
run_test "OpenAI 多模态识图+文本 - 非流式" \
    "curl -s -X POST $API_URL/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [{\"role\": \"user\", \"content\": [
          {\"type\":\"text\",\"text\":\"这张图片里有什么？\"},
          {\"type\":\"image_url\",\"image_url\":{\"url\":\"$IMAGE_URL\"}}
        ]}],
        \"stream\": false
      }' | jq ."

# 3.2 OpenAI 多模态识图+文本 - 流式
run_test "OpenAI 多模态识图+文本 - 流式" \
    "curl -s -X POST $API_URL/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer $OPENAI_API_KEY' \
      -d '{
        \"model\": \"auto\",
        \"messages\": [{\"role\": \"user\", \"content\": [
          {\"type\":\"text\",\"text\":\"这张图片里有什么？\"},
          {\"type\":\"image_url\",\"image_url\":{\"url\":\"$IMAGE_URL\"}}
        ]}],
        \"stream\": true
      }' | head -30"

# === Claude 兼容性测试 ===

# 4.1 Claude 文本对话 - 非流式（修正端点路径）
run_test "Claude 文本对话 - 非流式" \
    "curl -s -X POST $API_URL/api/v1/messages \
      -H 'Content-Type: application/json' \
      -H 'x-api-key: $ANTHROPIC_API_KEY' \
      -H 'anthropic-version: 2023-06-01' \
      -d '{
        \"model\": \"claude-3-haiku-20240307\",
        \"max_tokens\": 1000,
        \"messages\": [
          {
            \"role\": \"user\",
            \"content\": \"你好，你是谁？\"
          }
        ],
        \"stream\": false
      }' | jq ."

# 4.2 Claude 文本对话 - 流式（修正端点路径）
run_test "Claude 文本对话 - 流式" \
    "curl -s -X POST $API_URL/api/v1/messages \
      -H 'Content-Type: application/json' \
      -H 'x-api-key: $ANTHROPIC_API_KEY' \
      -H 'anthropic-version: 2023-06-01' \
      -d '{
        \"model\": \"claude-3-haiku-20240307\",
        \"max_tokens\": 1000,
        \"messages\": [
          {
            \"role\": \"user\",
            \"content\": \"你好，你是谁？\"
          }
        ],
        \"stream\": true
      }' | head -20"

# 5.1 Claude 扩展思维 (Extended Thinking) - 流式（修正模型名和端点）
run_test "Claude 扩展思维 - 流式" \
    "curl -s -X POST $API_URL/api/v1/messages \
      -H 'x-api-key: $ANTHROPIC_API_KEY' \
      -H 'anthropic-version: 2023-06-01' \
      -H 'content-type: application/json' \
      -d '{
        \"model\": \"claude-3-sonnet-20240229\",
        \"max_tokens\": 16000,
        \"stream\": true,
        \"thinking\": {
            \"type\": \"enabled\",
            \"budget_tokens\": 10000
        },
        \"messages\": [
            {
                \"role\": \"user\",
                \"content\": \"计算 12345 * 6789 的结果，并解释你的步骤。\"
            }
        ]
      }' | head -30"

# 5.2 Claude 工具使用 (Tool Use) - 流式（修正模型名和端点）
run_test "Claude 工具使用 - 流式" \
    "curl -s -X POST $API_URL/api/v1/messages \
      -H 'content-type: application/json' \
      -H 'x-api-key: $ANTHROPIC_API_KEY' \
      -H 'anthropic-version: 2023-06-01' \
      -d '{
        \"model\": \"claude-3-opus-20240229\",
        \"max_tokens\": 1024,
        \"tools\": [
          {
            \"name\": \"get_weather\",
            \"description\": \"获取指定地点的当前天气\",
            \"input_schema\": {
              \"type\": \"object\",
              \"properties\": {
                \"location\": {
                  \"type\": \"string\",
                  \"description\": \"城市和州，例如 San Francisco, CA\"
                }
              },
              \"required\": [\"location\"]
            }
          }
        ],
        \"tool_choice\": {\"type\": \"any\"},
        \"messages\": [
          {
            \"role\": \"user\",
            \"content\": \"今天旧金山的天气怎么样？\"
          }
        ],
        \"stream\": true
      }' | head -30"

# 5.3 Claude 提示缓存 (Prompt Caching) - 非流式（修正模型名和端点）
LONG_DOCUMENT_CONTENT="这是用于提示缓存的长文档内容示例。它应该足够长才能体现缓存的价值。在实际的应用场景中，这里通常会是一个完整的文档、代码库、或者用户手册。缓存功能可以显著提高处理长文档时的响应速度和成本效率。这个功能特别适用于需要反复引用同一份大型参考资料的对话场景。"
run_test "Claude 提示缓存 - 非流式" \
    "curl -s -X POST $API_URL/api/v1/messages \
      -H 'content-type: application/json' \
      -H 'x-api-key: $ANTHROPIC_API_KEY' \
      -H 'anthropic-version: 2023-06-01' \
      -d '{
        \"model\": \"claude-3-opus-20240229\",
        \"max_tokens\": 1024,
        \"system\": [
          {
            \"type\": \"text\",
            \"text\": \"你是一个文档分析助手。你的任务是根据提供的文档回答问题。\\n\\n文档内容如下：\\n\\n\"
          },
          {
            \"type\": \"text\",
            \"text\": \"$LONG_DOCUMENT_CONTENT\",
            \"cache_control\": {\"type\": \"ephemeral\"}
          }
        ],
        \"messages\": [
          {
            \"role\": \"user\",
            \"content\": \"请总结文档的主要观点。\"
          }
        ],
        \"stream\": false
      }' | jq ."

# === 模型列表获取测试 ===
run_test "获取模型列表" \
    "curl -s $API_URL/v1/models \
      -H 'Authorization: Bearer $OPENAI_API_KEY' | jq ."

echo "==============================================="
echo "校准后的核心兼容性测试用例执行完毕。"
echo "==============================================="
```

### 测试执行建议

#### 1. 分阶段测试
``bash
# 第一阶段：基础连通性测试
# 只执行健康检查和简单的文本对话测试

# 第二阶段：核心功能测试  
# 执行OpenAI和Claude的基本功能测试

# 第三阶段：高级功能测试
# 执行thinking、tools、cache_control等高级功能测试
```

#### 2. 错误处理验证
对于高级功能（特别是thinking、tools、cache_control），需要特别关注：
- 如果功能未实现，是否返回适当的错误信息
- 如果功能部分实现，响应格式是否正确
- 系统是否能够优雅地处理不支持的参数

#### 3. 响应格式验证
重点验证：
- Claude响应是否符合标准Claude API格式
- OpenAI响应是否符合标准OpenAI API格式
- 流式响应的SSE格式是否正确
- 错误响应的格式是否标准化

## 完整需求梳理与本地服务验证方案

### 需求梳理总览

根据您的要求，需要完善test.sh测试脚本，并建立完整的本地测试流程来确保服务的完善性和可用性。

#### 核心需求
1. **完善test.sh脚本**：增加全面的测试用例覆盖
2. **本地服务启动**：建立标准化的服务启动流程
3. **服务验证**：通过测试确保服务完善可用
4. **问题定位**：当测试失败时能快速定位问题

#### 测试覆盖范围
1. **基础功能测试**：健康检查、模型列表、基础对话
2. **协议兼容性测试**：OpenAI/Claude协议完整支持
3. **消息过滤测试**：无效消息的正确处理
4. **客户端兼容性测试**：Cherry Studio等真实客户端支持
5. **高级功能测试**：thinking、tools、cache_control等
6. **错误处理测试**：各种异常情况的稳定处理

### 完整的本地验证方案

#### 1. 一键测试脚本 (quick_test.sh)
```
#!/bin/bash
echo "🚀 开始完整的服务测试流程"

# 检查环境
command -v docker >/dev/null || { echo "❌ Docker未安装"; exit 1; }
command -v curl >/dev/null || { echo "❌ curl未安装"; exit 1; }

# 清理旧环境
docker stop de-test 2>/dev/null && docker rm de-test 2>/dev/null

# 启动服务
echo "🚀 启动服务..."
docker run -d --name de-test -p 7860:7860 -m 2g -e DEBUG=true ghcr.io/hhhaiai/de:latest
sleep 10

# 健康检查
for i in {1..5}; do
    if curl -s http://localhost:7860/health | grep -q "working"; then
        echo "✅ 服务健康检查通过"
        break
    fi
    if [ $i -eq 5 ]; then
        echo "❌ 服务健康检查失败"
        docker logs de-test | tail -20
        exit 1
    fi
    sleep 2
done

# 执行测试
echo "🧪 执行测试套件..."
bash test.sh
TEST_RESULT=$?

# 清理环境
docker stop de-test && docker rm de-test

if [ $TEST_RESULT -eq 0 ]; then
    echo "🎉 所有测试通过！服务工作正常。"
else
    echo "❌ 测试存在失败，请查看输出进行问题诊断。"
fi
exit $TEST_RESULT
```

#### 2. 增强的test.sh版本（精简版）
```
#!/bin/bash
# 增强的API测试脚本

API_URL="http://localhost:7860"
OPENAI_API_KEY="${OPENAI_API_KEY:-YOUR_OPENAI_API_KEY}"
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-YOUR_ANTHROPIC_API_KEY}"

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

log_info() { echo -e "\033[32m[INFO]\033[0m $1"; }
log_error() { echo -e "\033[31m[ERROR]\033[0m $1"; }

run_test_enhanced() {
    local test_name="$1"
    local test_command="$2"
    local expected_pattern="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo "======== 测试 $test_name ($TOTAL_TESTS) ========"
    
    local result
    if [[ "$test_command" =~ "stream.*true" ]]; then
        result=$(timeout 10s bash -c "$test_command" 2>&1 | head -10)
    else
        result=$(timeout 10s bash -c "$test_command" 2>&1)
    fi
    
    echo "$result"
    
    if [[ -n "$expected_pattern" ]] && echo "$result" | grep -q "$expected_pattern"; then
        log_info "✅ 测试通过"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    elif [[ -z "$expected_pattern" ]] && ! echo "$result" | grep -qiE "error|fail|invalid"; then
        log_info "✅ 测试通过"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        log_error "❌ 测试失败"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    echo
}

# 基础功能测试
run_test_enhanced "健康检查" "curl -s $API_URL/health" "working"
run_test_enhanced "模型列表" "curl -s $API_URL/v1/models -H 'Authorization: Bearer $OPENAI_API_KEY'" "data"
run_test_enhanced "OpenAI基础对话" "curl -s -X POST $API_URL/v1/chat/completions -H 'Content-Type: application/json' -H 'Authorization: Bearer $OPENAI_API_KEY' -d '{\"model\": \"auto\", \"messages\": [{\"role\": \"user\", \"content\": \"你好\"}], \"stream\": false}'" "choices"
run_test_enhanced "Claude基础对话" "curl -s -X POST $API_URL/api/v1/messages -H 'Content-Type: application/json' -H 'x-api-key: $ANTHROPIC_API_KEY' -H 'anthropic-version: 2023-06-01' -d '{\"model\": \"claude-3-haiku-20240307\", \"max_tokens\": 1000, \"messages\": [{\"role\": \"user\", \"content\": \"你好\"}], \"stream\": false}'" "content"

# 增强功能测试
run_test_enhanced "消息过滤" "curl -s -X POST $API_URL/v1/chat/completions -H 'Content-Type: application/json' -H 'Authorization: Bearer $OPENAI_API_KEY' -d '{\"model\": \"auto\", \"messages\": [{\"content\": \"无role消息\"}, {\"role\": \"user\", \"content\": \"有效消息\"}], \"stream\": false}'"
run_test_enhanced "Claude thinking" "curl -s -X POST $API_URL/api/v1/messages -H 'Content-Type: application/json' -H 'x-api-key: $ANTHROPIC_API_KEY' -H 'anthropic-version: 2023-06-01' -d '{\"model\": \"claude-3-sonnet-20240229\", \"max_tokens\": 1000, \"thinking\": {\"type\": \"enabled\"}, \"messages\": [{\"role\": \"user\", \"content\": \"简单思考\"}], \"stream\": false}'"
run_test_enhanced "Cherry Studio兼容" "curl -s $API_URL/v1/chat/completions -H 'User-Agent: CherryStudio/1.5.7' -H 'authorization: Bearer $OPENAI_API_KEY' -H 'content-type: application/json' -d '{\"model\":\"auto\", \"messages\":[{\"role\":\"user\",\"content\":\"你好\"}], \"stream\":false}'"

# 流式响应测试
run_test_enhanced "OpenAI流式" "curl -s -X POST $API_URL/v1/chat/completions -H 'Content-Type: application/json' -H 'Authorization: Bearer $OPENAI_API_KEY' -d '{\"model\": \"auto\", \"messages\": [{\"role\": \"user\", \"content\": \"测试流式\"}], \"stream\": true}'" "data:"
run_test_enhanced "Claude流式" "curl -s -X POST $API_URL/api/v1/messages -H 'Content-Type: application/json' -H 'x-api-key: $ANTHROPIC_API_KEY' -H 'anthropic-version: 2023-06-01' -d '{\"model\": \"claude-3-haiku-20240307\", \"max_tokens\": 500, \"stream\": true, \"messages\": [{\"role\": \"user\", \"content\": \"测试\"}]}'" "event:"

# 测试结果统计
echo "========== 测试结果 =========="
echo "总测试: $TOTAL_TESTS | 通过: $PASSED_TESTS | 失败: $FAILED_TESTS"
if [ $TOTAL_TESTS -gt 0 ]; then
    echo "成功率: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"
fi

[ $FAILED_TESTS -eq 0 ] && log_info "所有测试通过！" || log_error "存在失败测试"
exit $FAILED_TESTS