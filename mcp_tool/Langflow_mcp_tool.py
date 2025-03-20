from mcp.server import FastMCP
import os
import httpx
import json
from dotenv import load_dotenv
import logging
from typing import Dict, Any, List, Tuple

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
    根據訊息內容選擇適當的 Langflow API 發送請求並獲取回應
    
    Args:
        message (str): 用戶輸入的消息
        
    Returns:
        str: Langflow 的回應
    """
    try:
        # 直接在函數中判斷 API URL
        api_token = os.getenv("LANGFLOW_AUTH_TOKEN")
        api_key = os.getenv("LANGFLOW_API_KEY")
        
        # 判斷使用哪個 API URL
        if any(keyword in message for keyword in ["韓國", "男團", "女團", "偶像", "Kpop"]):
            api_url = os.getenv("LANGFLOW_API_URL_KOREA")
        elif any(keyword in message for keyword in ["MBTI", "人格", "性格", "測驗", "測試"]):
            api_url = os.getenv("LANGFLOW_API_URL_MBTI")
        elif any(keyword in message for keyword in ["輪播圖", "快速提問", "知識庫管理", "LangFlow串接"]):
            api_url = os.getenv("LANGFLOW_API_URL_ORDER")
        else:
            api_url = os.getenv("LANGFLOW_API_URL_GENERAL")

        if not api_url:
            return "錯誤：未設置對應的 API URL"

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
        
        try:
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
                None
            )

            if bot_response:
                if isinstance(bot_response, dict):
                    bot_response = (
                        bot_response.get('text') or
                        bot_response.get('content') or
                        bot_response.get('message') or
                        str(bot_response)
                    )
                return bot_response
            
            return "無法獲取有效回應"
                
        except httpx.RequestError as e:
            logger.error(f"API {api_url} 請求失敗：{str(e)}")
            return f"API 請求失敗：{str(e)}"

    except Exception as e:
        logger.error(f"發生錯誤：{str(e)}")
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