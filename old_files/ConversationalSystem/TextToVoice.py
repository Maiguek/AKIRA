from gtts import gTTS
import os

class AkiraTalkgTTS:

    def __init__(self, text="", language="en", file_path="output.mp3"):
        self.text = text
        self.language = language
        self.file_path = file_path

    def talk(self, speech, save_recording=False):
        self.text = speech
        tts = gTTS(text=self.text, lang=self.language)
        tts.save(self.file_path)
        os.system(f"cvlc --play-and-exit {self.file_path}")
        if not save_recording:
            os.remove(self.file_path)


if __name__ == "__main__":
    akira_talk = AkiraTalkgTTS()
    akira_talk.talk("Hello, how are you?")
