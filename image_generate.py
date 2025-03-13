import asyncio
import os
import base64
from typing import Dict, Any
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

# 讀取 .env 檔案
load_dotenv()

# 從環境變數讀取 API URL
STABLE_DIFFUSION_URL = os.getenv("STABLE_DIFFUSION_URL", "https://mystaable.zeabur.app")

def generate_image(params: Dict[str, Any]) -> str:
    """生成圖片的函數"""
    try:
        # 設定 API 端點
        endpoint = f"{STABLE_DIFFUSION_URL}/generate"
        
        # 發送請求
        response = requests.post(endpoint, json=params)
        response.raise_for_status()
        
        # 解析回應
        result = response.json()
        
        # 將 base64 圖像數據轉換為圖像檔案
        if 'images' in result and len(result['images']) > 0:
            image_data = base64.b64decode(result['images'][0])
            image = Image.open(BytesIO(image_data))
            
            # 儲存圖像
            output_path = "generated_image.png"
            image.save(output_path)
            return f"圖像已成功生成並儲存為: {output_path}"
        
        return "生成圖像失敗：未收到圖像數據"
        
    except Exception as e:
        return f"生成圖像時發生錯誤：{str(e)}"

async def main() -> None:
    # 測試參數
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
        "prompt": "a beautiful landscape",
        "sampler_name": "DPM++ 2M",
        "seed": -1,
        "steps": 30,
        "width": 512
    }

    # 生成圖片
    result = generate_image(params)
    print(result)

# 避免 asyncio.run() 衝突
loop = asyncio.get_event_loop()
if loop.is_running():
    task = loop.create_task(main())  # 適用於 Jupyter Notebook
else:
    asyncio.run(main())  # 適用於一般 Python 環境
