import threading
import time
import os
import sys
import random
from perception.listening import Akira_Listen
from cognition.dialogue_manager import Akira_Chat
from action.speech_synthesis import Akira_Talk
from action.motion_controller import MotionController

sys.path.append(os.path.join(os.path.dirname(__file__), "action"))

def start_blinking(mc)
    mc.start_blink_randomly()
    blinking_thread = threading.Thread(target=mc.akira_blink_randomly)
    blinking_thread.start()
    return blinking_thread

def stop_blinking(blinking_thread):
    mc.stop_blink_randomly()
    blinking_thread.join()

def start_moving_head(mc):
    mc.start_move_head_randomly()
    moving_head_rand_thread = threading.Thread(target=mc.move_head_randomly)
    moving_head_rand_thread.start()
    return moving_head_rand_thread

def stop_moving_head(moving_head_rand_thread):
    mc.stop_move_head_randomly()
    moving_head_rand_thread.join()

def main():
    global stop_blinking, stop_head_movement
    chat = Akira_Chat()
    chat.start_ollama()

    listener = Akira_Listen()
    listener.list_microphones()
    mic_index = int(input("Enter the index of your microphone: "))
    listener.set_mic_index(mic_index)

    akira_voice_file = "action/output.wav"
    voice = Akira_Talk(output_path = akira_voice_file, spec_path = "action/spec.png")
    mc = MotionController()

    moving_head_rand_thread = start_moving_head(mc)
    blinking_thread = start_blinking(mc)

    try:
        while True:
            user_input = listener.recognize_speech()
            if user_input:
                print("User:", user_input)
                if user_input.strip().replace(" ", "").lower() == "exit":
                    break
                response = chat.generate_response(user_input)
                print("Akira:", response)
                voice.speak(response)
                mc.move_jaw_and_play(akira_voice_file)

    finally:
        print("Stopping background threads...")

        stop_blinking(blinking_thread)
        stop_moving_head(moving_head_rand_thread)
        chat.stop_ollama()
        mc.close_connection()

        print("All processes stopped safely!")

if __name__ == "__main__":
    main()
