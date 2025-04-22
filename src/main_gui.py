import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk, ImageDraw
import cv2
import threading

# Import Akira system components and thread helpers
from main import (
    start_blinking, stop_blinking,
    start_moving_head_rand, stop_moving_head_rand,
    start_moving_hands_rand, stop_moving_hands_rand,
    start_moving_arms_rand, stop_moving_arms_rand,
    start_looking_at, stop_looking_at
)
from perception.listening import Akira_Listen
from perception.vision import Akira_See
from cognition.dialogue_manager import Akira_Chat
from action.speech_synthesis import Akira_Talk
from action.motion_controller import MotionController
from action.music_manager import MusicPlayer

class DualCameraSelectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dual Camera Selector with Chat & Conversation")
        self.root.geometry("1050x650")  # Extra height for controls
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        # Video & control state
        self.running = False
        self.captures = [None, None]
        self.selected_devices = [None, None]
        self.conversation_thread = None
        self.stop_event = threading.Event()

        # Initialize microphone listener
        self.listener = Akira_Listen()
        mic_dict = self.listener.list_microphones()  # {name: index}
        self.mic_mapping = mic_dict
        mic_names = ["None"] + list(mic_dict.keys())
        self.mic_var = tk.StringVar(value="None")
        self.mic_options = mic_names

        # Placeholder image for cameras
        self.placeholder_img = Image.new('RGB', (380, 240), color='gray')
        draw = ImageDraw.Draw(self.placeholder_img)
        draw.text((120, 100), "No Camera", fill="white")

        # Camera displays
        self.label_cam1 = ttk.Label(self.root)
        self.label_cam1.place(x=10, y=10, width=380, height=240)
        self.label_cam2 = ttk.Label(self.root)
        self.label_cam2.place(x=410, y=10, width=380, height=240)

        # Camera selectors
        self.camera_options = ["None", "0", "1", "2"]
        self.cam1_var = tk.StringVar(value="None")
        self.cam2_var = tk.StringVar(value="None")

        self.dropdown1 = ttk.Combobox(self.root, values=self.camera_options,
                                      textvariable=self.cam1_var, state="readonly")
        self.dropdown1.place(x=120, y=270)
        self.set_button1 = ttk.Button(self.root, text="Set Camera 1",
                                      command=lambda: self.set_camera(0))
        self.set_button1.place(x=140, y=300)

        self.dropdown2 = ttk.Combobox(self.root, values=self.camera_options,
                                      textvariable=self.cam2_var, state="readonly")
        self.dropdown2.place(x=520, y=270)
        self.set_button2 = ttk.Button(self.root, text="Set Camera 2",
                                      command=lambda: self.set_camera(1))
        self.set_button2.place(x=540, y=300)

        # Microphone selector
        self.mic_dropdown = ttk.Combobox(self.root, values=self.mic_options,
                                         textvariable=self.mic_var, state="readonly")
        self.mic_dropdown.place(x=320, y=270)
        self.set_mic_button = ttk.Button(self.root, text="Set Microphone",
                                         command=self.set_microphone)
        self.set_mic_button.place(x=320, y=300)

        # Video control buttons
        button_frame = ttk.Frame(self.root)
        button_frame.place(x=250, y=350)
        self.start_button = ttk.Button(button_frame, text="Start Cameras", command=self.start)
        self.start_button.grid(row=0, column=0, padx=5)
        self.pause_button = ttk.Button(button_frame, text="Pause Cameras", command=self.pause)
        self.pause_button.grid(row=0, column=1, padx=5)
        self.exit_button = ttk.Button(button_frame, text="Exit", command=self.exit_app)
        self.exit_button.grid(row=0, column=2, padx=5)

        # Chat display
        self.chat_display = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled')
        self.chat_display.place(x=810, y=10, width=220, height=540)
        # User input entry
        self.chat_entry = ttk.Entry(self.root)
        self.chat_entry.place(x=810, y=560, width=160, height=30)
        self.send_button = ttk.Button(self.root, text="Send", command=self.send_chat)
        self.send_button.place(x=975, y=560, width=50, height=30)

        # Conversation control
        self.start_conv_button = ttk.Button(self.root, text="Start Conversation",
                                            command=self.start_conversation)
        self.start_conv_button.place(x=810, y=600, width=220, height=30)

        # Kick off the video update loop
        self.update_frames()

    def set_camera(self, index):
        if self.captures[index]:
            self.captures[index].release()
            self.captures[index] = None

        selection = self.cam1_var.get() if index == 0 else self.cam2_var.get()
        if selection != "None":
            try:
                cam_index = int(selection)
                cap = cv2.VideoCapture(cam_index)
                if cap.isOpened():
                    self.captures[index] = cap
                    self.selected_devices[index] = cam_index
                    self.append_chat(f"ℹ️ Camera {index+1} set to {cam_index}")
                else:
                    self.append_chat(f"❌ Failed to open camera {cam_index}")
            except Exception as e:
                self.append_chat(f"⚠️ Error opening camera {selection}: {e}")
        else:
            self.selected_devices[index] = None
            self.append_chat(f"ℹ️ Camera {index+1} set to None")

    def set_microphone(self):
        sel = self.mic_var.get()
        if sel != "None":
            mic_index = sel
            try:
                self.listener.set_mic_index(mic_index)
                self.append_chat(f"ℹ️ Microphone set to {mic_index}")
            except Exception as e:
                self.append_chat(f"❌ Error setting microphone {mic_index}: {e}")
        else:
            self.append_chat("ℹ️ Microphone set to None")

    def start(self):
        self.running = True
        self.append_chat("▶️ Cameras started")

    def pause(self):
        self.running = False
        self.append_chat("⏸️ Cameras paused")

    def start_conversation(self):
        if self.conversation_thread and self.conversation_thread.is_alive():
            return
        self.start_conv_button.config(state='disabled')
        self.stop_event.clear()
        self.conversation_thread = threading.Thread(target=self.run_conversation, daemon=True)
        self.conversation_thread.start()
        self.append_chat("🤖 Conversation started")

    def run_conversation(self):
        chat = Akira_Chat()
        chat.start_ollama()
        listener = self.listener
        voice = Akira_Talk(output_path="action/output.wav", spec_path="action/spec.png")
        mc = MotionController(verbose=False)
        akira_vision = Akira_See(motion_controller=mc)
        music_player = MusicPlayer()

        blink_t = start_blinking(mc)
        hands_t = start_moving_hands_rand(mc)
        arms_t = start_moving_arms_rand(mc)
        head_t = start_moving_head_rand(mc)

        try:
            while not self.stop_event.is_set():
                stop_moving_head_rand(mc, head_t)
                mc.neck_rest()
                stop_moving_hands_rand(mc, hands_t)
                stop_moving_arms_rand(mc, arms_t)
                mc.arms_rest()
                look_t = start_looking_at(akira_vision)

                user_input = listener.recognize_speech()
                if user_input:
                    self.append_chat(f"🧑 You: {user_input}")
                    if 'exit' in user_input.lower():
                        break

                    image_input = akira_vision.take_photo()

                    stop_blinking(mc, blink_t)
                    stop_looking_at(akira_vision, look_t)
                    music_player.play_music()
                    mc.akira_close_eyes()
                    mc.akira_close_hand(arduino="left")
                    mc.akira_index_up(arduino="right")
                    hands_t = start_moving_hands_rand(mc, only_wrist=True)
                    arms_t = start_moving_arms_rand(mc)
                    head_t = start_moving_head_rand(mc)

                    description = akira_vision.describe_what_akira_sees(
                        image_input=image_input,
                        eliminate_photo=False,
                        annotate_photo=True
                    )
                    response = chat.generate_response(user_input, description)
                    self.append_chat(f"🤖 Akira: {response}")
                    voice.speak(response)

                    music_player.stop_music()
                    mc.akira_open_eyes()
                    blink_t = start_blinking(mc)
                    mc.akira_half_close_hand("left")
                    mc.akira_half_close_hand("right")
                    mc.move_jaw_and_play("action/output.wav")
        finally:
            try: music_player.stop_music()
            except: pass
            try: voice.speak("Thanks for talking with me, see you next time.")
            except: pass
            try: mc.move_jaw_and_play("action/output.wav")
            except: pass
            try: stop_looking_at(akira_vision, look_t)
            except: pass
            try: stop_moving_arms_rand(mc, arms_t)
            except: pass
            try: stop_moving_hands_rand(mc, hands_t)
            except: pass
            try: stop_moving_head_rand(mc, head_t)
            except: pass
            try: stop_blinking(mc, blink_t)
            except: pass
            try: chat.stop_ollama()
            except: pass
            try: mc.close_connection()
            except: pass

            self.append_chat("✅ Conversation stopped safely.")
            self.start_conv_button.config(state='normal')

    def send_chat(self):
        msg = self.chat_entry.get().strip()
        if msg:
            self.append_chat(f"🧑 You: {msg}")
            self.chat_entry.delete(0, tk.END)

    def append_chat(self, message):
        self.chat_display.configure(state='normal')
        self.chat_display.insert(tk.END, message + "\n")
        self.chat_display.configure(state='disabled')
        self.chat_display.see(tk.END)

    def exit_app(self):
        self.stop_event.set()
        if self.conversation_thread and self.conversation_thread.is_alive():
            self.conversation_thread.join(timeout=2)

        self.pause()
        for cap in self.captures:
            if cap:
                cap.release()

        self.append_chat("👋 Exiting application...")
        self.root.destroy()

    def update_frames(self):
        for i, label in enumerate([self.label_cam1, self.label_cam2]):
            if self.running and self.captures[i]:
                ret, frame = self.captures[i].read()
                if ret:
                    frame = cv2.resize(frame, (380, 240))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame)
                else:
                    img = self.placeholder_img
            else:
                img = self.placeholder_img

            imgtk = ImageTk.PhotoImage(image=img)
            label.imgtk = imgtk
            label.configure(image=imgtk)

        self.root.after(30, self.update_frames)

if __name__ == "__main__":
    root = tk.Tk()
    app = DualCameraSelectorApp(root)
    root.mainloop()
