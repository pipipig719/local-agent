import os
import logging
import gradio as gr
from gradio import ChatMessage
from langchain_core.messages import HumanMessage
from rag import initialize_rag_system, add_document_by_url, add_document_by_pdf
from base_model import initialize_base_model, base_model_invoke
from music_agent import music_agent
from session_manager import SessionManager
from tts import TTS

# 初始化共享资源和配置参数
session_manager = SessionManager()
base_model = initialize_base_model()
conversational_rag_chain, vectorstore = initialize_rag_system(session_manager)
music_agent_instance = music_agent()
config = {'configurable': {'session_id': os.getenv('SESSION_ID')}}
tts_instance = TTS()


def ask_question(question: str) -> str:
    """调用 RAG 系统回答问题"""
    response = conversational_rag_chain.invoke({"input": question}, config=config)
    answer = response.get("answer", "").replace("\n", "")
    return answer


def return_none():
    return None


def add_document_by_url_chroma(url: str, classname: str) -> str:
    """通过 URL 上传文档到向量库"""
    try:
        if classname:
            add_document_by_url(url, vectorstore, classname)
            return "文档提交成功"
        return "classname为必填字段"
    except Exception as e:
        logging.exception("add_document_by_url_chroma出错")
        return str(e)


async def add_document_by_pdf_chroma(pdf_path: str) -> str:
    """通过 PDF 上传文档到向量库"""
    try:
        await add_document_by_pdf(pdf_path, vectorstore)
        return "文档提交成功"
    except Exception as e:
        logging.exception("add_document_by_pdf_chroma出错")
        return str(e)


def get_similar_score(question: str) -> str:
    """查询与输入问题相似的文档及相似度得分"""
    results = vectorstore.similarity_search_with_score(question, k=4)
    text = ""
    for doc, score in results:
        text += "文档:" + doc.page_content[:100] + " 相似度得分:" + str(score) + "\n"
    return text


def download_music(question: str) -> (str, str):
    """调用音乐代理下载音乐，并返回回复文本和音乐文件路径"""
    resp = music_agent_instance.invoke(
        {'messages': [HumanMessage(content=question)]},
        {"configurable": {"thread_id": os.getenv('SESSION_ID')}},
    )
    message = resp["messages"][-1]
    file_path = None
    for msg in reversed(resp["messages"]):
        if msg.name == "download_music_tool" and "音乐文件保存本地路径:" in msg.content:
            file_path = msg.content.split("音乐文件保存本地路径:")[1]
            break
    return message.content, file_path


def rag_respond(message: str, history: list) -> (str, list, str):
    """RAG 模式回复，将问题传递给 RAG 系统并更新历史记录"""
    bot_message = ask_question(message)
    history.append(ChatMessage(role="user", content=message))
    history.append(ChatMessage(role="assistant", content=bot_message))
    return "", history, bot_message


def music_respond(message: str, history: list) -> (str, list, str, str):
    """音乐模式回复，调用音乐代理并更新历史记录"""
    bot_message, file_path = download_music(message)
    history.append(ChatMessage(role="user", content=message))
    history.append(ChatMessage(role="assistant", content=bot_message))
    return "", history, file_path, bot_message


def base_model_respond(message: str, history: list) -> (str, list, str):
    """调用基础语言模型回复，并更新聊天历史"""
    bot_message = base_model_invoke(message)
    history.append(ChatMessage(role="user", content=message))
    history.append(ChatMessage(role="assistant", content=bot_message))
    return "", history, bot_message


def trans_text(gen_text: str):
    """处理生成文本，并调用 TTS 生成语音"""
    if gen_text:
        if "<think>" in gen_text:
            if "</think>" in gen_text:
                gen_text = gen_text.split("</think>")[-1].replace("\n", "")
                if not gen_text:
                    return None
            else:
                return None
    else:
        return None
    return tts_instance.generate(gen_text)


