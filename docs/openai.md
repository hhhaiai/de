# OpenAI API 接口简明参考

本文档提供与 OpenAI 兼容的常用 API 接口的简明参考，涵盖模型列表获取、文本补全、多模态对话及图像生成功能。

---

#### **1. Models API（模型列表获取）**

获取当前可用的模型列表及其基本信息。

**Endpoint:** `GET /v1/models`

**说明:** 此接口无需请求体，直接调用即可返回所有可用模型的列表，包括模型ID、所属组织、权限等信息。

**请求示例（cURL）：**

```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**响应格式：**

```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4-turbo",
      "object": "model",
      "created": 1687882411,
      "owned_by": "openai",
      "permission": [...],
      "root": "gpt-4-turbo",
      "parent": null
    },
    {
      "id": "gpt-4",
      "object": "model",
      "created": 1687882410,
      "owned_by": "openai",
      "permission": [...],
      "root": "gpt-4",
      "parent": null
    },
    {
      "id": "dall-e-3",
      "object": "model",
      "created": 1698939181,
      "owned_by": "openai",
      "permission": [...],
      "root": "dall-e-3",
      "parent": null
    }
    // 更多模型...
  ]
}
```

---

#### **2. Chat Completions API（文本对话）**

该接口用于与纯文本模型（如 `gpt-3.5-turbo`、`gpt-4` 系列）进行交互。

**Endpoint:** `POST /v1/chat/completions`

**说明:** 通过发送一个消息列表（可包含系统指令、用户查询及历史对话），从模型获取一条补全回复。

**请求示例（cURL）：**

```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4-turbo",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "Hello! What can you do?"
      }
    ]
  }'
```

**关键参数：**

*   **`model`** (string, required): 指定需使用的模型标识符，例如 `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`。
*   **`messages`** (array, required): 构成对话上下文的消息对象数组。每个对象必须包含 `role` (取值为 `system`, `user`, 或 `assistant`) 和 `content` (文本内容)。
*   **`stream`** (boolean, optional): 设置为 `true` 以启用流式传输输出。默认为 `false`。

**响应格式（非流式）：**

```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-4-turbo",
  "system_fingerprint": "fp_44709d6fcb",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! I can answer questions, generate text, assist with analysis, and more."
      },
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 34,
    "total_tokens": 59
  }
}
```

---

#### **3. Chat Completions API（多模态对话）**

用于与支持视觉输入的模型（如 `gpt-4-turbo`、`gpt-4o`）进行对话，可同时处理图像和文本信息。

**Endpoint:** `POST /v1/chat/completions`

**说明:** 此端点与文本对话接口一致，但其 `user` 角色的 `content` 字段可接受一个由文本和图像对象组成的数组，以实现多模态输入。

**请求示例（包含图片 URL）：**

```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4-turbo",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "What is in this image?"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "https://example.com/image.jpg"
            }
          }
        ]
      }
    ],
    "max_tokens": 300
  }'
```

**关键参数：**

*   **`model`** (string, required): 支持多模态能力的模型 ID，如 `gpt-4-turbo`, `gpt-4o`。
*   **`messages`** (array, required): `content` 字段可定义为字符串（纯文本）或消息内容对象数组。
    *   **文本对象**: `{"type": "text", "text": "Your text here"}`
    *   **图像对象**: `{"type": "image_url", "image_url": {"url": "image_url_here"}}` (URL 支持公网可访问的图片链接或 `data:image/<format>;base64,<data>` 格式的 Base64 编码字符串)。

**提示:** 多模态功能为模型特有特性，请确保所选模型具备图像理解能力。

**响应格式:** 与文本对话接口的响应结构一致。

---

#### **4. Images Generations API（图像生成）**

根据给定的文本提示（Prompt）生成图像。

**Endpoint:** `POST /v1/images/generations`

**说明:** 提交一段文本描述，模型将生成一张或多张与之匹配的图像。

**请求示例：**

```bash
curl https://api.openai.com/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "dall-e-3",
    "prompt": "A cute baby sea otter wearing a beret",
    "n": 1,
    "size": "1024x1024",
    "quality": "standard"
  }'
```

**关键参数：**

*   **`model`** (string, required): 图像生成模型 ID，如 `dall-e-2`, `dall-e-3`。
*   **`prompt`** (string, required): 描述期望生成图像的文本。
*   **`n`** (integer, optional): 生成图像的数量。
    *   `dall-e-3`: 仅支持生成 1 张图像。
    *   `dall-e-2`: 支持生成 1 至 10 张图像。
*   **`size`** (string, optional): 生成图像的尺寸规格。
    *   `dall-e-2`: `256x256`, `512x512`, `1024x1024`。
    *   `dall-e-3`: `1024x1024`, `1792x1024`, `1024x1792`。
*   **`quality`** (string, optional, 仅 `dall-e-3` 支持): 图像质量，可选 `standard` (默认) 或 `hd` (细节更丰富，生成时间更长)。
*   **`style`** (string, optional, 仅 `dall-e-3` 支持): 生成风格，可选 `vivid` (默认，色彩鲜艳、超现实) 或 `natural` (风格更逼真、自然)。
*   **`response_format`** (string, optional): 响应格式，可选 `url` (默认，返回临时可访问的 URL) 或 `b64_json` (返回 Base64 编码的图像字符串)。

**响应格式：**

```json
{
  "created": 1589478378,
  "data": [
    {
      "url": "https://example.com/image.jpg",
      "revised_prompt": "A photorealistic depiction of a baby sea otter..."
    }
  ]
}
```
*(若 `response_format` 为 `b64_json`，则 `url` 字段将由 `b64_json` 字段替代)*

---

**注意:** 所有请求均需在 `Header` 中包含有效的 `Authorization: Bearer $OPENAI_API_KEY`。

**版本:** 1.1
**最后更新:** 2024-08-23
