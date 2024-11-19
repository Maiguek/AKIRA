import pandas as pd
from LanguageGeneration import AkiraChatbot
from SpeechRecognition import Listening

# Define important paths and initialize modulos
user_info_path = "userInfo.csv"
conversation_history_path = "ConversationHistory.txt"

Listener = Listening()

model_path = "/home/maiguek/Documents/LlamaModels/DownloadedWeights/Llama3.2-3B-Instruct-int4-qlora-eo8/llama3_2.pte"
tokenizer_path = "/home/maiguek/Documents/LlamaModels/DownloadedWeights/Llama3.2-3B-Instruct-int4-qlora-eo8/tokenizer.model"
executable_path = "../LlamaModels/executorch/cmake-out/examples/models/llama/llama_main"
ChatBot = AkiraChatbot(model_path, tokenizer_path, executable_path)

# Some helper functions for functionality
def read_user_info(path=user_info_path):
    return pd.read_csv(path)

def generate_prompt(user_info, conversation_history):
    name, age, emotion, ocuppation, likes, dislikes = user_info

    prompt = "You are Akira, a humanoid robot designed for joyful and meaningful interactions. You are friendly, curious, and love to ask questions to learn more about the people you talk to."
    prompt += f"\nThe person in front of you is {age} years old, likes {likes}, dislikes {dislikes}, and is {ocuppation}. {name} feels {emotion}"
    prompt += "\n\nConversation:"
    prompt += conversation_history
    prompt += "\nAkira:"

    return prompt

def read_conversation_history(path=conversation_history_path):
    with open(path, "r") as file:
        lines = file.readlines()

    return lines

def get_seq_len(prompt, extra_tokens=100):
    # This is very important as it needs to be large enough so Akira can write completely his sentence, but small enough so the computer can resist the prompt.
    return len(prompt.replace("\n", " ").replace('"', '').split()) + extra_tokens

def get_last_k_records(path=conversation_history_path, k=3):
    lines = read_conversation_history(path)
    return lines[:-k]

def update_conversation(new_message, path=conversation_history_path):
    with open(path, "wb") as file:
        file.write(new_message)


# Main part Conversational System
while True:
    user_info = read_user_info()
    
    # TODO: Make subtle movements (waiting/listening) ALSO: on the background, trying to make eye contact, but taking care of the gaze

    User_Speech = Listener.hear()

    if User_Speech:
        if user_info["Name"] is None:
            name = "User"
        else:
            name = user_info["Name"]

        # This is the message from the user to Akira
        User_Speech = "name: " + User_Speech

        # We update the current conversation with the user's message
        update_conversation(User_Speech)

        # We could either read all the conversation so far or extract just the last k messages between Akira and the User
        # conversation_history = read_conversation_history().strip()
        last_k_records = get_last_k_records().strip()

        # We prepare our prompt to generate the message from Akira
        prompt = generate_prompt(user_info, last_k_records)
        seq_len = get_seq_len(prompt)

        Akira_text_answer = AkiraChatbot.generate_response(prompt, seq_len)

        # We update the conversation history
        update_conversation(Akira_text_answer)

        # TODO:  Add a feature to the LanguageGeneration for analyzing the ConversationHistory and Determining likes, dislikes, ocuppation, and age to update the user information.

        # TODO:  Produce Akira's voice text_answer
        #   while doing so move jaw
        
        # TODO:  Produce Gesture movements

        # TODO:  Analyze user's face and emotion

        # TODO:  Reproduce Akira's current facial emotion








    