import speech_recognition as sr

# Inspired and adapted from https://www.geeksforgeeks.org/python-speech-recognition-module/

class Listening():
    def __init__(self):
        self.r = sr.Recognizer()

    def hear(self):
        mic_index = 24  # Blue Microphone
        with sr.Microphone(device_index=mic_index) as source:
            print("Adjusting for ambient noise...")  
            self.r.adjust_for_ambient_noise(source)  # Helps in noisy environments
            audio_text = self.r.listen(source)
            
            try:
                return self.r.recognize_google(audio_text)
            except sr.UnknownValueError:
                return None
            except sr.RequestError:
                return None

if __name__ == "__main__":
    print("Listening...")
    listener = Listening()
    print(listener.hear())
    #print(sr.Microphone.list_microphone_names())

            

