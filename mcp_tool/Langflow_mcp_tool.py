from mcp.server import FastMCP
import os
import httpx
import json
from dotenv import load_dotenv
import logging
from typing import Dict, Any, List

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 載入環境變數
load_dotenv()

# 創建一個 MCP 服務器
mcp = FastMCP("Langflow 聊天服務")

@mcp.tool()
async def get_langflow_response(message: str) -> str:
    """
    向 Langflow API 發送請求並獲取回應
    
    Args:
        message (str): 用戶輸入的消息
        
    Returns:
        str: Langflow 的回應
    """
    try:
        # 檢查 API URL
        api_url = os.getenv("LANGFLOW_API_URL")
        api_token = os.getenv("LANGFLOW_AUTH_TOKEN")
        api_key = os.getenv("LANGFLOW_API_KEY")

        if not api_url:
            return "錯誤：未設置 LANGFLOW_API_URL"

        headers = {
            "Content-Type": "application/json",
            'Authorization': f'Bearer {api_token}',
            'x-api-key': api_key
        }
        
        request_body = {
            "question": message,
            "chat_history": [],
            "input_value": message,
            "output_type": "chat",
            "input_type": "chat"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, headers=headers, json=request_body)
            if response.status_code != 200:
                return f"API 請求錯誤：狀態碼 {response.status_code}"
            data = response.json()
        
        # 提取回應內容
        bot_response = (
            data.get('result', {}).get('output') or
            data.get('result', {}).get('response') or
            data.get('outputs', [{}])[0].get('output') or
            (data.get('outputs', [{}])[0].get('outputs', [{}])[0].get('artifacts', {}).get('message')) or
            data.get('outputs', [{}])[0].get('messages', [{}])[0].get('message', '') or
            '抱歉，我無法理解您的問題。'
        )

        if isinstance(bot_response, dict):
            bot_response = (
                bot_response.get('text') or
                bot_response.get('content') or
                bot_response.get('message') or
                str(bot_response)
            )

        return bot_response

    except httpx.RequestError as e:
        return f"API 請求錯誤：{str(e)}"
    except Exception as e:
        return f"發生錯誤：{str(e)}"

@mcp.tool()
def get_chat_info() -> str:
    """獲取聊天服務的基本信息"""
    return """
【Langflow 聊天服務信息】

此服務提供以下功能：
1. 與 Langflow API 進行對話
2. 支持多輪對話
3. 自動處理錯誤和異常情況

使用方法：
- 直接發送消息即可開始對話
- 使用 get_langflow_response 工具發送具體請求
- 使用 get_chat_info 工具獲取服務信息

環境配置：
- LANGFLOW_API_URL: Langflow API 的地址
- LANGFLOW_AUTH_TOKEN: 認證令牌
- LANGFLOW_API_KEY: API 金鑰
"""

if __name__ == "__main__":
    mcp.run() 