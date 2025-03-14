#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import requests
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv
from autogen_ext.tools.mcp import SseServerParams, mcp_server_tools

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 載入環境變數
load_dotenv()

def get_image_generation_response(prompt: str, timeout: int = 60) -> str:
    """
    向遠端 MCP 服務發送圖片生成請求並獲取回應
    
    Args:
        prompt (str): 圖片生成提示詞
        timeout (int): 請求超時時間（秒）
        
    Returns:
        str: Markdown 格式的圖片連結
    """
    try:
        # 檢查 API URL
        api_url = os.getenv("STABLE_DIFFUSION_URL")

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

        logger.info(f"正在發送圖片生成請求到：{endpoint}")
        logger.info(f"請等待最多 {timeout} 秒...")
        
        response = requests.post(endpoint, headers=headers, json=params, timeout=timeout)
        response.raise_for_status()
        
        # 解析回應
        image_url = response.text.strip()
        if not image_url:
            return "錯誤：API 返回空回應"
            
        logger.info(f"獲取到圖片 URL：{image_url}")
        
        # 返回 Markdown 格式的圖片
        markdown_response = f"""
### 生成的圖片

![Generated Image]({image_url})

[點擊查看原圖]({image_url})
"""
        return markdown_response

    except requests.exceptions.Timeout:
        return "錯誤：請求超時，請稍後再試"
    except requests.exceptions.RequestException as e:
        logger.error(f'API 請求錯誤: {e}')
        return f"API 請求錯誤：{str(e)}"
    except Exception as e:
        logger.error(f'發生未知錯誤: {e}')
        return f"發生錯誤：{str(e)}"

async def get_mcp_tools() -> List[Dict[str, Any]]:
    """
    獲取可用的 MCP 工具列表
    
    Returns:
        List[Dict[str, Any]]: 可用工具列表
    """
    try:
        api_url = os.getenv("MCP_API_URL")
        api_token = os.getenv("MCP_API_TOKEN")

        server_params = SseServerParams(
            url=api_url,
            headers={"Authorization": f"Bearer {api_token}"}
        )

        tools = await mcp_server_tools(server_params)
        return tools
    except Exception as error:
        logger.error(f'獲取 MCP 工具失敗: {error}')
        return []

def main():
    """
    主函數，用於測試圖片生成功能
    """
    print("開始圖片生成測試（輸入 'exit' 結束）")
    while True:
        prompt = input("\n請輸入圖片描述: ").strip()
        if prompt.lower() == 'exit':
            print("結束測試")
            break
        
        result = get_image_generation_response(prompt)
        print(f"結果:\n{result}")

if __name__ == "__main__":
    main() 