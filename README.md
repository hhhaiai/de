# DD

## 环境变量

- **REPLACE_CHAT**: 强制替换目标地址,/开头
- **PREFIX_CHAT**:   支持多个,每个都增加前缀，/开头 
- **APPEND_CHAT**:  增加更多的接口, /开头
- **DEBUG**:  是否debug默认，是否可以查看日志
- **TOKEN**:  是否限制token才能访问，设置则限制，不设置则不限制

## down and use

Install from the command line
``` bash
$ docker pull ghcr.io/hhhaiai/de:latest
$ docker run -d \
  --name de \
  --restart always \
  -p 7860:7860 \
  -m 2g \
  -e DEBUG=false \
  ghcr.io/hhhaiai/de:latest
```
Use as base image in Dockerfile:
``` dockerfile
FROM ghcr.io/hhhaiai/de:latest
```

build test use code
``` bash
$ docker build --no-cache --compress -t de .
$ docker run -p 7860:7860 -m 2g -e DEBUG=false de
```


call demo

```

curl http://localhost:7860/v1/models
curl http://localhost:7860/api/v1/models

curl -X POST http://localhost:7860/api/v1/chat/completions \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "你是什么模型?"}],
    "stream":true
  }'

curl -X POST http://localhost:7860/api/v1/chat/completions \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "你是什么模型?"}],
    "stream":false
  }'

```