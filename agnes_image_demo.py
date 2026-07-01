"""
Agnes Image 2.1 Flash 图像生成示例（文生图 / 图生图）
文档：https://agnes-ai.com/doc/agnes-image-21-flash
"""
import base64
import os
import sys

import requests

# Windows 控制台默认 GBK，重新配置为 UTF-8 以避免中文乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

API_URL = "https://apihub.agnes-ai.com/v1/images/generations"
MODEL = "agnes-image-2.1-flash"
API_KEY = os.getenv("AGNES_API_KEY")

if not API_KEY:
    sys.exit("请先设置环境变量 AGNES_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def _post(payload: dict) -> dict:
    """发送请求，失败时打印服务端返回内容。"""
    resp = requests.post(API_URL, headers=HEADERS, json=payload, timeout=360)
    if resp.status_code >= 400:
        resp.encoding = "utf-8"
        print(f"\n[请求失败] HTTP {resp.status_code}: {resp.text}")
        resp.raise_for_status()
    return resp.json()


def _save_b64(b64: str, filename: str) -> None:
    """把 base64 图片保存到文件。"""
    with open(filename, "wb") as f:
        f.write(base64.b64decode(b64))
    print(f"已保存图片：{filename}")


def _save_url(url: str, filename: str) -> None:
    """下载图片 URL 并保存到文件。"""
    img = requests.get(url, timeout=120)
    img.raise_for_status()
    with open(filename, "wb") as f:
        f.write(img.content)
    print(f"已保存图片：{filename}")


def _save_item(item: dict, filename: str) -> None:
    """根据返回项保存图片：优先 base64，否则回退到下载 URL。"""
    b64 = item.get("b64_json")
    url = item.get("url")
    if b64:
        _save_b64(b64, filename)
    elif url:
        _save_url(url, filename)
    else:
        raise ValueError("返回结果既无 b64_json 也无 url")


def text_to_image_url(prompt: str, size: str = "1024x768") -> str:
    """文生图，返回图片 URL。"""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "size": size,
        "extra_body": {"response_format": "url"},
    }
    data = _post(payload)
    return data["data"][0]["url"]


def text_to_image_file(prompt: str, filename: str, size: str = "1024x768") -> None:
    """文生图，返回 base64 并保存为本地文件。"""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "size": size,
        "return_base64": True,
    }
    data = _post(payload)
    _save_item(data["data"][0], filename)


def image_to_image_url(prompt: str, input_image: str, size: str = "1024x768") -> str:
    """图生图：基于输入图片（公开 URL 或 Data URI）进行编辑，返回图片 URL。"""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "size": size,
        "extra_body": {
            "image": [input_image],
            "response_format": "url",
        },
    }
    data = _post(payload)
    return data["data"][0]["url"]


if __name__ == "__main__":
    print("=== 1. 文生图（返回 URL）===")
    url = text_to_image_url(
        "A luminous floating city above a misty canyon at sunrise, "
        "cinematic realism, wide-angle composition, rich architectural details, "
        "soft golden light, high visual density"
    )
    print("图片 URL：", url)

    print("\n=== 2. 文生图（保存为本地文件）===")
    text_to_image_file(
        "A clean product photo of a glass cube on a white studio background, "
        "soft shadows, high detail",
        "output_image.png",
    )

    print("\n=== 3. 图生图（基于上一步生成的图片进行风格转换）===")
    edited = image_to_image_url(
        "Transform the scene into a rain-soaked cyberpunk night with neon "
        "reflections while preserving the original composition",
        url,
    )
    print("编辑后图片 URL：", edited)
