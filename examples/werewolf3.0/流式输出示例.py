import json
import requests

url = "https://www.dmxapi.cn/v1/chat/completions"

payload = {
    "model": "gpt-4o-mini",  # 模型名称
    "stream": True,  # 流式输出True开启
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "周树人和鲁迅是兄弟吗？"},
    ],
}
headers = {
    "Accept": "application/json",
    "Authorization": "sk-****************************************************",  # 这里放你的 DMXAPI key
    "User-Agent": "DMXAPI/1.0.0 (https://www.dmxapi.cn)",
    "Content-Type": "application/json",
}

response = requests.post(url, headers=headers, json=payload, stream=True)

buffer = ""
for chunk in response.iter_content(chunk_size=None):
    if chunk:
        buffer += chunk.decode("utf-8")
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            if line.strip() == "":
                continue
            if line.startswith("data: "):
                data_line = line[len("data: ") :].strip()
                if data_line == "[DONE]":
                    break
                else:
                    try:
                        data = json.loads(data_line)
                        delta = data["choices"][0]["delta"]
                        content = delta.get("content", "")
                        print(content, end="", flush=True)
                    except json.JSONDecodeError:
                        # 如果JSON解析失败，可能是数据不完整，继续累积buffer
                        buffer = line + "\n" + buffer
                        break
