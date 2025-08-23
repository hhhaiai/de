
## 1. 获取模型接口

``` bash
$ curl http://localhost:7860/api/v1/models

{"object":"list","data":[{"id":"deepseek-chat","object":"model","model":"deepseek-chat","created":1755952008000,"owned_by":"deepseek","name":"DeepSeek V3.1","description":"Suitable for reasoning and writing","support":"text","tip":"DeepSeek V3.1"},{"id":"doubao-seed-1-6-250615","object":"model","model":"doubao-seed-1-6-250615","created":1755952008000,"owned_by":"doubao","name":"DouBao 1.6 (TikTok)","description":"Multimodal graphics and text, suitable for daily tasks","support":"image","tip":"DouBao 1.6 (TikTok)"},{"id":"qwen3-235b-a22b","object":"model","model":"qwen3-235b-a22b","created":1755952008000,"owned_by":"qwen3","name":"Qwen3 (Ali Cloud)","description":"Strong language skills","support":"image","tip":"Qwen3 (Ali Cloud)"},{"id":"qwen3-235b-a22b","object":"model","model":"qwen3-235b-a22b","created":1755952008000,"owned_by":"qwen3","name":"Qwen3 Thinking (Ali Cloud)","description":"Enhanced reasoning, suitable for complex tasks","support":"image","tip":"Qwen3 Thinking (Ali Cloud)"},{"id":"gpt-5-mini","object":"model","model":"gpt-5-mini","created":1755952008000,"owned_by":"gpt","name":"GPT-5 mini (OpenAI)","description":"Lightweight general-purpose model with fast response speed","support":"image","tip":"GPT-5 mini (OpenAI)"},{"id":"gpt-4o","object":"model","model":"gpt-4o","created":1755952008000,"owned_by":"gpt","name":"GPT-4o (OpenAI)","description":"Multimodal graphics and text, suitable for most tasks","support":"image","tip":"GPT-4o (OpenAI)"},{"id":"deepseek-reasoner","object":"model","model":"deepseek-reasoner","created":1755952008000,"owned_by":"deepseek","name":"DeepSeek R1","description":"Strong writing and coding skills","support":"text","tip":"DeepSeek R1"},{"id":"gemini-2.5-flash-preview-05-20","object":"model","model":"gemini-2.5-flash-preview-05-20","created":1755952008000,"owned_by":"gemini","name":"Gemini 2.5 Flash (Google)","description":"Multimodal graphics and text, quick response","support":"text","tip":"Gemini 2.5 Flash (Google)"},{"id":"grok-4-0709","object":"model","model":"grok-4-0709","created":1755952008000,"owned_by":"grok","name":"Grok 4 (Elon Musk)","description":"Expert in Q&A, lively expression style","support":"image","tip":"Grok 4 (Elon Musk)"},{"id":"doubao-seed-1-6-thinking-250615","object":"model","model":"doubao-seed-1-6-thinking-250615","created":1755952008000,"owned_by":"doubao","name":"DouBao 1.6 Thinking (TikTok)","description":"Multimodal graphics and text, reasoning enhancement","support":"image","tip":"DouBao 1.6 Thinking (TikTok)"},{"id":"o3","object":"model","model":"o3","created":1755952008000,"owned_by":"unknown","name":"GPT o3 (OpenAI)","description":"Using advanced reasoning","support":"image","tip":"GPT o3 (OpenAI)"},{"id":"o4-mini","object":"model","model":"o4-mini","created":1755952008000,"owned_by":"o4","name":"GPT o4-mini high (OpenAI)","description":"Using advanced reasoning","support":"image","tip":"GPT o4-mini high (OpenAI)"},{"id":"gpt-4.1","object":"model","model":"gpt-4.1","created":1755952008000,"owned_by":"gpt","name":"GPT-4.1 (OpenAI)","description":"Good at fast coding and analysis","support":"image","tip":"GPT-4.1 (OpenAI)"},{"id":"gpt-5","object":"model","model":"gpt-5","created":1755952008000,"owned_by":"gpt","name":"GPT-5 (OpenAI)","description":"Good at fast coding and analysis","support":"image","tip":"GPT-5 (OpenAI)"},{"id":"claude-opus-4-20250514","object":"model","model":"claude-opus-4-20250514","created":1755952008000,"owned_by":"claude","name":"Claude 4 Opus (Anthropic)","description":"Strongest in coding, suitable for complex tasks","support":"text","tip":"Claude 4 Opus (Anthropic)"},{"id":"claude-opus-4-20250514","object":"model","model":"claude-opus-4-20250514","created":1755952008000,"owned_by":"claude","name":"Claude 4 Opus Thinking (Anthropic)","description":"Deep reasoning enhancement","support":"text","tip":"Claude 4 Opus Thinking (Anthropic)"},{"id":"grok-3-mini","object":"model","model":"grok-3-mini","created":1755952008000,"owned_by":"grok","name":"Grok 3 Thinking (Elon Musk)","description":"Strengthened logical reasoning and knowledge expression","support":"image","tip":"Grok 3 Thinking (Elon Musk)"},{"id":"gemini-2.5-pro","object":"model","model":"gemini-2.5-pro","created":1755952008000,"owned_by":"gemini","name":"Gemini 2.5 Pro (Google)","description":"Powerful multimodal capabilities, proficient in graphics, text, and code","support":"text","tip":"Gemini 2.5 Pro (Google)"}],"version":"0.1.125","provider":"DeGPT","name":"DeGPT","default_locale":"en-US","status":true,"time":20250822}
```

