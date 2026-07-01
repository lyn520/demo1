"""
Agnes-Video-V2.0 视频生成示例（文生视频 / 图生视频，异步任务）
文档：https://agnes-ai.com/doc/agnes-video-v20

工作流程：先创建视频任务拿到 video_id，再轮询查询结果直到 completed。
"""
import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()

# Windows 控制台默认 GBK，重新配置为 UTF-8 以避免中文乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

CREATE_URL = "https://apihub.agnes-ai.com/v1/videos"
RESULT_URL = "https://apihub.agnes-ai.com/agnesapi"
MODEL = "agnes-video-v2.0"
API_KEY = os.getenv("AGNES_API_KEY")

if not API_KEY:
    sys.exit("请先设置环境变量 AGNES_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def create_video_task(payload: dict) -> str:
    """创建视频生成任务，返回 video_id。"""
    resp = requests.post(CREATE_URL, headers=HEADERS, json=payload, timeout=60)
    if resp.status_code >= 400:
        resp.encoding = "utf-8"
        print(f"\n[创建任务失败] HTTP {resp.status_code}: {resp.text}")
        resp.raise_for_status()
    data = resp.json()
    print(f"任务已创建：video_id={data.get('video_id')} status={data.get('status')}")
    return data["video_id"]


def wait_for_video(video_id: str, interval: int = 10, max_wait: int = 600) -> str:
    """轮询查询视频结果，完成后返回视频 URL。"""
    deadline = time.time() + max_wait
    while time.time() < deadline:
        resp = requests.get(
            RESULT_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            params={"video_id": video_id, "model_name": MODEL},
            timeout=60,
        )
        if resp.status_code >= 400:
            resp.encoding = "utf-8"
            print(f"\n[查询失败] HTTP {resp.status_code}: {resp.text}")
            resp.raise_for_status()
        data = resp.json()
        status = data.get("status")
        progress = data.get("progress", 0)
        print(f"  状态：{status}  进度：{progress}%")
        if status == "completed":
            return data["remixed_from_video_id"]
        if status == "failed":
            raise RuntimeError(f"视频生成失败：{data.get('error')}")
        time.sleep(interval)
    raise TimeoutError("等待视频生成超时")


def text_to_video(prompt: str) -> str:
    """文生视频。"""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "height": 768,
        "width": 1152,
        "num_frames": 121,   # 约 5 秒，须 ≤441 且满足 8n+1
        "frame_rate": 24,
    }
    video_id = create_video_task(payload)
    return wait_for_video(video_id)


def image_to_video(prompt: str, image_url: str) -> str:
    """图生视频：让一张静态图片动起来。"""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "image": image_url,
        "num_frames": 121,
        "frame_rate": 24,
    }
    video_id = create_video_task(payload)
    return wait_for_video(video_id)


if __name__ == "__main__":
    # print("=== 1. 文生视频 ===")
    # url = text_to_video(
    #     "A cinematic shot of a cat walking on the beach at sunset, "
    #     "soft ocean waves, warm golden lighting, realistic motion"
    # )
    # print("视频 URL：", url)

    print("\n=== 2. 图生视频 ===")
    url2 = image_to_video(
        "Gentle camera push-in on the scene with soft natural motion, "
        "subtle lighting changes, cinematic atmosphere",
        "https://www.gstatic.com/webp/gallery/1.jpg",
    )
    print("视频 URL：", url2)
