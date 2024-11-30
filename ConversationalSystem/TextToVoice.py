from gtts import gTTS
import os

class AkiraTalk:

    def __init__(self, text="", language="en"):
        self.text = text
        self.language = language

    def talk(self, speech):
        self.text = speech
        tts = gTTS(text=self.text, lang=self.language)
        tts.save("output.mp3")
        os.system("start output.mp3")