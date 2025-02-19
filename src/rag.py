import os

import bs4
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_core.runnables import RunnableWithMessageHistory
from src.session_manager import SessionManager


def initialize_rag_system(session_manager: SessionManager):
    """
    初始化 RAG 系统，包括向量库、检索器、问题重构提示和问答链，
    并返回支持会话历史管理的可调用链与向量库实例。
    """

    llm = ChatOllama(model="qwen2.5:14b", temperature=0)
    embeddings = OllamaEmbeddings(model="all-minilm:l6-v2")
    persist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../rag_chroma_data_dir'))
    if not os.path.exists(persist_dir):
        os.makedirs(persist_dir)
    vectorstore = Chroma(
        collection_name="my_collection",
        embedding_function=embeddings,
        persist_directory=persist_dir
    )
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    system_prompt = (
        "You are an assistant for question-answering tasks. You need to understand and combine the "
        "following context to answer questions before each answer. If you don't know the answer, say that you don't know. "
        "Please answer in Chinese every time. Respond in plain text format only. Do not use any MarkDown syntax including "
        "asterisks (*), backticks (`), hashtags (#), brackets ([]), or any other formatting symbols. Present all content "
        "as simple, unformatted text with clear paragraph breaks when needed.\n\n{context}"
    )
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    return RunnableWithMessageHistory(
        rag_chain,
        session_manager.get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    ), vectorstore


def add_document_by_url(url: str, vectorstore: Chroma, classname: str):
    """
    通过给定 URL 和 CSS 类名加载网页内容，拆分后添加至向量库。
    """
    from langchain_community.document_loaders import WebBaseLoader
    loader = WebBaseLoader(
        web_paths=[url],
        bs_kwargs=dict(parse_only=bs4.SoupStrainer(class_=classname)),
    )
    new_docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
    new_splits = splitter.split_documents(new_docs)
    vectorstore.add_documents(new_splits)


async def add_document_by_pdf(pdf_path: str, vectorstore: Chroma):
    """
    加载 PDF 文件内容，拆分后添加至向量库。
    """
    from langchain_community.document_loaders import PyPDFLoader
    loader = PyPDFLoader(pdf_path)
    pages = []
    async for page in loader.alazy_load():
        pages.append(page)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
    new_splits = splitter.split_documents(pages)
    vectorstore.add_documents(new_splits)
