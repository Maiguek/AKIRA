"""
This code will communicate with my laptop to run F5-TTS and then
retrive the audio generated with my voice clonned.

For this I need to open on my laptop a server which will receive
any request by this script to clone my voice and return the
clonned voice.
"""
import os
import requests
from playsound import playsound


class Akira_Talk:
    def __init__(self, url_path = "../../../url.txt"):
        
        if not os.path.exists(url_path):
            raise FileNotFoundError(f"URL file not found: {url_path}")
                
        with open(url_path, "r") as f:
            self.url = f.read().strip()

    def speak(self, gen_text, play=False):
        text = {"gen_text": gen_text}

        try:
            response = requests.post(self.url, json=text)
            response.raise_for_status()

            with open("output.wav", "wb") as f:
                f.write(response.content)
            print("Audio file saved as output.wav")

        except Exception as e:
            print("Error:", e)

        if play:
            playsound("output.wav")

        return os.path.join(os.getcwd(), "output.wav")
        


if __name__ == "__main__":
    voice = Akira_Talk()

    print(voice.speak("Hey, how are you? My name is Akira!"))







    
            
