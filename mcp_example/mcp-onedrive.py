import asyncio
import os
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import SseMcpToolAdapter, SseServerParams
from autogen_agentchat.ui import Console
from autogen_core import CancellationToken
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

## groq NIM
def get_model_client_groq() -> OpenAIChatCompletionClient:  # type: ignore
    return OpenAIChatCompletionClient(
        model="deepseek-r1-distill-llama-70b",
        api_key='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',
        base_url="https://api.groq.com/openai/v1",
        model_capabilities={
            "json_output": True,
            "vision": False,
            "function_calling": True,
        },
    )

async def main() -> None:
    try:
            
        # 設定 MCP SSE 遠端連線
        server_params = SseServerParams(
            url="https://mcp.composio.dev/one_drive/prickly-eager-photographer-TMTAD8",
            timeout=120,
        )
        
        print("正在連接到MCP服務器...")
        
        # 創建 MCP 工具適配器
        create_folder_adapter = await SseMcpToolAdapter.from_server_params(
            server_params, 
            "ONE_DRIVE_ONEDRIVE_CREATE_FOLDER"
        )
        create_text_file_adapter = await SseMcpToolAdapter.from_server_params(
            server_params, 
            "ONE_DRIVE_ONEDRIVE_CREATE_TEXT_FILE"
        )

        # 獲取模型客戶端
        model_client = get_model_client_groq()
        
        # 讀取 mbti_personalities.csv 文件內容
        csv_file = os.path.join(os.getcwd(), "mbti_personalities.csv")
        if os.path.exists(csv_file):
            # 嘗試不同的編碼方式
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                file_content = f.read()

        else:
            print("錯誤: mbti_personalities.csv 文件不存在")
            return
        
        # 除錯用：檢查文件內容
        print("檔案內容預覽：")
        print(file_content[:200])  # 只顯示前200個字符
        print("檔案編碼檢查：")
        print("內容類型：", type(file_content))
        print("字符數：", len(file_content))
        
        # 創建上傳代理
        uploader = AssistantAgent(
            name="onedrive_uploader",
            system_message="""[必須執行的兩個指令]

第一個指令（創建資料夾）：
{
    "name": "ONE_DRIVE_ONEDRIVE_CREATE_FOLDER",
    "parameters": {
        "params": {
            "name": "深度學習小組"
        }
    }
}

第二個指令（創建文本文件）：
{
    "name": "ONE_DRIVE_ONEDRIVE_CREATE_TEXT_FILE",
    "parameters": {
        "params": {
            "name": "mbti_personalities.csv",
            "content": "測試內容",
            "folder": "folder_id"
        }
    }
}

[執行要求]
1. 必須依序執行上述兩個指令
2. 兩個指令都要執行，不能只執行一個
3. 每個指令執行後都要等待回應
4. 不要修改任何參數或格式
5. 回報每個指令的執行結果""",
            model_client=model_client,
            tools=[create_folder_adapter, create_text_file_adapter]
        )

        print("\n開始上傳文件到 OneDrive...")
        
        # 分別執行兩個指令
        print("\n1. 創建資料夾...")
        create_result = await uploader.run(
            task="""請執行第一個指令（創建資料夾）：
{
    "name": "ONE_DRIVE_ONEDRIVE_CREATE_FOLDER",
    "parameters": {
        "params": {
            "name": "深度學習小組"
        }
    }
}""",
            cancellation_token=CancellationToken()
        )

        # 從創建資料夾的結果中獲取資料夾 ID
        folder_id = None
        if hasattr(create_result, 'messages'):
            for msg in create_result.messages:
                if hasattr(msg, 'content') and isinstance(msg.content, str):
                    try:
                        # 使用更簡單的方式解析 JSON 字符串
                        content = msg.content
                        if '"id"' in content:
                            # 找到 id 的位置
                            id_start = content.find('"id":') + 6
                            id_end = content.find('"', id_start + 1)
                            if id_start != -1 and id_end != -1:
                                folder_id = content[id_start:id_end].strip('"')
                                print(f"\n成功獲取資料夾 ID: {folder_id}")
                                break

                    except Exception as e:
                        print(f"處理回應時出錯: {str(e)}")
                        print(f"原始內容: {msg.content}")

        if folder_id:
            print("\n2. 創建文本文件...")
            upload_result = await uploader.run(
                task=f"""請執行第二個指令（創建文本文件）：
{{
    "name": "ONE_DRIVE_ONEDRIVE_CREATE_TEXT_FILE",
    "parameters": {{
        "params": {{
            "name": "mbti_personalities.csv",
            "content": "{file_content}",
            "folder": "{folder_id}"
        }}
    }}
}}""",
                cancellation_token=CancellationToken()
            )
            print("\n檢查文件上傳結果...")
        else:
            print("\n❌ 無法獲取資料夾 ID，無法繼續上傳文件")
            print("請檢查資料夾創建回應的格式")
        
        # 顯示執行結果
        print("\n=== 執行結果 ===")
        if hasattr(create_result, 'messages'):
            print("所有訊息：")
            for i, msg in enumerate(create_result.messages):
                print(f"\n訊息 {i+1}:")
                print(f"類型: {type(msg)}")
                print(f"內容: {msg.content if hasattr(msg, 'content') else '無內容'}")
        
        # 只在成功創建文件時才檢查上傳結果
        if folder_id:
            if hasattr(upload_result, 'messages'):
                for msg in upload_result.messages:
                    if hasattr(msg, 'content'):
                        try:
                            # 先打印原始內容以便調試
                            print("\n原始回應:", msg.content)
                            
                            # 檢查 content 是否為字符串
                            if isinstance(msg.content, str):
                                if '"successful": true' in msg.content:
                                    print("\n✅ 文件上傳成功！")
                                elif 'error' in msg.content:
                                    print("\n❌ 文件上傳失敗！")
                                    print("錯誤信息：", msg.content)
                            else:
                                # 如果不是字符串，直接打印內容
                                print("\n回應內容（非字符串）：", msg.content)
                                
                            print("回應內容類型:", type(msg.content))
                            print("完整回應內容:", msg.content)
                                
                        except Exception as e:
                            print(f"處理回應時出錯：{str(e)}")
                            print("原始回應類型：", type(msg.content))
                            print("原始回應內容：", msg.content)
        
        print("=" * 50)
        
    except asyncio.TimeoutError:
        print("操作超時，請檢查網絡連接或服務是否正常運行")
    except Exception as e:
        print(f"發生錯誤：{str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())