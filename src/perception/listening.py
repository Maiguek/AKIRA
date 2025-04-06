import speech_recognition as sr
import pyaudio

class Akira_Listen():
    def __init__(self):
        self.r = sr.Recognizer()
        self.mic_index = 0
    
    def list_microphones(self):
        """List all available microphones"""
        print("Available Microphones:")
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            print(f"{index}: {name}")

    def set_mic_index(self, mic_index):
        self.mic_index = mic_index

    def test_microphone(self, mic_index_to_test):
        """Test if the microphone captures sound"""
        try:
            with sr.Microphone(device_index=mic_index_to_test) as source:
                print(f"Testing microphone (Index: {mic_index}) - Speak now...")
                self.r.adjust_for_ambient_noise(source)
                audio = self.r.listen(source, timeout=5)
                print("Audio captured successfully! Playing back...")

                # Save and play the recorded sound for verification
                with open("test_audio.wav", "wb") as f:
                    f.write(audio.get_wav_data())

                print("Playback test_audio.wav with any media player to verify.")
        except Exception as e:
            print(f"Error testing microphone: {e}")

    def recognize_speech(self):
        """Recognize speech from the microphone"""
        try:
            with sr.Microphone(device_index=self.mic_index) as source:
                print("Listening...")
                self.r.adjust_for_ambient_noise(source)
                audio_text = self.r.listen(source)

            return self.r.recognize_google(audio_text)
        except sr.UnknownValueError:
            print("Could not understand the audio.")
            return None
        except sr.RequestError:
            print("Error with the speech recognition service.")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None


if __name__ == "__main__":
    listener = Akira_Listen()

    # Step 1: List available microphones
    listener.list_microphones()
    
    # Step 2: Allow user to choose a microphone index
    mic_index = int(input("Enter the index of your microphone: "))

    # Step 3: Test if the microphone is working
    
    listener.test_microphone(mic_index)
    listener.set_mic_index(mic_index)

    # Step 4: Run Speech Recognition
    print("Now testing speech recognition...")
    print(listener.recognize_speech())
