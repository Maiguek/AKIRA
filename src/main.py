import threading
import time
import random
from perception.listening import Akira_Listen
from cognition.dialogue_manager import Akira_Chat
from action.speech_synthesis import Akira_Talk
from action.motion_controller import MotionController

# Threading events for stopping background threads
stop_blinking = threading.Event()
stop_head_movement = threading.Event()

def blink_randomly(mc):
    """ Makes Akira blink at random intervals until stopped. """
    while not stop_blinking.is_set():
        time.sleep(random.uniform(3, 7))  # Wait between 3 to 7 seconds
        mc.blink_eyes()

def move_head(mc):
    """ Runs head movement in a separate thread until stopped. """
    while not stop_head_movement.is_set():
        mc.move_head_randomly()

def main():
    global stop_blinking, stop_head_movement
    chat = Akira_Chat()
    chat.start_ollama()

    listener = Akira_Listen()
    listener.list_microphones()
    mic_index = int(input("Enter the index of your microphone: "))
    listener.set_mic_index(mic_index)

    voice = Akira_Talk(url_path="../../url.txt")
    mc = MotionController()

    # Start blinking and head movement threads
    blink_thread = threading.Thread(target=blink_randomly, args=(mc,))
    head_thread = threading.Thread(target=move_head, args=(mc,))
    blink_thread.start()
    head_thread.start()

    try:
        while True:
            user_input = listener.recognize_speech()
            if user_input:
                print("User:", user_input)
                if user_input.strip().replace(" ", "").lower() == "exit":
                    break
                response = chat.generate_response(user_input)
                print("Akira:", response)
                akira_voice_file = voice.speak(response)
                mc.move_jaw_and_play(akira_voice_file)

    finally:
        print("Stopping background threads...")

        mc.stop_head()

        # Stop blinking and head movement **BEFORE** closing the serial port
        stop_blinking.set()
        stop_head_movement.set()

        blink_thread.join()
        head_thread.join()

        # Now it's safe to close the serial connection
        chat.stop_ollama()
        mc.close_connection()

        print("All processes stopped safely!")

if __name__ == "__main__":
    main()
