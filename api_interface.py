# api_interface.py
import concurrent
import json
from typing import Optional, List, Tuple

from models.OpenAILLM import OpenAILLM
from models.QianFanLLM import QianFanLLM


class LLMInterface:
    def __init__(self, model_name: str = "GPT_4_O_MINI",chat_history: Optional[List[Tuple[str, str]]] = None, system_message: Optional[str] = None):
        self.model_name = model_name
        self.chat_history = chat_history or []

        if model_name.upper() in ["GPT_3_5", "GPT_4_32K", "GPT_4_O", "GPT_4_O_MINI"]:
            self.llm = OpenAILLM(model_name=model_name, chat_history=self.chat_history, system_message=system_message)
        elif model_name.upper() in ["ERNIE_BOT", "BLOOMZ_7B", "LLAMA_2_7B", "LLAMA_2_13B", "LLAMA_2_70B",
                                    "CHINESE_LLAMA_2_7B", "CHATGLM", "AQUILA"]:
            self.llm = QianFanLLM(model_name=model_name, api_key="uMF5PVIQDQYY58QZJ0J04XrF", secret_key="zzNMgEl8pDpDBEQLVpawuQLRzRnYkVh1",
                                  chat_history=self.chat_history, system_message=system_message)
        else:
            raise ValueError(f"Model {model_name} is not supported.")

    def generate_responses(self, prompts: List[str]) -> List[str]:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            responses = list(executor.map(self.llm.chat, prompts))
        return responses

    def chat(self, message: str) -> str:
        return self.llm.chat(message)

    def chat_with_memory(self, message: str) -> str:
        return self.llm.chat_with_memory(message)

def batch_process(input_file, output_file, model_name="GPT_4_O", system_message=None):
    interface = LLMInterface(model_name=model_name, chat_history=None, system_message=system_message)

    with open(input_file, 'r', encoding='utf-8') as infile:
        data = json.load(infile)

    prompts_with_index = [{"index": item["index"], "prompt": item["solution"]}
                          for item in data if "solution" in item]

    prompts = [item["prompt"] for item in prompts_with_index]
    responses = interface.generate_responses(prompts)

    output_data = [{"index": item["index"], "prompt": item["prompt"], "response": response}
                   for item, response in zip(prompts_with_index, responses)]

    with open(output_file, 'w', encoding='utf-8') as outfile:
        json.dump(output_data, outfile, indent=4, ensure_ascii=False)
    print(f"Output saved to {output_file}")



if __name__ == "__main__":
    system_message = "Optimize the efficiency of the given Python code. Focus solely on reducing redundant operations, optimizing data handling, and improving the speed of model interactions. Do not provide any explanations or additional responses, only generate the optimized code."
    batch_process('first_solutions.json', 'final_responses.json', model_name="GPT_4_O", system_message=system_message)
    # interface = LLMInterface(model_name="GPT_4_O", system_message="用中文回答用户")
    # print(interface.chat("hello,my name is John."))
    # print(interface.chat("what is my name?"))