def launch_demo():
    """构建 Gradio 前端界面并启动服务"""
    with gr.Blocks() as demo:
        # 用户输入区域
        with gr.Row():
            with gr.Column():
                textarea1 = gr.TextArea(lines=10, max_lines=30, label="用户输入", placeholder="请输入您的问题...")

        # 标签页：AI、RAG、音乐下载
        with gr.Tab(label="AI"):
            with gr.Row():
                button3 = gr.Button(value="发送", variant="primary")
                button4 = gr.Button(value="清空用户输入", variant="stop")

        with gr.Tab(label="RAG"):
            with gr.Row():
                button1 = gr.Button(value="发送", variant="primary")
                button2 = gr.Button(value="清空用户输入", variant="stop")
            with gr.Accordion("文档管理", open=False):
                with gr.Tab(label="URL上传"):
                    with gr.Row():
                        url_input = gr.Textbox(label="网页地址", placeholder="请输入文档URL...")
                        class_input = gr.Textbox(label="CSS类名", placeholder="请输入内容CSS类名(必填)")
                    url_status = gr.Textbox(label="上传状态")
                    url_submit = gr.Button("提交URL文档", variant="secondary")
                with gr.Tab(label="PDF上传"):
                    with gr.Row():
                        pdf_input = gr.Textbox(label="PDF路径", placeholder="请输入PDF文件路径...")
                    pdf_status = gr.Textbox(label="上传状态")
                    pdf_submit = gr.Button("提交PDF文档", variant="secondary")
            with gr.Accordion("相似度分析", open=False):
                textarea3 = gr.TextArea(label="相似度得分", lines=5, max_lines=10)

        with gr.Tab(label="音乐下载"):
            with gr.Row():
                audio = gr.Audio(type="filepath", label="下载的歌曲", loop=True)
            with gr.Row():
                button5 = gr.Button(value="发送", variant="primary")
                button6 = gr.Button(value="清空用户输入", variant="stop")
                button7 = gr.Button(value="清空音乐", variant="stop")

        with gr.Row():
            with gr.Column():
                chatbot = gr.Chatbot(type="messages", show_copy_all_button=True, height=600)

        hidden_ai_resp = gr.Textbox(visible=False, interactive=False)
        hidden_ai_audio = gr.Audio(visible=False, interactive=False, autoplay=True, show_download_button=False)

        # 按钮事件绑定
        button1.click(fn=return_none, outputs=hidden_ai_audio) \
            .then(fn=get_similar_score, inputs=textarea1, outputs=textarea3) \
            .then(fn=rag_respond, inputs=[textarea1, chatbot], outputs=[textarea1, chatbot, hidden_ai_resp]) \
            .success(fn=trans_text, inputs=hidden_ai_resp, outputs=hidden_ai_audio)
        button2.click(fn=return_none, outputs=textarea1)
        url_submit.click(fn=add_document_by_url_chroma, inputs=[url_input, class_input], outputs=url_status)
        pdf_submit.click(fn=add_document_by_pdf_chroma, inputs=pdf_input, outputs=pdf_status)
        button5.click(fn=return_none, outputs=audio) \
            .then(fn=return_none, outputs=hidden_ai_audio) \
            .then(fn=music_respond, inputs=[textarea1, chatbot], outputs=[textarea1, chatbot, audio, hidden_ai_resp]) \
            .success(fn=trans_text, inputs=hidden_ai_resp, outputs=hidden_ai_audio)
        button6.click(fn=return_none, outputs=textarea1)
        button7.click(fn=return_none, outputs=audio)
        button3.click(fn=return_none, outputs=audio) \
            .then(fn=return_none, outputs=hidden_ai_audio) \
            .then(fn=base_model_respond, inputs=[textarea1, chatbot], outputs=[textarea1, chatbot, hidden_ai_resp]) \
            .success(fn=trans_text, inputs=hidden_ai_resp, outputs=hidden_ai_audio)
        button4.click(fn=return_none, outputs=textarea1)

    demo.launch(allowed_paths=[r"."], server_name='0.0.0.0', server_port=80)
