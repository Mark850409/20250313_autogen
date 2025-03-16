from mcp.server import FastMCP
import os
from exa_py import Exa
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
mcp = FastMCP("EXA 搜索服務")

@mcp.tool()
async def exa_search(query: str, num_results: int = 5, category: str = "web", search_type: str = "keyword") -> str:
    """
    使用 EXA Search API 進行網路搜索
    
    Args:
        query (str): 搜索關鍵字
        num_results (int): 返回結果數量，預設為5
        category (str): 搜索類別，預設為"web"
        search_type (str): 搜索類型，預設為"keyword"
        
    Returns:
        str: 格式化的搜索結果
    """
    try:
        # 檢查 API Key
        exa_api_key = os.getenv("EXA_API_KEY")
        if not exa_api_key:
            return "錯誤：未設置 EXA_API_KEY"

        # 初始化 Exa 客戶端
        exa = Exa(api_key=exa_api_key)

        # 執行搜索
        search_response = exa.search_and_contents(
            query,
            text=True,
            num_results=num_results,
            category=category,
            type=search_type
        )

        # 取得搜索結果
        results = search_response.results

        # 格式化結果
        formatted_content = []
        for result in results:
            content = f"標題: {result.title if hasattr(result, 'title') else '無標題'}\n"
            content += f"網址: {result.url if hasattr(result, 'url') else '無網址'}\n"
            if hasattr(result, 'text'):
                # 移除 HTML 標籤
                import re
                clean_text = re.sub(r'<[^>]+>', '', result.text)
                content += f"內容:\n{clean_text}\n"
            formatted_content.append(content)

        return "\n---\n".join(formatted_content) if formatted_content else "無搜索結果"

    except Exception as e:
        logger.error(f"搜索過程中發生錯誤: {str(e)}")
        return f"發生錯誤：{str(e)}"

@mcp.tool()
def get_search_info() -> str:
    """獲取搜索服務的基本信息"""
    return """
【EXA 搜索服務信息】

此服務提供以下功能：
1. 使用 EXA Search API 進行網路搜索
2. 支持自定義搜索結果數量
3. 支持自定義搜索類別和類型
4. 自動格式化搜索結果

使用方法：
- 使用 exa_search 工具進行搜索，可指定：
  * 關鍵字 (query)
  * 結果數量 (num_results)
  * 搜索類別 (category)
  * 搜索類型 (search_type)
- 使用 get_search_info 工具獲取服務信息

環境配置：
- EXA_API_KEY: EXA Search API 的金鑰

支援的搜索類別：
- web: 網頁搜索
- news: 新聞搜索
- academic: 學術搜索
"""

if __name__ == "__main__":
    mcp.run() 