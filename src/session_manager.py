from langchain_community.chat_message_histories import ChatMessageHistory


class SessionManager:
    """
    管理共享的会话历史记录
    """

    def __init__(self):
        self.store = {}

    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]
