import os
import csv
import shutil
import pandas as pd
from LanguageGeneration import AkiraChatbot
from SpeechRecognition import Listening
from TextToVoice import AkiraTalkgTTS as AkiraTalk


class ConversationalSystem:
    def __init__(self, model_path, tokenizer_path, executable_path, user_info_path="user.csv", conversation_history_path="chat.txt"):
        self.listener = Listening()
        self.talker = AkiraTalk()
        self.chatbot = AkiraChatbot(model_path, tokenizer_path, executable_path)

        base_dir = os.getcwd() + "/ConversationalSystem/data/"
        self.user_info_path = os.path.join(base_dir, user_info_path)
        self.conversation_history_path = os.path.join(base_dir, conversation_history_path)

        # Ensure base directory exists
        os.makedirs(base_dir, exist_ok=True)

        # Conversation History Handling
        folder_old_conversations = os.path.join(base_dir, "old_conversations")
        os.makedirs(folder_old_conversations, exist_ok=True)
        num_files = len([name for name in os.listdir(folder_old_conversations) if os.path.isfile(os.path.join(folder_old_conversations, name))])
        move_file_path = os.path.join(folder_old_conversations, f"conversation_{num_files + 1}.txt")

        if os.path.exists(self.conversation_history_path):
            shutil.move(self.conversation_history_path, move_file_path)

        # Create empty conversation history file
        try:
            open(self.conversation_history_path, "w").close()
        except IOError as e:
            print(f"Error creating conversation history file: {e}")

        # User Info Handling
        folder_old_user_info = os.path.join(base_dir, "old_user_info")
        os.makedirs(folder_old_user_info, exist_ok=True)
        num_files = len([name for name in os.listdir(folder_old_user_info) if os.path.isfile(os.path.join(folder_old_user_info, name))])
        move_file_path = os.path.join(folder_old_user_info, f"user_info_{num_files + 1}.csv")

        if os.path.exists(self.user_info_path):
            shutil.move(self.user_info_path, move_file_path)

        # Create empty user info CSV
        headers = ["Name", "Age", "Emotion", "Occupation", "Likes", "Dislikes"]
        empty_user = {header: "" for header in headers}
        try:
            with open(self.user_info_path, mode="w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=headers)
                writer.writeheader()
                writer.writerow(empty_user)
        except IOError as e:
            print(f"Error creating user info CSV: {e}")
        


    def read_user_info(self):
        return pd.read_csv(self.user_info_path)

    def generate_prompt(self, user_info, conversation_history):
        name, age, emotion, occupation, likes, dislikes = user_info

        prompt = "You are Akira, a humanoid robot designed for joyful and meaningful interactions. You are friendly, curious, and love to ask questions to learn more about the people you talk to."
        prompt += f"\nThe person in front of you is {age} years old, likes {likes}, dislikes {dislikes}, and is {occupation}. {name} feels {emotion}\n"
        #prompt += f"\nInstructions: Use <ioc> for initialization of conversation, and <eoc> for end of conversation for both {name} and Akira. DO NOT include actions with **"
        prompt += f"\nInstructions: DO NOT include actions with *action*, DO NOT produce too long answers."
        prompt += "\n\nConversation:"
        prompt += conversation_history
        #prompt += "\nAkira:"

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
        if len(lines) < k:
            return lines
        return lines[-k:]

    def update_conversation(self, new_message):
        with open(self.conversation_history_path, "a") as file:
            file.write(new_message.strip() + "\n")

    def listen_and_respond(self):
        user_info = self.read_user_info()
        user_speech = self.listener.hear()

        if user_speech:
            if user_info["Name"].isnull().values.any():
                name = "User"
            else:
                name = user_info["Name"][0]

            #user_speech = f"{name}: <ioc>{user_speech}<eoc>"
            user_speech = f"{name}: {user_speech}"
            print("User speech:", user_speech)
            self.update_conversation(user_speech)

            last_k_records = self.get_last_k_records()
            conversation_history = "".join(last_k_records)

            
            prompt = self.generate_prompt(user_info.iloc[0], conversation_history)
            seq_len = self.get_seq_len(prompt)
            print("Prompt:", prompt)

            try:
                print("Generating response...")
                akira_response, observer_data = self.chatbot.generate_response(prompt, seq_len)
            except Exception as e:
                print(f"Error generating response: {e}")
                akira_response, observer_data = None, None

            if akira_response:
                self.update_conversation(f"Akira: {akira_response}")

            return user_speech, akira_response
        return None, None
    
    def talk(self, speech):
        self.talker.talk(speech)

# For testing Main Part of how it should work
if __name__ == "__main__":
    model_path = "/home/maiguek/Documents/LlamaModels/DownloadedWeights/Llama3.2-3B-Instruct-int4-qlora-eo8/llama3_2.pte"
    tokenizer_path = "/home/maiguek/Documents/LlamaModels/DownloadedWeights/Llama3.2-3B-Instruct-int4-qlora-eo8/tokenizer.model"
    executable_path = "../LlamaModels/executorch/cmake-out/examples/models/llama/llama_main"

    conversational_system = ConversationalSystem(model_path, tokenizer_path, executable_path)

    while True:
        
        #user_info = conversational_system.read_user_info()

        print("\n>>Usuario habla...")
        user_speech, akira_response = conversational_system.listen_and_respond()
        print(">>Akira Habla...\n")

        if user_speech and akira_response:
            print(f"User: {user_speech}")
            print(f"Akira: {akira_response}")
            conversational_system.talk(akira_response)
            print()
            print()

        
















        # TODO: Make subtle movements (waiting/listening) ALSO: on the background, trying to make eye contact, but taking care of the gaze

        # TODO:  Add a feature to the LanguageGeneration for analyzing the ConversationHistory and Determining likes, dislikes, occupation, and age to update the user information.

        # TODO:  While producing Akira's voice text_answer, add a feature to move jaw
        
        # TODO:  Produce Gesture movements

        # TODO:  Analyze user's face and emotion

        # TODO:  Reproduce Akira's current facial emotion
