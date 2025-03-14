import asyncio
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_core import CancellationToken
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools

async def main():
    # Setup the MCP fetch server parameters
    fetch_mcp_server = StdioServerParams(command="uvx", args=["mcp-server-fetch"])
    
    # Get the fetch tool from the MCP server
    tools = await mcp_server_tools(fetch_mcp_server)
    
    # Create fetch agent with the MCP fetch tool
    fetch_agent = AssistantAgent(
        name="content_fetcher",
        model_client=OllamaChatCompletionClient(model="llama3.2:3b"),
        tools=tools,  # The MCP fetch tool will be included here
        system_message="你是一个网页内容获取助手。使用fetch工具获取网页内容。"
    )
    
    # Create rewriter Agent (unchanged)
    rewriter_agent = AssistantAgent(
        name="content_rewriter",
        model_client=OllamaChatCompletionClient(model="llama3.2:3b"),
        system_message="""你是一个内容改写专家。将提供给你的网页内容改写为科技资讯风格的文章。
        科技资讯风格特点：
        1. 标题简洁醒目
        2. 开头直接点明主题
        3. 内容客观准确但生动有趣
        4. 使用专业术语但解释清晰
        5. 段落简短，重点突出
        
        当你完成改写后，回复TERMINATE。"""
    )
    
    # Set up termination condition and team (unchanged)
    termination = TextMentionTermination("TERMINATE")
    team = RoundRobinGroupChat([fetch_agent, rewriter_agent], termination_condition=termination)
    
    # Run the workflow (unchanged)
    result = await team.run(
        task="获取https://www.aivi.fyi/llms/introduce-Claude-3.7-Sonnet的内容，然后将其改写为科技资讯风格的文章",
        cancellation_token=CancellationToken()
    )
    
    print("\n最终改写结果：\n")
    print(result.messages[-1].content)
    return result

# This is the correct way to run async code in a Python script
if __name__ == "__main__":
    asyncio.run(main())