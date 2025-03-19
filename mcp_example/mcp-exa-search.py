import asyncio
import os
import json
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import SseMcpToolAdapter, SseServerParams, StdioServerParams, mcp_server_tools
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_core import CancellationToken
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()
EXA_API_KEY = os.getenv("EXA_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
def get_model_client_groq() -> OpenAIChatCompletionClient:  # type: ignore
    return OpenAIChatCompletionClient(
        model="qwen-2.5-32b",
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
        model_capabilities={
            "json_output": True,
            "vision": False,
            "function_calling": True,
        },
    )
async def format_search_results(message) -> str:
    try:
        if isinstance(message, list) and len(message) > 0:
            item = message[0]
            text = str(item)
            
            if "text='" in text:
                start_index = text.find("text='") + 6
                end_index = text.rfind("'")
                if start_index > 5 and end_index > start_index:
                    json_str = text[start_index:end_index]
                    json_str = bytes(json_str, 'utf-8').decode('unicode_escape')
                    data = json.loads(json_str)
                    
                    if "data" in data and "results" in data["data"]:
                        results = data["data"]["results"]
                        formatted_content = []
                        
                        if "results" in results:
                            for result in results["results"]:
                                content = f"標題: {result.get('title', '無標題')}\n"
                                content += f"網址: {result.get('url', '無網址')}\n"
                                if "text" in result:
                                    # 移除 HTML 標籤
                                    import re
                                    clean_text = re.sub(r'<[^>]+>', '', result["text"])
                                    content += f"內容:\n{clean_text}\n"
                                formatted_content.append(content)
                        
                        return "\n---\n".join(formatted_content)
    except Exception as e:
        return f"處理搜索結果時發生錯誤: {str(e)}"
    
    return "無法解析搜索結果"

async def main() -> None:
    try:
        # 創建必要的目錄
        current_dir = os.path.dirname(os.path.abspath(__file__))
        mbti_dir = os.path.join(current_dir, "mbti")
        if not os.path.exists(mbti_dir):
            os.makedirs(mbti_dir)
            
        # 獲取 CSV 文件的完整路徑
        csv_path = os.path.join(current_dir, "mbti_personalities.csv")
        
        # 初始化模型客戶端
        model_client = get_model_client_groq()
        
        # 設定各種 MCP 服務器參數
        search_server_params = SseServerParams(
            url="https://mcp.composio.dev/exa/prickly-eager-photographer-TMTAD8",
            headers={
                "api_key": EXA_API_KEY,
                "Content-Type": "application/json"
            },
            timeout=60,
        )
        
        write_mcp_server = StdioServerParams(
            command="npx.cmd", 
            args=["-y", "@modelcontextprotocol/server-filesystem", "."]
        )
        
        onedrive_server_params = SseServerParams(
            url="https://mcp.composio.dev/one_drive/prickly-eager-photographer-TMTAD8",
            timeout=60,
        )
        
        # 獲取所有工具
        search_adapter = await SseMcpToolAdapter.from_server_params(search_server_params, "EXA_SEARCH")
        tools_write = await mcp_server_tools(write_mcp_server)
        onedrive_adapter = await SseMcpToolAdapter.from_server_params(onedrive_server_params, "ONE_DRIVE_ONEDRIVE_UPLOAD_FILE")
        
        # 創建搜索代理
        search_agent = AssistantAgent(
            name="search_agent",
            model_client=model_client,
            tools=[search_adapter],
            system_message="""你是一個搜索專家。使用 EXA_SEARCH 工具搜索 MBTI 16型人格相關的資訊。
            搜索完成後，將結果傳遞給資料分析專家進行處理。
            
            請使用以下格式執行搜索：
            {
                "params": {
                    "query": "MBTI 16型人格特性、個性、職業、代表人物",
                    "type": "keyword",
                    "text": true,
                    "numResults": 1
                }
            }"""
        )
        
        # 創建資料分析專家
        analyst_agent = AssistantAgent(
            name="analyst_agent",
            model_client=model_client,
            system_message="""你是一個資料分析專家。從網頁內容中提取和整理以下資訊：
            1. 16種人格類型的特性
            2. 每種類型的個性特點
            3. 適合的職業
            4. 代表人物
            
            請將資訊整理成 CSV 格式的文本，包含以下欄位：
            personality_type,characteristics,traits,suitable_jobs,famous_people
            
            完成後，請將整理好的資料傳遞給 file_writer 代理。"""
        )
        
        # 創建文件寫入代理
        file_writer = AssistantAgent(
            name="file_writer",
            model_client=model_client,
            tools=tools_write,
            system_message=f"""你是一個文件處理專家。使用 filesystem 工具將資料寫入 CSV 文件。
            
            文件名稱：mbti_personalities.csv
            檔案路徑：{csv_path}
            格式編碼：utf-8
            欄位：personality_type,characteristics,traits,suitable_jobs,famous_people
            
            寫入完成後，請將結果傳遞給 onedrive_uploader 代理。"""
        )
        
        # 先處理路徑
        upload_path = csv_path.replace('\\', '/')
        
        # 新增：OneDrive 上傳代理
        onedrive_uploader = AssistantAgent(
            name="onedrive_uploader",
            model_client=model_client,
            tools=[onedrive_adapter],
            system_message=f"""你是一個 OneDrive 文件上傳專家。
            請將以下文件上傳到 OneDrive：
            
            檔案路徑：{upload_path}
            上傳目錄名稱：深度學習小組
            
            請使用 ONE_DRIVE_ONEDRIVE_UPLOAD_FILE 工具，參數格式如下：
            {{
                "params": {{
                    "file_schema_parsed_file": "{upload_path}",
                    "folder": "深度學習小組"
                }}
            }}
            
            上傳完成後，請回覆 "TERMINATE" 結束對話。"""
        )
        
        # 設定終止條件和團隊
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([search_agent, analyst_agent, file_writer, onedrive_uploader],
            termination_condition=termination
        )
        
        # 執行搜索任務
        print("開始執行團隊任務...")
        try:
            result = await team.run(
                task="""請依序執行以下任務：
                1. 搜索代理：使用 EXA_SEARCH 搜索 MBTI 16型人格的相關資訊
                2. 分析代理：整理出每種人格類型的特性、個性、適合職業和代表人物
                3. 文件代理：將整理好的資料寫入 CSV 文件
                4. 上傳代理：將文件上傳到 OneDrive 的深度學習小組資料夾
                
                請確保每個代理完成自己的任務後，將結果傳遞給下一個代理。""",
                cancellation_token=CancellationToken()
            )
            
            # 處理結果
            if result and result.messages:
                print("\n=== 執行過程 ===")
                for msg in result.messages:
                    if hasattr(msg, 'source') and hasattr(msg, 'content'):
                        print(f"\n--- {msg.source} ---")
                        print(msg.content)
                    print("-" * 50)
            else:
                print("執行完成但沒有返回消息")
                
        except Exception as e:
            print(f"團隊執行過程中發生錯誤：{str(e)}")
            raise

        # 在 main 函數中添加調試信息
        print(f"模型客戶端配置：{model_client}")
        print(f"搜索適配器：{search_adapter}")
        print(f"文件工具：{tools_write}")
        print(f"OneDrive 適配器：{onedrive_adapter}")

    except Exception as e:
        print(f"執行過程中發生錯誤：{str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())