from perception.listening import Akira_Listen
from cognition.dialogue_manager import Akira_Chat
#from action.speech_synthesis import speak_and_move

def main():
    chat = Akira_Chat()
    chat.start_ollama()

    listener = Akira_Listen()
    listener.list_microphones()
    mic_index = int(input("Enter the index of your microphone: "))
    listener.set_mic_index(mic_index)
    try:
        while True:
            user_input = listener.recognize_speech()
            if user_input:
                print("User:", user_input)
                if user_input.strip().replace(" ", "").lower() == "exit":
                    break
                response = chat.generate_response(user_input)
                #speak_and_move(response)
                print("Akira:", response)
    finally:
        chat.stop_ollama()

if __name__ == "__main__":
    main()
