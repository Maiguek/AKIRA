import subprocess
import re
import json

class AkiraChatbot:
    def __init__(self, model_path, tokenizer_path, executable_path):
        self.model_path = model_path
        self.tokenizer_path = tokenizer_path
        self.executable_path = executable_path

    def generate_response(self, prompt, seq_len):
        command = [
            executable_path,
            f"--model_path={self.model_path}",
            f"--tokenizer_path={self.tokenizer_path}",
            f"--prompt={prompt}",
            f"--seq_len={seq_len}"
        ]

        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True).stdout
            result = result[len(prompt):]
            akiras_response = re.findall(r"Akira: <ioc>(.*?)<eoc>", result, re.DOTALL)[0]

            observer_match = re.search(r"PyTorchObserver\s*({.*?})", result)
            if observer_match:
                observer_data = json.loads(observer_match.group(1))
            
        except subprocess.CalledProcessError as e:
            print("Error:")
            print(e.stderr)

            akiras_response, observer_data = None, None
        
        return akiras_response, observer_data
    
    # TODO: Create a method for analyzing the text and updating the user information. Do this while listening to the person.
    


if __name__ == "__main__":
    # I am using Llama3.2-3B-Instruct-int4-qlora-eo8 as the main model for generting responses from Akira
    model_path = "/home/maiguek/Documents/LlamaModels/DownloadedWeights/Llama3.2-3B-Instruct-int4-qlora-eo8/llama3_2.pte"
    tokenizer_path = "/home/maiguek/Documents/LlamaModels/DownloadedWeights/Llama3.2-3B-Instruct-int4-qlora-eo8/tokenizer.model"
    # Prompts will follow a specific format, in which I will combine information about Akira and the user, 
    # instructions on how to produce a response, and the conversation history.
    # Example prompt:
    prompt = """
    You are Akira, a humanoid robot designed for joyful and meaningful interactions. You are friendly, curious, and love to ask questions to learn more about the people you talk to.

    Conversation:
    Akira: <ioc>"Hello! What's your name?"<eoc>
    Miguel: <ioc>"My name is Miguel."<eoc>
    Akira: <ioc>"My name is Akira. I am pleased to meet you, Miguel!"<eoc>
    Miguel: <ioc>"Hi Akira! It is my pleasure to meet you."<eoc>
    """
    seq_len = len(prompt.replace("\n", " ").replace('"', '').split()) + 200 # I have to check really which values for the seq_len are appropriate
    executable_path = "../LlamaModels/executorch/cmake-out/examples/models/llama/llama_main"

    akira_chatbot = AkiraChatbot(model_path, tokenizer_path, executable_path)
    akiras_response, observer_data = akira_chatbot.generate_response(prompt, seq_len)

    print(akiras_response)