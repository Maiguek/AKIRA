import speech_recognition as sr

# Inspired and adapted from https://www.geeksforgeeks.org/python-speech-recognition-module/

class Listening():
    def __init__(self):
        self.r = sr.Recognizer()

    def hear(self):
        with sr.Microphone() as source:
            audio_text = self.r.listen(source)            
            try:
                return self.r.recognize_google(audio_text)
            except:
                return None # speech was not recognized
            

