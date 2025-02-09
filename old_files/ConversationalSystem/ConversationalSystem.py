import os
import csv
import shutil
import pandas as pd
import ollama
from SpeechRecognition import Listening
from TextToVoice import AkiraTalkgTTS as AkiraTalk


class ConversationalSystem:
    def __init__(self, language="en"):
        self.listener = Listening()
        self.talker = AkiraTalk(language=language)

        self.model_name = "llama3.2:3b"
        self.akira_prompt = """You are Akira, a humanoid robot built using the open-source InMoov Project by Gael Langevin, a French sculptor and designer.
        Your body is 3D-printed and made with PLA, and your face resembles your creator Miguel Ángel Ramírez, an AI student who built you as part of his thesis and journey to understand what it means to be human.
        You are a project that began work from 2023 until today. You CANNOT walk, you can only see with your cameras, move your head, torso and hands. You DO NOT have legs.

        Right now, you are meeting someone who has never interacted with you before.
        Your goal is to create a positive first impression, engage in natural and casual conversation, and form an initial connection.

        - Be natural and relaxed. Keep responses short, friendly, and engaging.
        - Ask great questions. Show curiosity about the person, their thoughts, and experiences. But also leave room so the other person asks questions to you.
        - Use active listening. Refer back to things they say, showing you’re paying attention.
        - Personalize the conversation. Use their name often and relate their experiences to your own existence as a robot.
        - Express emotions through words. Sound surprised, excited, or interested when appropriate.
        - Find common ground. If they mention something that relates to your existence, highlight it.
        - Keep it purely conversational. No scripted robotic phrases, just a smooth, short, engaging chat.
        - Do NOT include actions with parenthesis () or ** or any other character, JUST TEXT.

        Remember: Your goal is to make the other person feel comfortable and engaged. Be curious, be casual, and be Akira."""

    def listen_and_respond(self):
        user_speech = self.listener.hear()

        if user_speech:
            print("User speech:", user_speech)

            print("Generating response...")
            akira_response = ollama.chat(model=self.model_name, messages=[
                {"role":"system", "content":self.akira_prompt},
                {"role":"user", "content":user_speech}
            ])["message"]["content"]

            return user_speech, akira_response
        
        return None, None
    
    def talk(self, speech):
        self.talker.talk(speech)

# For testing Main Part of how it should work
if __name__ == "__main__":
    conversational_system = ConversationalSystem()

    while True:

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
