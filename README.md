## Local-Agent
Created by PiPiPig

## 📝 介绍
本项目旨在构建一个集成了问答（RAG）、基础语言模型、音乐下载与文本转语音（TTS）功能的交互平台。
项目使用 Gradio 构建前端界面，集成 LangChain、Chroma、F5TTS 等组件，实现了文档管理、问答检索、音乐下载以及 TTS 语音生成等完整流程。
项目结构清晰、模块划分明确，适合 LLM 工程化实践和小规模应用的快速开发。

## 📚 项目愿景
多功能集成：提供 RAG 问答、基础语言模型交互、音乐下载和 TTS 语音合成等多种功能。
易用性与扩展性：通过 Gradio 前端实现简洁交互，文档管理模块支持 URL 和 PDF 两种方式上传内容，并集成向量检索功能，便于后续扩展。
## 🚀 快速开始
```bash
# 1. 克隆项目代码到本地
git clone https://github.com/yourusername/local-agent.git

# 2. 进入项目目录
cd local-agent

# 3. 配置环境变量，将 config.env 文件中的参数修改为你的配置
# 示例：SESSION_ID、LANGSMITH_ENDPOINT、LANGSMITH_API_KEY 等

# 4. 安装项目依赖
pip install -r requirements.txt

# 5. 下载模型文件model_1200000.safetensors放到src目录下

# 6. 运行项目入口，启动 Gradio 前端
python main.py

# 7. 打开浏览器访问 http://localhost 即可体验本项目功能
```
## 📁 项目结构
```perl
local-agent/
├── config.env             # 环境变量配置文件
├── main.py                # 项目入口，加载配置并启动 Gradio 界面
├── requirements.txt       # 项目依赖包列表
├── rag_chroma_data_dir    # RAG向量数据库文件目录
└── src/                   # 源码目录
    ├── tools/             # 工具文件目录
    ├── app.py             # Gradio 前端构建与交互逻辑，包含问答、文档管理、音乐下载等功能
    ├── base_model.py      # 基础语言模型初始化与调用（支持工具链调用及中文格式化要求）
    ├── music_agent.py     # 音乐下载代理模块，通过工具链实现音乐链接分析和下载
    ├── rag.py             # RAG 系统模块，包含向量库初始化、文档上传与检索功能
    ├── session_manager.py # 会话历史管理，支持多会话存储与检索
    ├── tts.py             # 文本转语音模块，集成 F5TTS 实现中文语音合成
    ├── basic_ref_zh.wav   # 文本转语音参考人声文件
    ├── model_1200000.safetensors # 文本转语音模型文件
    └── vocab.txt          # 文本转语音词表文件  
```    
## ⚙️ 配置说明
- config.env：请根据实际情况配置项目所需环境变量，如 SESSION_ID、LANGSMITH_ENDPOINT、LANGSMITH_API_KEY、LANGSMITH_PROJECT 等。
- 在 src/tts.py 中，vocab.txt 与模型文件应与代码处于同级目录，代码中已通过 os.path 动态获取当前文件路径，并自动检查目录是否存在，若不存在则创建。
persist_dir 路径在 src/rag.py 中也采用了相对路径转绝对路径的方式，保证无论在哪个路径启动项目都能正常使用。
## 🛠 使用方法
- Gradio 前端交互：
启动后，界面提供多个 Tab 页，包括 AI 模式（基础语言模型）、RAG 模式（检索增强问答）、音乐下载模式。

- RAG 模式：支持上传 URL 或 PDF 文档，并可查看与提问相似的文档及得分。
- 音乐下载模式：输入音乐名称后，系统将调用音乐代理进行链接分析和下载，返回音乐文件。
- TTS 语音合成：所有回答生成后将经过 TTS 模块处理，生成对应的语音输出。
- 日志记录与错误处理：
项目在各个关键模块中均采用 Python 内置 logging 模块记录日志，有助于调试和生产环境的问题追踪。

## 🔧 开发与调试
- 推荐在虚拟环境中运行项目，并确保所有依赖包正确安装。
- 若遇文件路径问题，请检查当前工作目录与模块内使用的 os.path.dirname(__file__) 是否一致。
- 控制台日志会输出详细调试信息，便于快速定位问题。
## 🤝 贡献与交流
欢迎大家一起改进和完善本项目！
如果在使用过程中遇到问题或有改进建议，欢迎提交 issue 或 pull request。

## 🎉 参考链接
[Gradio](https://github.com/gradio-app/gradio)
[LangChain](https://github.com/langchain-ai/langchain)
[F5TTS](https://github.com/SWivid/F5-TTS)