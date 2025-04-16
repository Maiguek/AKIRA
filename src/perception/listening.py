import speech_recognition as sr
from faster_whisper import WhisperModel
import tempfile
from playsound import playsound

class Akira_Listen():
    def __init__(self, recognizer_method="whisper", whisper_model_size="tiny"):
        self.r = sr.Recognizer()
        self.r.pause_threshold = 5.0
        self.mic_index = 0
        self.recognizer_method = recognizer_method

        if self.recognizer_method == "whisper":
            self.whisper_model = WhisperModel(whisper_model_size)
    
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
                print("Audio captured successfully!")

                with open("test_audio.wav", "wb") as f:
                    f.write(audio.get_wav_data())
                print("Playing audio...")
                playsound("test_audio.wav")

        except Exception as e:
            print(f"Error testing microphone: {e}")

    def recognize_speech(self):
        """Recognize speech from the microphone"""
        try:
            with sr.Microphone(device_index=self.mic_index) as source:
                print("Listening...")
                self.r.adjust_for_ambient_noise(source)
                audio_text = self.r.listen(
                    source,
                    timeout=None,
                    phrase_time_limit=None
                    )

            if self.recognizer_method == "google":
                return self.r.recognize_google(audio_text)
            elif self.recognizer_method == "whisper":
                wav_bytes = audio_text.get_wav_data()
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                    tmp_wav.write(wav_bytes)
                    tmp_wav.flush()

                    segments, info = self.whisper_model.transcribe(tmp_wav.name)

                transcription = " ".join(segment.text for segment in segments)
                return transcription
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
    listener = Akira_Listen(
        recognizer_method="whisper",
        whisper_model_size="tiny"
        )

    listener.list_microphones()
    mic_index = int(input("Enter the index of your microphone: "))
    #listener.test_microphone(mic_index)
    
    listener.set_mic_index(mic_index)

    # Step 4: Run Speech Recognition
    print("Now testing speech recognition...")
    print(listener.recognize_speech())
