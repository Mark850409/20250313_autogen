#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv
from mcp.server import FastMCP
import httpx

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 載入環境變數
load_dotenv()

# 創建一個 MCP 服務器
mcp = FastMCP("圖片生成服務")

def check_environment():
    """檢查必要的環境變數"""
    required_vars = ["STABLE_DIFFUSION_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"缺少必要的環境變數: {', '.join(missing_vars)}")
        return False
    return True

@mcp.tool()
async def generate_image(
    prompt: str,
    width: int = 512,
    height: int = 512,
    steps: int = 30
) -> str:
    """
    生成圖片的工具
    
    Args:
        prompt (str): 圖片生成的提示詞
        width (int): 圖片寬度，預設 512
        height (int): 圖片高度，預設 512
        steps (int): 生成步驟數，預設 30
        
    Returns:
        str: Markdown 格式的圖片連結
    """
    logger.info(f"開始生成圖片，提示詞：{prompt}")
    logger.info(f"參數設置 - 寬度：{width}, 高度：{height}, 步驟數：{steps}")
    
    try:
        # 檢查 API URL
        api_url = os.getenv("STABLE_DIFFUSION_URL")
        if not api_url:
            return "錯誤：未設置 STABLE_DIFFUSION_URL"

        # 設定請求參數
        generation_params = {
            "batch_size": 1,
            "cfg_scale": 7,
            "face_detector": "face_yolov8n.pt",
            "hand_detector": "hand_yolov8n.pt",
            "height": height,
            "width": width,
            "negative_prompt": "",
            "override_settings": {
                "sd_model_checkpoint": "sd-v1-5-inpainting.ckpt"
            },
            "person_detector": "person_yolov8n-seg.pt",
            "prompt": prompt,
            "sampler_name": "DPM++ 2M",
            "seed": -1,
            "steps": steps
        }

        headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }

        # 使用 httpx 發送非同步請求
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_url}/generate",
                headers=headers,
                json=generation_params,
                timeout=60  # 添加超時設定
            )
            
            if response.status_code != 200:
                return f"API 請求錯誤：狀態碼 {response.status_code}"

            # 直接獲取文本回應，因為 API 直接返回 URL 字符串
            image_url = response.text.strip()
            if not image_url:
                return "錯誤：API 返回空回應"
            
            # 驗證返回的 URL
            if not image_url.startswith(('http://', 'https://')):
                logger.error(f'無效的圖片 URL: {image_url}')
                return "錯誤：收到無效的圖片 URL"

            logger.info(f"成功獲取圖片 URL：{image_url}")

            # 返回 Markdown 格式的圖片
            return f"""
### 生成的圖片

![Generated Image]({image_url})

[點擊查看原圖]({image_url})
"""

    except httpx.TimeoutException as e:
        logger.error(f'請求超時: {e}')
        return "錯誤：請求超時，請稍後再試"
    except httpx.RequestError as e:
        logger.error(f'API 請求錯誤: {e}')
        return f"API 請求錯誤：{str(e)}"
    except Exception as e:
        logger.error(f'發生未知錯誤: {e}')
        return f"發生錯誤：{str(e)}"

@mcp.tool()
def get_service_info() -> str:
    """獲取圖片生成服務的基本信息"""
    api_url = os.getenv("STABLE_DIFFUSION_URL", "未設置")
    return f"""
【圖片生成服務信息】

此服務提供以下功能：
1. 基於文字提示生成圖片
2. 支持自定義圖片尺寸
3. 支持調整生成步驟數
4. 自動處理錯誤和異常情況

使用方法：
- 使用 generate_image 工具生成圖片
- 使用 get_service_info 工具獲取服務信息

參數說明：
- prompt: 圖片生成的提示詞（必填）
- width: 圖片寬度（預設 512）
- height: 圖片高度（預設 512）
- steps: 生成步驟數（預設 30）

環境配置：
- STABLE_DIFFUSION_URL: {api_url}

服務狀態：{'正常運行中' if check_environment() else '配置不完整'}
"""

if __name__ == "__main__":
    if not check_environment():
        logger.error("環境變數設置不完整，程式終止")
        exit(1)
    mcp.run() 