## 2. openai 文本对话接口

``` bash

curl -X POST http://localhost:7860/api/v1/chat/completions \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "你是什么模型?"}],
    "stream":true
  }'
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": ""}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u6211\u662f"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": " **"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "Deep"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "Se"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "ek"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "-V"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "3"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "**"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\uff0c"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u7531"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": " **"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u6df1\u5ea6"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u6c42"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u7d22"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\uff08"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "Deep"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "Se"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "ek"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\uff09"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "**"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": " "}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u516c\u53f8"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u5f00\u53d1\u7684"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": " **"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u5927"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u8bed\u8a00"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u6a21\u578b"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "**"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u3002"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u6211\u7684"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u77e5\u8bc6"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u622a\u6b62"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u65e5\u671f"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u662f"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": " **"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "202"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "4"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u5e74"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "7"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u6708"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "**"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\uff0c"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u53ef\u4ee5"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u5904\u7406"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": " **"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "128"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "K"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": " "}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u4e0a\u4e0b\u6587"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "**"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\uff0c"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u5e76\u4e14"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u652f\u6301"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": " **"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u6587\u672c"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u3001"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u6587\u6863"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\uff08"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u5982"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "PDF"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u3001"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "Word"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u3001"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "Excel"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u3001"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "PPT"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u7b49"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\uff09"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u7684"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u89e3\u6790"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u548c\u5206\u6790"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "**"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u3002"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "  \n\n"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u5982\u679c\u4f60"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u6709\u4efb\u4f55"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u95ee\u9898"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u6216"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u9700\u8981"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u5e2e\u52a9"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\uff0c"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u5c3d\u7ba1"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u95ee\u6211"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\u54e6"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\uff01"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "\ud83d\ude0a"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "23c1e5ec-0e48-40be-8803-4b2701c1b4b0", "object": "chat.completion.chunk", "created": 1755954793, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": ""}, "logprobs": null, "finish_reason": "stop"}]}
data: [DONE]

####################
curl -X POST http://localhost:7860/api/v1/chat/completions \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "你是什么模型?"}],
    "stream":false
  }'

{"id":"chatcmpl-hfkw656400","object":"chat.completion","created":1755954836,"model":"deepseek-chat","usage":{"prompt_tokens":0,"completion_tokens":131,"total_tokens":131},"choices":[{"message":{"role":"assistant","content":"我是 **DeepSeek-V3**，由 **深度求索（DeepSeek）** 公司开发的 **大语言模型**。我的知识截止到 **2024年7月**，可以处理 **128K 超长上下文**，并且支持 **文本、文档（如PDF、Word、Excel、PPT等）的解析和分析**。  \n\n如果你有任何问题，不论是学习、编程、写作，还是生活相关，都可以问我！😊"},"finish_reason":"stop","index":0}]}

```

## 3. claude 文本对话接口


``` bash
curl http://localhost:7860/api/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-opus-4-20250514",
    "max_tokens": 1000,
    "messages": [
      {
        "role": "user",
        "content": "你是什么模型?"
      }
    ]
  }'


{"id":"chatcmpl-jzis922349","type":"message","role":"assistant","content":[{"type":"text","text":"我是Claude，一个由Anthropic公司创建的AI助手。我是基于大型语言模型训练而成的，旨在通过自然对话的方式提供帮助。我可以协助处理各种任务，包括回答问题、写作、分析、编程、翻译等。有什么我可以帮助您的吗？"}],"model":"claude-opus-4-20250514","stop_reason":"end_turn","stop_sequence":null,"usage":{"input_tokens":0,"output_tokens":103}}

```
