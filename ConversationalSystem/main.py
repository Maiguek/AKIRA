import cv2
import tkinter as tk
from tkinter import Text, Scrollbar, messagebox
from PIL import Image, ImageTk
import mediapipe as mp
from VisualAnalyzer import CameraAnalyzer
from ConversationalSystem import ConversationalSystem

# Define important paths and initialize modules
user_info_path = "userInfo.csv"
conversation_history_path = "ConversationHistory.txt"

class AkiraInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("Akira Interaction Interface")
        self.root.geometry("1600x1000")
        
        # Video Capture for both eyes
        self.cap_left = cv2.VideoCapture(0)  # Left eye
        self.cap_right = cv2.VideoCapture(2)  # Right eye

        # Layout for Eye Camera Display
        self.eye_label = tk.Label(self.root, borderwidth=2, relief="solid")
        self.eye_label.place(x=10, y=10, width=640, height=480)

        # Button to Switch Cameras
        self.switch_button = tk.Button(self.root, text="Switch Camera", command=self.switch_camera)
        self.switch_button.place(x=10, y=500, width=150, height=40)

        # Conversation History
        self.conversation_history = Text(self.root, wrap="word", borderwidth=2, relief="solid")
        self.conversation_history.place(x=670, y=10, width=900, height=480)
        
        # Scrollbar for Conversation History
        self.scrollbar = Scrollbar(self.conversation_history)
        self.scrollbar.pack(side="right", fill="y")
        self.conversation_history.config(yscrollcommand=self.scrollbar.set)
        
        # User Information Section
        self.user_info_frame = tk.Frame(self.root, borderwidth=2, relief="solid", bg="yellow")
        self.user_info_frame.place(x=10, y=550, width=780, height=200)
        self.user_info_label = tk.Label(self.user_info_frame, text="Information of the user:")
        self.user_info_label.pack(anchor="w", padx=10, pady=10)
        
        # System Information Section
        self.system_info_frame = tk.Frame(self.root, borderwidth=2, relief="solid", bg="purple")
        self.system_info_frame.place(x=800, y=550, width=780, height=200)
        self.system_info_label = tk.Label(self.system_info_frame, text="Information on the system:\nCurrently talking: \nTotal time of conversation:")
        self.system_info_label.pack(anchor="w", padx=10, pady=10)
        
        # Start and Stop buttons
        self.start_button = tk.Button(self.root, text="Start", command=self.start_conversation, fg="red")
        self.start_button.place(x=10, y=800, width=150, height=50)
        
        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop_conversation, fg="red")
        self.stop_button.place(x=180, y=800, width=150, height=50)
        
        # To control the state of updating frames
        self.running = True
        self.current_camera = 'left'
        
        # Initialize MediaPipe Face Detection
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_detection = self.mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5)
        
        # Initialize Camera Analyzer
        self.camera_analyzer = CameraAnalyzer()
        self.last_analysis_result = "No analysis yet"
        
        # Initialize Conversational System
        model_path = "/home/maiguek/Documents/LlamaModels/DownloadedWeights/Llama3.2-3B-Instruct-int4-qlora-eo8/llama3_2.pte"
        tokenizer_path = "/home/maiguek/Documents/LlamaModels/DownloadedWeights/Llama3.2-3B-Instruct-int4-qlora-eo8/tokenizer.model"
        executable_path = "../LlamaModels/executorch/cmake-out/examples/models/llama/llama_main"
        self.conversational_system = ConversationalSystem(user_info_path, conversation_history_path, model_path, tokenizer_path, executable_path)
        
        # Start updating frames
        self.update_frames()
        self.root.after(3000, self.update_analysis)  # Schedule analysis every 3 seconds

    def start_conversation(self):
        messagebox.showinfo("Info", "Conversation Started")
        self.running = True
        self.update_conversation()

    def stop_conversation(self):
        messagebox.showinfo("Info", "Conversation Stopped")
        self.running = False
    
    def switch_camera(self):
        # Switch between left and right camera
        if self.current_camera == 'left':
            self.current_camera = 'right'
            self.camera_analyzer.update_camera_index(2)
        else:
            self.current_camera = 'left'
            self.camera_analyzer.update_camera_index(0)
        
        # Release and reinitialize the camera to prevent freezing
        if self.current_camera == 'left':
            self.cap_right.release()
            self.cap_left = cv2.VideoCapture(0, cv2.CAP_V4L2)
        else:
            self.cap_left.release()
            self.cap_right = cv2.VideoCapture(2, cv2.CAP_V4L2)

    def update_frames(self):
        if not self.running:
            return

        if self.current_camera == 'left':
            ret, frame = self.cap_left.read()
        else:
            ret, frame = self.cap_right.read()

        if ret:
            # Convert the frame to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect faces using MediaPipe
            results = self.face_detection.process(frame_rgb)
            
            # Draw face detection annotations on the frame
            if results.detections:
                for detection in results.detections:
                    self.mp_drawing.draw_detection(frame_rgb, detection)
            
            # Convert frame to ImageTk format
            img = ImageTk.PhotoImage(Image.fromarray(frame_rgb))
            self.eye_label.config(image=img)
            self.eye_label.image = img

        # Call update_frames again after 30 ms
        self.root.after(30, self.update_frames)

    def update_analysis(self):
        # Perform analysis every 3 seconds
        analysis_result = self.camera_analyzer.get_analysis_string()
        if analysis_result != "No face detected":
            self.last_analysis_result = analysis_result
        
        # Update user information label
        self.user_info_label.config(text=f"Information of the user:\n{self.last_analysis_result}")
        
        # Schedule the next analysis
        self.root.after(3000, self.update_analysis)

    def update_conversation(self):
        if not self.running:
            return

        user_speech, akira_response = self.conversational_system.listen_and_respond()

        if user_speech and akira_response:
            # Update conversation history in the GUI
            self.conversation_history.insert(tk.END, f"{user_speech}\nAkira: {akira_response}\n")
            self.conversation_history.see(tk.END)

        # Schedule the next conversation update
        self.root.after(3000, self.update_conversation)

    def on_close(self):
        self.running = False
        self.cap_left.release()
        self.cap_right.release()
        self.camera_analyzer.release_camera()
        self.root.destroy()

# Main loop
if __name__ == "__main__":
    root = tk.Tk()
    app = AkiraInterface(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
