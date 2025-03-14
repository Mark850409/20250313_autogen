import os
import requests
import json
from dotenv import load_dotenv
import logging
from typing import Dict, Any, List
from autogen_ext.tools.mcp import SseServerParams, mcp_server_tools

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 載入環境變數
load_dotenv()

def get_mcp_response(message: str) -> str:
    """
    向遠端 MCP 服務發送請求並獲取回應
    
    Args:
        message (str): 用戶輸入的消息
        
    Returns:
        str: MCP 服務的回應
    """
    api_url = os.getenv("LANGFLOW_API_URL")
    api_token = os.getenv("LANGFLOW_AUTH_TOKEN")
    api_key = os.getenv("LANGFLOW_API_KEY")


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
        response = requests.post(
            api_url,  # 直接使用完整的 API URL
            headers=headers,
            json=request_body
        )
        response.raise_for_status()
        data = response.json()
        
        # 提取回應內容，使用與 langflow_api.py 相同的邏輯
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

    except Exception as error:
        logger.error(f'MCP API 請求失敗: {error}')
        return '抱歉，我現在無法回應。請稍後再試。'

async def get_mcp_tools() -> List[Dict[str, Any]]:
    """
    獲取可用的 MCP 工具列表
    
    Returns:
        List[Dict[str, Any]]: 可用工具列表
    """
    api_url = os.getenv("MCP_API_URL")
    api_token = os.getenv("MCP_API_TOKEN")

    server_params = SseServerParams(
        url=api_url,
        headers={"Authorization": f"Bearer {api_token}"}
    )

    try:
        tools = await mcp_server_tools(server_params)
        return tools
    except Exception as error:
        logger.error(f'獲取 MCP 工具失敗: {error}')
        return []

def main():
    """
    主函數，用於測試 MCP API
    """
    print("開始對話（輸入 'exit' 結束）")
    while True:
        user_input = input("\n你: ").strip()
        if user_input.lower() == 'exit':
            print("結束對話")
            break
        
        response = get_mcp_response(user_input)
        print(f"MCP: {response}")

if __name__ == "__main__":
    main()
