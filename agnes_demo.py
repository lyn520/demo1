"""
Agnes AI 免费模型 (agnes-2.0-flash) 调用示例
文档：https://agnes-ai.com/doc/agnes-20-flash
"""
import json
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

# Windows 控制台默认 GBK，重新配置为 UTF-8 以避免中文乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

API_URL = "https://apihub.agnes-ai.com/v1/chat/completions"
MODEL = "agnes-2.0-flash"
API_KEY = os.getenv("AGNES_API_KEY")

if not API_KEY:
    sys.exit("请先设置环境变量 AGNES_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def chat(user_message: str, system_prompt: str = "You are a helpful AI assistant.") -> str:
    """基础聊天补全。"""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.7,
        "max_tokens": 1024,
    }
    resp = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def chat_stream(user_message: str) -> None:
    """流式输出（SSE）。"""
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": user_message}],
        "temperature": 0.7,
        "max_tokens": 1024,
        "stream": True,
    }
    with requests.post(API_URL, headers=HEADERS, json=payload, stream=True, timeout=60) as resp:
        if resp.status_code >= 400:
            resp.encoding = "utf-8"
            print(f"\n[请求失败] HTTP {resp.status_code}: {resp.text}")
            resp.raise_for_status()
        resp.encoding = "utf-8"
        for raw in resp.iter_lines(decode_unicode=True):
            if not raw or not raw.startswith("data:"):
                continue
            chunk = raw[5:].strip()
            if chunk == "[DONE]":
                break
            try:
                obj = json.loads(chunk)
            except json.JSONDecodeError:
                continue
            choices = obj.get("choices")
            if not choices:
                continue
            delta = choices[0].get("delta", {}).get("content")
            if delta:
                print(delta, end="", flush=True)
        print()


def chat_with_image(image_url: str, question: str) -> str:
    """图像理解：传入公开可访问的图片 URL。

    注意：根据官方文档，agnes-2.0-flash 的图像输入仅支持「公开可访问的图片 URL」，
    不支持 base64 / Data URI；且图片不能有登录验证或防盗链（hotlink protection）。
    """
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
    }
    resp = requests.post(API_URL, headers=HEADERS, json=payload, timeout=120)
    if resp.status_code >= 400:
        resp.encoding = "utf-8"
        print(f"\n[请求失败] HTTP {resp.status_code}: {resp.text}")
        resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


if __name__ == "__main__":
    # print("=== 1. 基础对话 ===")
    # print(chat("用一句话解释什么是自主智能体（autonomous agent）。"))

    # print("\n=== 2. 流式输出 ===")
    # chat_stream("写一段 50 字的 AI 助手 App 产品介绍。")

    print("\n=== 3. 图像理解 ===")
    try:
        print(chat_with_image(
            "https://www.gstatic.com/webp/gallery/1.jpg",
            "请描述这张图片的主要内容。",
        ))
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        print(f"图像理解请求失败（HTTP {status}）。"
              "该免费模型可能不支持图像输入，或上游服务暂时不可用。")