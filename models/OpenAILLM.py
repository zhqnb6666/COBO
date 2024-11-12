from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from typing import List, Tuple, Optional, Dict


def choose_model(model_name: str, api_key: str, base_url: str) -> ChatOpenAI:
    supported_models = {
        "GPT_3_5_TURBO": "gpt-3.5-turbo",
        "GPT_4_32K": "gpt-4-32k",
        "GPT_4_O": "gpt-4",
        "GPT_4_O_MINI": "gpt-4-mini"
    }
    model_name_mapped = supported_models.get(model_name.upper())
    if not model_name_mapped:
        raise ValueError(f"Unknown model name: {model_name}")

    return ChatOpenAI(model_name=model_name_mapped, openai_api_key=api_key, base_url=base_url)


class OpenAILLM:
    def __init__(self, model_name: str, system_message: Optional[str], chat_history: Optional[List[Tuple[str, str]]] = None):
        self.api_key = "sk-6hMxxGzo2ZT6WzKXBa9cB82d964e4cAe9eE0F95d70C1Ba0e"
        self.base_url = "https://xiaoai.plus/v1"
        self.model = choose_model(model_name, self.api_key, self.base_url)
        self.chat_memory = ConversationBufferMemory()
        self.initialize_messages(chat_history, system_message)
        self.system_message = SystemMessage(content=system_message) if system_message else None

    def initialize_messages(self, chat_history: Optional[List[Tuple[str, str]]], system_message: Optional[str]):
        if system_message:
            self.chat_memory.chat_memory.add_message(SystemMessage(content=system_message))
        if chat_history:
            for role, message in chat_history:
                if role == "user":
                    self.chat_memory.chat_memory.add_message(HumanMessage(content=message))
                elif role == "assistant":
                    self.chat_memory.chat_memory.add_message(AIMessage(content=message))


    def chat_with_memory(self, message: str) -> str:
        self.chat_memory.chat_memory.add_message(HumanMessage(content=message))
        try:
            response = self.model.invoke(self.chat_memory.chat_memory.messages)
            assistant_reply = response.content
            self.chat_memory.chat_memory.add_message(AIMessage(content=assistant_reply))
        except Exception as e:
            raise RuntimeError(f"Error generating response: {e}")

        return assistant_reply

    def chat(self, message: str) -> str:
        try:
            messages = [self.system_message, HumanMessage(content=message)]
            response = self.model.invoke(messages)
            assistant_reply = response.content
        except Exception as e:
            raise RuntimeError(f"Error generating response: {e}")
        return assistant_reply

    def get_chat_history(self) -> List[Dict[str, str]]:
        history = []
        for msg in self.chat_memory.chat_memory.messages:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
        return history
