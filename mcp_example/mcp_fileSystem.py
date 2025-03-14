import asyncio
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_core import CancellationToken
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os
from autogen_core.models import ModelFamily

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("MODEL")

## 其他第三方测试
def get_model_client_other() -> OpenAIChatCompletionClient:  # type: ignore
    return OpenAIChatCompletionClient(
        model=MODEL,
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/",
        model_capabilities={
            "json_output": False,
            "vision": False,
            "function_calling": True,
        },
    )

## OpenRouter
def get_model_client_OpenRouter() -> OpenAIChatCompletionClient:  # type: ignore
    "Mimic OpenAI API using Local LLM Server."
    return OpenAIChatCompletionClient(
        model="google/gemini-2.0-flash-001",
        api_key="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",
        base_url="https://openrouter.ai/api/v1",
        model_capabilities={
            "json_output": False,
            "vision": False,
            "function_calling": True,
        },
    )

# # ollama本地部署
def get_model_client_ollama() -> OpenAIChatCompletionClient:  # type: ignore
    return OpenAIChatCompletionClient(
        model="llama3.2:3b",
        api_key="ollama",
        base_url="http://localhost:11434/v1",
        model_capabilities={
            "json_output": False,
            "vision": False,
            "function_calling": True,
        },
    )

async def main():
    # Initialize Gemini model client
    model_client = get_model_client_OpenRouter()

    # 设置MCP fetch服务器参数
    # 这个服务器用于获取网页内容
    fetch_mcp_server = StdioServerParams(command="uvx", args=["mcp-server-fetch"])

    # 设置MCP文件系统服务器参数
    # 这个服务器用于写入本地文件
    write_mcp_server = StdioServerParams(
        command="npx.cmd", args=["-y", "@modelcontextprotocol/server-filesystem", "."]
    )
    # 从MCP服务器获取fetch工具
    tools_fetch = await mcp_server_tools(fetch_mcp_server)

    # 从MCP服务器获取filesystem工具
    tools_write = await mcp_server_tools(write_mcp_server)
    
    # 创建内容获取代理
    # 这个代理负责获取网页内容
    fetch_agent = AssistantAgent(
        name="content_fetcher",
        model_client = model_client,
        tools=tools_fetch,
        system_message="你是一个网页内容获取助手。使用fetch工具获取网页内容。获取成功后请传递给content_rewriter。"
    )
    
    # 创建内容改写代理
    # 这个代理负责将网页内容改写为科技资讯风格
    # 注意：不再在完成时添加TERMINATE，而是将内容传递给下一个代理    
    rewriter_agent = AssistantAgent(
        name="content_rewriter",
        model_client = model_client,
        system_message="""你是一个内容改写专家。将提供给你的网页内容改写为科技资讯风格的文章。
        科技资讯风格特点：
        1. 标题简洁醒目
        2. 开头直接点明主题
        3. 内容客观准确但生动有趣
        4. 使用专业术语但解释清晰
        5. 段落简短，重点突出
        
        当你完成改写后，请将内容传递给content_writer代理，让它将你的改写内容写入到文件中。"""
    )
    
    # 获取当前日期并格式化为YYYY-MM-DD
    current_date = datetime.now().strftime('%Y-%m-%d')

    # 创建文件写入代理
    # 这个代理负责将改写后的内容写入本地文件
    # 注意：这个代理会在完成任务后添加TERMINATE来结束对话
    write_agent = AssistantAgent(
        name="content_writer",
        model_client = model_client,
        tools=tools_write,
        system_message="""你是一个文件助手。使用filesystem工具将content_rewriter提供的内容写入txt文件，檔案名稱为test.txt。

        当你成功将文件写入后，回复"TERMINATE"以结束对话。"""
    )
    
    # 设置终止条件和团队
    # 当任何代理回复TERMINATE时，对话将结束
    termination = TextMentionTermination("TERMINATE")
    team = RoundRobinGroupChat([fetch_agent, rewriter_agent, write_agent], termination_condition=termination)
    
    task = "获取https://www.aivi.fyi/llms/introduce-Claude-3.7-Sonnet的内容，然后将其改写为科技资讯风格的文章，然后将改写的文章写入本地txt文件"
    
    # 只执行一次任务，使用run方法
    result = await team.run(task=task, cancellation_token=CancellationToken())
    
    # 遍历并打印所有消息，以显示整个过程
    print("\n整个对话过程：\n")
    print("-" * 60)
    
    for i, msg in enumerate(result.messages):
        # 判断消息的类型并相应地打印
        if hasattr(msg, 'source') and hasattr(msg, 'content'):
            print(f"\n---------- {msg.source} ----------")
            print(msg.content)
        elif hasattr(msg, 'source') and hasattr(msg, 'content') and isinstance(msg.content, list):
            print(f"\n---------- {msg.source} (工具调用) ----------")
            for item in msg.content:
                print(item)
        else:
            print(f"\n[消息 {i+1}] (类型: {type(msg).__name__})")
            print(msg)
        
        print("-" * 60)
    
    # 打印最终改写结果
    print("\n最终改写结果：\n")
    final_message = result.messages[-1]
    if hasattr(final_message, 'content'):
        print(final_message.content)
    
    return result

# 在Python脚本中运行异步代码的正确方式
if __name__ == "__main__":
    asyncio.run(main())