import os
import sys
import shutil
import requests
from playsound import playsound
from gradio_client import Client, handle_file

sys.path.append(os.path.join(os.path.dirname(__file__), "f5_tts_"))

try:
    from f5_tts_.api import F5TTS
except ModuleNotFoundError as e:
    from action.f5_tts_.api import F5TTS


class Akira_Talk:
    def __init__(
        self,
        method="jetson",    
        url_path = "../../../url.txt",
        output_path = "./output.wav",
        spec_path = "./spec.png"
        ):

        self.method = method
        self.ref_audio_path = "/home/maiguek/Documents/PROJECTS/AKIRA/src/action/ref_audio.wav"
        self.ref_text = "This is a test of my voice that I will use for cloning it and specially for the speech of Akira. Akira will have my voice and I hope it can mimic it very well. Thank you!"
        self.output_path = output_path
        self.spec_path = spec_path
        
        
        if self.method in ["jetson", "API", "laptop"]:
            if self.method == "jetson":
                
                self.f5tts = F5TTS(
                    ref_file=self.ref_audio_path, 
                    ref_text=self.ref_text
                )
                
            elif self.method == "laptop":
                if not os.path.exists(url_path):
                    raise FileNotFoundError(f"URL file not found: {url_path}")
                        
                with open(url_path, "r") as f:
                    self.url = f.read().strip()
            elif self.method == "API":
                self.client = Client("mrfakename/E2-F5-TTS")
        else:
            raise ValueError(f"Method {method} not found. Please try again!")

    def speak(self, gen_text, play=False):
        if self.method == "jetson":
            wav, sr, spect = self.f5tts.infer(
                ref_file=self.ref_audio_path,
                ref_text=self.ref_text,
                gen_text=gen_text,
                file_wave=self.output_path,
                file_spect=self.spec_path,
                seed=-1  # random seed = -1
            )
            
            
        elif self.method == "laptop":
            # requires connection with external laptop
            text = {"gen_text": gen_text}
            try:
                response = requests.post(self.url, json=text)
                response.raise_for_status()

                with open("output.wav", "wb") as f:
                    f.write(response.content)
                print("Audio file saved as output.wav")

            except Exception as e:
                print("Error:", e)
                
        elif self.method == "API":    
            # only a limited amount of times available
            result = self.client.predict(
                            ref_audio_input=handle_file(self.ref_audio_path),
                            ref_text_input=self.ref_text,
                            gen_text_input=gen_text,
                            remove_silence=False,
                            cross_fade_duration_slider=0.15,
                            nfe_slider=32,
                            speed_slider=1,
                            api_name="/basic_tts"
            )
            
            source = result[0]
            destination = self.output_path
            shutil.copy(source, destination)
        else:
            raise ValueError(f"Method {method} not found. Please try again!")

        if play:
            playsound(self.output_path)
        


if __name__ == "__main__":
    voice = Akira_Talk()

    print(voice.speak("I would love to be cat. Real bad, you know!"))
            
