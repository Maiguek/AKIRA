import threading
import time
import os
import sys
import random

from perception.listening import Akira_Listen
from perception.vision import Akira_See
from cognition.dialogue_manager import Akira_Chat
from action.speech_synthesis import Akira_Talk
from action.motion_controller import MotionController
from action.music_manager import MusicPlayer

sys.path.append(os.path.join(os.path.dirname(__file__), "action"))


def start_blinking(mc):
    mc.start_blink_randomly()
    blinking_thread = threading.Thread(target=mc.akira_blink_randomly)
    blinking_thread.start()
    return blinking_thread

def stop_blinking(mc, blinking_thread):
    mc.stop_blink_randomly()
    blinking_thread.join()

def start_moving_head_rand(mc):
    mc.start_move_head_randomly()
    moving_head_rand_thread = threading.Thread(target=mc.akira_move_head_randomly)
    moving_head_rand_thread.start()
    return moving_head_rand_thread

def stop_moving_head_rand(mc, moving_head_rand_thread):
    mc.stop_move_head_randomly()
    moving_head_rand_thread.join()

def start_moving_hands_rand(mc, only_wrist=False):
    mc.start_move_hands_randomly()
    moving_hands_rand_thread = threading.Thread(target=mc.akira_move_hands_randomly, args=(only_wrist,))
    moving_hands_rand_thread.start()
    return moving_hands_rand_thread

def stop_moving_hands_rand(mc, moving_hands_rand_thread):
    mc.stop_move_hands_randomly()
    moving_hands_rand_thread.join()

def start_moving_arms_rand(mc):
    mc.start_move_arms_randomly()
    moving_arms_rand_thread = threading.Thread(target=mc.akira_move_arms_randomly)
    moving_arms_rand_thread.start()
    return moving_arms_rand_thread

def stop_moving_arms_rand(mc, moving_arms_rand_thread):
    mc.stop_move_arms_randomly()
    moving_arms_rand_thread.join()

def start_looking_at(akira_vision):
    akira_vision.start_looking_at()
    looking_at_thread = threading.Thread(target=akira_vision.look_at_face_stereo)
    looking_at_thread.start() 
    return looking_at_thread

def stop_looking_at(akira_vision, looking_at_thread):
    akira_vision.stop_looking_at()
    looking_at_thread.join()
    
def main():
    chat = Akira_Chat()
    chat.start_ollama()

    listener = Akira_Listen()
    listener.list_microphones()
    mic_index = int(input("Enter the index of your microphone: "))
    listener.set_mic_index(mic_index)

    akira_voice_file = "action/output.wav"
    voice = Akira_Talk(output_path = akira_voice_file, spec_path = "action/spec.png")
    mc = MotionController(verbose=False)

    akira_vision = Akira_See(motion_controller=mc)

    music_player = MusicPlayer()

    blinking_thread = start_blinking(mc)
    moving_hands_rand_thread = start_moving_hands_rand(mc)
    moving_arms_rand_thread = start_moving_arms_rand(mc)
    moving_head_rand_thread = start_moving_head_rand(mc)
 
    try:
        while True:
            # Pay attention mode
            stop_moving_head_rand(mc, moving_head_rand_thread)
            mc.neck_rest()
            stop_moving_hands_rand(mc, moving_hands_rand_thread)
            stop_moving_arms_rand(mc, moving_arms_rand_thread)
            mc.arms_rest()
            looking_at_thread = start_looking_at(akira_vision)
            
            user_input = listener.recognize_speech()
            if user_input:
                # Akira asks for confirmation: or says something by default
                print("User:", user_input)
                if "exit" in user_input.lower():
                    break

                # Take a photo of what is happening
                image_input = akira_vision.take_photo()

                # Akira will appear to be thinking while we generate an answer
                stop_blinking(mc, blinking_thread)
                stop_looking_at(akira_vision, looking_at_thread)
                music_player.play_music()
                mc.akira_close_eyes()
                mc.akira_close_hand(arduino="left")
                mc.akira_index_up(arduino="right")
                moving_hands_rand_thread = start_moving_hands_rand(mc, only_wrist=True)
                moving_arms_rand_thread = start_moving_arms_rand(mc)
                moving_head_rand_thread = start_moving_head_rand(mc)

                # Get a description ow fhat is happening
                description = akira_vision.describe_what_akira_sees(
                    image_input=image_input,
                    eliminate_photo=False,
                    annotate_photo=True
                    )

                response = chat.generate_response(user_input, description) # generates text to speak
                print("Akira:", response)
                voice.speak(response) # clones the voice

                music_player.stop_music()
                
                # Akira stops thinking mode
                mc.akira_open_eyes()
                blinking_thread = start_blinking(mc)
                mc.akira_half_close_hand("left")
                mc.akira_half_close_hand("right")
                
                mc.move_jaw_and_play(akira_voice_file) # reproduces audio and moves jaw

    finally:
        try:
            music_player.stop_music()
        except Exception as e:
            print(e)
            
        voice.speak("Thanks for talking with me, see you next time.")
        mc.move_jaw_and_play(akira_voice_file)
        print("Stopping background threads...")

        # add for putting all servos in their rest positions before closing connection
        try:
            stop_looking_at(akira_vision, looking_at_thread)
        except Exception as e:
            print(e)
        try:
            stop_moving_arms_rand(mc, moving_arms_rand_thread)
        except Exception as e:
            print(e)
        try:
            stop_moving_hands_rand(mc, moving_hands_rand_thread)
        except Exception as e:
            print(e)
        try:
            stop_moving_head_rand(mc, moving_head_rand_thread)
        except Exception as e:
            print(e)
        try:
            stop_blinking(mc, blinking_thread)
        except Exception as e:
            print(e)
            
        chat.stop_ollama()
        mc.close_connection()

        print("All processes stopped safely!")

if __name__ == "__main__":
    main()
    
    
