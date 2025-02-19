import os
from langchain_ollama import ChatOllama
from langgraph.prebuilt import chat_agent_executor
from tools.baidu_weather_tool.baidu_weather_tool import WeatherTool
from tools.get_now_tool.get_now_tool import GetNowTool
from tools.email_tool.email_tool import EmailTool
from langchain_core.messages import HumanMessage


def initialize_base_model():
    """
    初始化基础语言模型，并配置调用工具，
    要求回答时严格使用中文、转换数字格式且不使用 Markdown。
    """

    llm = ChatOllama(model="qwen2.5:14b", temperature=0)
    weather_tool = WeatherTool()
    get_now_tool = GetNowTool()
    email_tool = EmailTool()
    tools = [weather_tool, get_now_tool, email_tool]

    prompt = (
        "请严格按照以下要求回答问题："
        "1.使用中文回答问题，尽可能在回答中不要出现英文字母（如abc）"
        "2.回答中所有阿拉伯数字必须转换为中文数字"
        "例如：温度为10摄氏度，体感温度为9摄氏度，相对湿度为30%，北风为1级。需要改为：温度为十摄氏度，体感温度为九摄氏度，相对湿度为三十%，北风为一级。"
        "3.不使用任何Markdown格式或代码框"
        "保持回答自然流畅，符合中文表达习惯"
        "现在请用纯文本格式回答我的问题："
    )
    agent_executor = chat_agent_executor.create_tool_calling_executor(llm, tools, state_modifier=prompt)
    return agent_executor


def base_model_invoke(question: str) -> str:
    """调用基础语言模型处理问题"""
    config = {'configurable': {'session_id': os.getenv('SESSION_ID')}}
    resp = initialize_base_model().invoke({"messages": [HumanMessage(content=question)]}, config=config)
    if resp.get("messages"):
        message = resp["messages"][-1]
        return message.content.replace("\n", "")
    else:
        return ""
