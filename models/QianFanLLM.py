from typing import List, Optional, Tuple
from langchain_community.chat_models import QianfanChatEndpoint as ChatQianFan
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.memory import ConversationBufferMemory

class QianFanLLM:
    def __init__(self, model_name: str, api_key: str, secret_key: str, system_message: Optional[str], chat_history: Optional[List[Tuple[str, str]]] = None):
        self.api_key = api_key
        self.secret_key = secret_key
        self.model_name = model_name
        self.chat_memory = ConversationBufferMemory()
        self.model = self.initialize_model()
        self.initialize_messages(chat_history, system_message)
        self.system_message = SystemMessage(content=system_message) if system_message else None

    def initialize_model(self) -> ChatQianFan:
        return ChatQianFan(
            model_name=self.model_name,
            api_key=self.api_key,
            secret_key=self.secret_key
        )

    def initialize_messages(self, chat_history: Optional[List[Tuple[str, str]]], system_message: Optional[str]):
        if system_message:
            self.chat_memory.chat_memory.add_message(SystemMessage(content=system_message))
        if chat_history:
            for role, message in chat_history:
                if role == "user":
                    self.chat_memory.chat_memory.add_message(HumanMessage(content=message))
                elif role == "assistant":
                    self.chat_memory.chat_memory.add_message(AIMessage(content=message))

    def chat_with_memory(self, user_message: str) -> str:
        self.chat_memory.chat_memory.add_message(HumanMessage(content=user_message))
        try:
            response = self.model.invoke(self.chat_memory.chat_memory.messages)
            assistant_reply = response.content
            self.chat_memory.chat_memory.add_message(AIMessage(content=assistant_reply))
        except Exception as e:
            raise RuntimeError(f"Error generating response: {e}")

        return assistant_reply

    def chat(self, user_message: str) -> str:
        try:
            messages = [self.system_message, HumanMessage(content=user_message)]
            response = self.model.invoke(messages)
            assistant_reply = response.content
        except Exception as e:
            raise RuntimeError(f"Error generating response: {e}")
        return assistant_reply

    def get_chat_history(self) -> List[Tuple[str, str]]:
        history = []
        for msg in self.chat_memory.chat_memory.messages:
            if isinstance(msg, HumanMessage):
                history.append(("user", msg.content))
            elif isinstance(msg, AIMessage):
                history.append(("assistant", msg.content))
        return history
