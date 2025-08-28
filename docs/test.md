curl 'http://0.0.0.0:7860/api/v1/chat/completions' \
  -H 'accept: application/json' \
  -H 'accept-language: zh-CN' \
  -H 'authorization: Bearer hf' \
  -H 'content-type: application/json' \
  -H 'http-referer: https://cherry-ai.com' \
  -H 'priority: u=1, i' \
  -H 'sec-ch-ua: "Not)A;Brand";v="8", "Chromium";v="138"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: cross-site' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) CherryStudio/1.5.7 Chrome/138.0.7204.100 Electron/37.2.3 Safari/537.36' \
  -H 'x-api-key: hf' \
  -H 'x-stainless-retry-count: 0' \
  -H 'x-stainless-timeout: 600' \
  -H 'x-title: Cherry Studio' \
  --data-raw $'{"model":"deepseek-reasoner","messages":[{"role":"user","content":"1"},{"role":"assistant","content":"It looks like you\'ve entered \\"1\\" as your input. Could you please clarify what you\'d like help with? For example, are you:\\n\\n- Looking for information related to the number 1?\\n- Asking a question that starts with \\"1\\"?\\n- Referring to a specific topic or problem?\\n\\nLet me know how I can assist you\u0021"},{"role":"user","content":"hi"},{"role":"assistant","content":""},{"role":"user","content":"nihao"}],"temperature":0.05,"top_p":0.08,"stream":true,"stream_options":{"include_usage":true}}'



$   curl 'http://0.0.0.0:7860/api/v1/chat/completions' \
>   -H 'accept: application/json' \
>   -H 'accept-language: zh-CN' \
>   -H 'authorization: Bearer hf' \
>   -H 'content-type: application/json' \
>   -H 'http-referer: https://cherry-ai.com' \
>   -H 'priority: u=1, i' \
>   -H 'sec-ch-ua: "Not)A;Brand";v="8", "Chromium";v="138"' \
>   -H 'sec-ch-ua-mobile: ?0' \
>   -H 'sec-ch-ua-platform: "macOS"' \
>   -H 'sec-fetch-dest: empty' \
>   -H 'sec-fetch-mode: cors' \
>   -H 'sec-fetch-site: cross-site' \
>   -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) CherryStudio/1.5.7 Chrome/138.0.7204.100 Electron/37.2.3 Safari/537.36' \
>   -H 'x-api-key: hf' \
>   -H 'x-stainless-retry-count: 0' \
>   -H 'x-stainless-timeout: 600' \
>   -H 'x-title: Cherry Studio' \
>   --data-raw '{"model":"deepseek-reasoner","messages":[{"role":"user","content":"hi"}],"temperature":0.05,"top_p":0.08,"stream":true,"stream_options":{"include_usage":true}}'
data: {"id": "eeafb517-4b59-4773-a740-31565cd7c220", "object": "chat.completion.chunk", "created": 1756273400, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": ""}, "logprobs": null, "finish_reason": null}]}
data: {"id": "eeafb517-4b59-4773-a740-31565cd7c220", "object": "chat.completion.chunk", "created": 1756273400, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "Hello"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "eeafb517-4b59-4773-a740-31565cd7c220", "object": "chat.completion.chunk", "created": 1756273400, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "!"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "eeafb517-4b59-4773-a740-31565cd7c220", "object": "chat.completion.chunk", "created": 1756273400, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": " How"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "eeafb517-4b59-4773-a740-31565cd7c220", "object": "chat.completion.chunk", "created": 1756273400, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": " can"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "eeafb517-4b59-4773-a740-31565cd7c220", "object": "chat.completion.chunk", "created": 1756273400, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": " I"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "eeafb517-4b59-4773-a740-31565cd7c220", "object": "chat.completion.chunk", "created": 1756273400, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": " help"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "eeafb517-4b59-4773-a740-31565cd7c220", "object": "chat.completion.chunk", "created": 1756273400, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": " you"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "eeafb517-4b59-4773-a740-31565cd7c220", "object": "chat.completion.chunk", "created": 1756273400, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": " today"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "eeafb517-4b59-4773-a740-31565cd7c220", "object": "chat.completion.chunk", "created": 1756273400, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": "?"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "eeafb517-4b59-4773-a740-31565cd7c220", "object": "chat.completion.chunk", "created": 1756273400, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": " \ud83d\ude0a"}, "logprobs": null, "finish_reason": null}]}
data: {"id": "eeafb517-4b59-4773-a740-31565cd7c220", "object": "chat.completion.chunk", "created": 1756273400, "model": "deepseek-chat", "choices": [{"index": 0, "delta": {"content": ""}, "logprobs": null, "finish_reason": "stop"}]}
data: [DONE]


