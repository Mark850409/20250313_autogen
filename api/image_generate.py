#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

# 讀取 .env 檔案
load_dotenv()

def generate_image(prompt: str, timeout: int = 60) -> str:
    """生成圖片的函數
    
    Args:
        prompt (str): 圖片生成提示詞
        timeout (int): 請求超時時間（秒），默認60秒
        
    Returns:
        str: 生成結果訊息
    """
    try:
        # 檢查 API URL
        api_url = os.getenv("STABLE_DIFFUSION_URL", "https://mystaable.zeabur.app")
        if not api_url:
            return "錯誤：未設置 STABLE_DIFFUSION_URL"

        # 設定請求
        endpoint = f"{api_url}/generate"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        
        params = {
            "batch_size": 1,
            "cfg_scale": 7,
            "face_detector": "face_yolov8n.pt",
            "hand_detector": "hand_yolov8n.pt",
            "height": 512,
            "negative_prompt": "",
            "override_settings": {
                "sd_model_checkpoint": "sd-v1-5-inpainting.ckpt"
            },
            "person_detector": "person_yolov8n-seg.pt",
            "prompt": prompt,
            "sampler_name": "DPM++ 2M",
            "seed": -1,
            "steps": 30,
            "width": 512
        }
        
        # 發送請求
        print(f"正在發送請求到：{endpoint}")
        print(f"請等待最多 {timeout} 秒...")
        response = requests.post(endpoint, headers=headers, json=params, timeout=timeout)
        response.raise_for_status()
        
        # 解析回應
        image_url = response.text.strip()
        if not image_url:
            return "錯誤：API 返回空回應"
            
        print(f"獲取到圖片 URL：{image_url}")
        
        # 下載圖片
        print("正在下載圖片...")
        img_response = requests.get(image_url, timeout=timeout)
        img_response.raise_for_status()
        
        # 保存圖片
        image = Image.open(BytesIO(img_response.content))
        output_path = "generated_image.png"
        image.save(output_path)
        return f"圖像已成功生成並儲存為: {output_path}"
        
    except requests.exceptions.Timeout:
        return "錯誤：請求超時，請稍後再試"
    except requests.exceptions.RequestException as e:
        return f"API 請求錯誤：{str(e)}"
    except Exception as e:
        return f"發生錯誤：{str(e)}"

# 直接執行生成
prompt = "a beautiful cat sitting on a window sill"
print("開始生成圖像...")
result = generate_image(prompt, timeout=60)  # 設置 60 秒超時
print(result)
