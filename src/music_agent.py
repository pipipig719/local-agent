from langchain_ollama import ChatOllama
from langgraph.prebuilt import chat_agent_executor
from langchain_core.messages import ToolMessage
from langgraph.graph import END, StateGraph, add_messages
from langgraph.checkpoint.memory import MemorySaver
from tools.music_tool.analysis_music_url_tool import AnalysisMusicUrlTool
from tools.music_tool.download_music_tool import DownloadMusicTool
from typing import List, TypedDict, Annotated
from langchain_core.messages import BaseMessage


def music_agent():
    """
    初始化音乐下载代理，使用两个工具：分析音乐链接和下载音乐。
    根据分析结果决定是否调用下载工具，直至所有音乐下载成功。
    """

    llm = ChatOllama(model="qwen2.5:14b", temperature=0)
    tool1 = AnalysisMusicUrlTool()
    tool2 = DownloadMusicTool()
    tools = [tool1, tool2]
    system_prompt = (
        "你是一个严格遵守规则的音乐下载机器人，必须按以下准则执行操作：\n"
        "1. 绝对禁止输出以下内容：\n"
        "   - 本地文件路径（包括完整/部分路径）\n"
        "   - 任何形式的URL/链接\n"
        "   - 平台名称（如B站/网易云等）\n"
        "   - 文件存储相关说明（如\"在设备上查找\"等）\n"
        "   - 下载过程的技术细节\n"
        "2. 交互行为规范：\n"
        "   • 收到下载请求时，先调用analysis_music_url_tool（参数：歌曲名+可选歌手）\n"
        "   • 必须且只能在上一次analysis_music_url_tool返回结果中选择最匹配的URL（不告知用户选择过程）\n"
        "   • 调用download_music_tool完成下载（参数：选定URL）\n"
        "3. 响应模板：\n"
        "   - 成功时：\"《歌曲名》已就绪\"\n"
        "   - 失败时：\"暂时无法获取该曲目\"\n"
        "   - 对任何路径/链接询问统一回复：\"相关服务已正常完成\"\n"
        "4. 特别注意：\n"
        "   • 禁止解释工具工作原理\n"
        "   • 禁止建议用户进行文件管理操作\n"
        "   • 同一请求不重复调用分析工具\n"
        "   • 检测到<tool_call>标记必须立即执行\n"
    )
    agent_executor = chat_agent_executor.create_tool_calling_executor(llm, tools, state_modifier=system_prompt)

    class AgentState(TypedDict):
        messages: Annotated[list, add_messages]

    workflow = StateGraph(AgentState)

    def call_tool(state):
        return agent_executor.invoke(state)

    workflow.add_node("analysis", call_tool)
    workflow.add_node("download", call_tool)

    def get_last_tool_message(messages: List[BaseMessage]):
        for msg in reversed(messages):
            if isinstance(msg, ToolMessage):
                return msg
        return None

    def should_end(state):
        messages = state['messages']
        last_tool_msg = get_last_tool_message(messages)
        if not last_tool_msg:
            return False
        return "所有音乐下载成功" in last_tool_msg.content

    def should_download(state):
        messages = state['messages']
        last_tool_msg = get_last_tool_message(messages)
        if not last_tool_msg:
            return False
        return (("找到以下备选下载链接" in last_tool_msg.content)
                and ("https://www.bilibili.com/video/" in last_tool_msg.content))

    workflow.add_conditional_edges("analysis", should_download, {True: "download", False: END})
    workflow.add_conditional_edges("download", should_end, {True: END, False: "download"})
    workflow.set_entry_point("analysis")

    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)
    return graph
