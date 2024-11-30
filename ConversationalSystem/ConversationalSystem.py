import pandas as pd
from LanguageGeneration import AkiraChatbot
from SpeechRecognition import Listening

# Define important paths and initialize modules
user_info_path = "userInfo.csv"
conversation_history_path = "ConversationHistory.txt"

class ConversationalSystem:
    def __init__(self, user_info_path, conversation_history_path, model_path, tokenizer_path, executable_path):
        self.user_info_path = user_info_path
        self.conversation_history_path = conversation_history_path
        self.listener = Listening()
        self.chatbot = AkiraChatbot(model_path, tokenizer_path, executable_path)

    def read_user_info(self):
        return pd.read_csv(self.user_info_path)

    def generate_prompt(self, user_info, conversation_history):
        name, age, emotion, occupation, likes, dislikes = user_info

        prompt = "You are Akira, a humanoid robot designed for joyful and meaningful interactions. You are friendly, curious, and love to ask questions to learn more about the people you talk to."
        prompt += f"\nThe person in front of you is {age} years old, likes {likes}, dislikes {dislikes}, and is {occupation}. {name} feels {emotion}"
        prompt += "\n\nConversation:"
        prompt += conversation_history
        prompt += "\nAkira:"

        return prompt

    def read_conversation_history(self):
        with open(self.conversation_history_path, "r") as file:
            lines = file.readlines()

        return lines

    def get_seq_len(self, prompt, extra_tokens=150):
        # This is very important as it needs to be large enough so Akira can write completely his sentence, but small enough so the computer can resist the prompt.
        return len(prompt.replace("\n", " ").replace('"', '').split()) + extra_tokens

    def get_last_k_records(self, k=3):
        lines = self.read_conversation_history()
        return lines[-k:]

    def update_conversation(self, new_message):
        with open(self.conversation_history_path, "a") as file:
            file.write(new_message + "\n")

    def listen_and_respond(self):
        user_info = self.read_user_info()
        user_speech = self.listener.hear()

        if user_speech:
            if user_info["Name"].isnull().values.any():
                name = "User"
            else:
                name = user_info["Name"][0]

            user_speech = f"{name}: {user_speech}"
            self.update_conversation(user_speech)

            last_k_records = self.get_last_k_records()
            conversation_history = "".join(last_k_records)

            prompt = self.generate_prompt(user_info.iloc[0], conversation_history)
            seq_len = self.get_seq_len(prompt)

            akira_response = self.chatbot.generate_response(prompt, seq_len)
            self.update_conversation(f"Akira: {akira_response}")

            return user_speech, akira_response
        return None, None

# Main part Conversational System
if __name__ == "__main__":
    model_path = "/home/maiguek/Documents/LlamaModels/DownloadedWeights/Llama3.2-3B-Instruct-int4-qlora-eo8/llama3_2.pte"
    tokenizer_path = "/home/maiguek/Documents/LlamaModels/DownloadedWeights/Llama3.2-3B-Instruct-int4-qlora-eo8/tokenizer.model"
    executable_path = "../LlamaModels/executorch/cmake-out/examples/models/llama/llama_main"

    conversational_system = ConversationalSystem(user_info_path, conversation_history_path, model_path, tokenizer_path, executable_path)

    while True:
        user_info = conversational_system.read_user_info()
        
        # TODO: Make subtle movements (waiting/listening) ALSO: on the background, trying to make eye contact, but taking care of the gaze

        user_speech, akira_response = conversational_system.listen_and_respond()

        # TODO:  Add a feature to the LanguageGeneration for analyzing the ConversationHistory and Determining likes, dislikes, occupation, and age to update the user information.

        # TODO:  Produce Akira's voice text_answer
        #   while doing so move jaw
        
        # TODO:  Produce Gesture movements

        # TODO:  Analyze user's face and emotion

        # TODO:  Reproduce Akira's current facial emotion
