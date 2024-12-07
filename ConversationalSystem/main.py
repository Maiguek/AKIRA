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
        
        # Video Capture for both left cameras
        self.eye_left = cv2.VideoCapture(2)  # Left camera 
        self.eye_right = cv2.VideoCapture(0)  # Right camera

        # Layout for Eye Camera Display
        self.eye_label_1 = tk.Label(self.root, borderwidth=2, relief="solid")
        self.eye_label_1.place(x=10, y=10, width=640, height=480)

        self.eye_label_2 = tk.Label(self.root, borderwidth=2, relief="solid")
        self.eye_label_2.place(x=660, y=10, width=640, height=480)

        # Conversation History
        self.conversation_history = Text(self.root, wrap="word", borderwidth=2, relief="solid")
        self.conversation_history.place(x=1320, y=10, width=260, height=480)
        
        # Scrollbar for Conversation History
        self.scrollbar = Scrollbar(self.conversation_history)
        self.scrollbar.pack(side="right", fill="y")
        self.conversation_history.config(yscrollcommand=self.scrollbar.set)
        
        # User Information Section
        self.user_info_frame = tk.Frame(self.root, borderwidth=2, relief="solid", bg="yellow")
        self.user_info_frame.place(x=10, y=500, width=780, height=200)
        self.user_info_label = tk.Label(self.user_info_frame, text="Information of the user:")
        self.user_info_label.pack(anchor="w", padx=10, pady=10)
        
        # System Information Section
        self.system_info_frame = tk.Frame(self.root, borderwidth=2, relief="solid", bg="purple")
        self.system_info_frame.place(x=800, y=500, width=780, height=200)
        self.system_info_label = tk.Label(self.system_info_frame, text="Information on the system:\nCurrently talking: \nTotal time of conversation:")
        self.system_info_label.pack(anchor="w", padx=10, pady=10)
        
        # Start and Stop buttons
        self.start_button = tk.Button(self.root, text="Start", command=self.start_conversation, fg="red")
        self.start_button.place(x=10, y=800, width=150, height=50)
        
        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop_conversation, fg="red")
        self.stop_button.place(x=180, y=800, width=150, height=50)
        
        # To control the state of updating frames
        self.running = True
        
        # Initialize MediaPipe Face Mesh and Pose Detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_mesh = self.mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, min_detection_confidence=0.5)
        self.pose = self.mp_pose.Pose(static_image_mode=False, model_complexity=1, min_detection_confidence=0.5)
        
        # Initialize Camera Analyzer
        self.camera_analyzer = CameraAnalyzer()
        self.last_analysis_result = "No analysis yet"
        
        # Initialize Conversational System
        model_path = "/home/maiguek/Documents/LlamaModels/DownloadedWeights/Llama3.2-3B-Instruct-int4-qlora-eo8/llama3_2.pte"
        tokenizer_path = "/home/maiguek/Documents/LlamaModels/DownloadedWeights/Llama3.2-3B-Instruct-int4-qlora-eo8/tokenizer.model"
        executable_path = "../LlamaModels/executorch/cmake-out/examples/models/llama/llama_main"
        self.conversational_system = ConversationalSystem(model_path, tokenizer_path, executable_path)
        
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
    
    def update_frames(self):
        if not self.running:
            return

        # Read frames from both left cameras
        ret1, frame1 = self.eye_left.read()
        ret2, frame2 = self.eye_right.read()

        if ret1:
            # Convert the frame to RGB
            frame_rgb_1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB)
            
            # Detect face mesh using MediaPipe
            results_1 = self.face_mesh.process(frame_rgb_1)
            
            # Draw face mesh annotations on the frame
            if results_1.multi_face_landmarks:
                for face_landmarks in results_1.multi_face_landmarks:
                    self.mp_drawing.draw_landmarks(frame_rgb_1, face_landmarks, self.mp_face_mesh.FACEMESH_TESSELATION)
            
            # Convert frame to ImageTk format
            img_1 = ImageTk.PhotoImage(Image.fromarray(frame_rgb_1))
            self.eye_label_1.config(image=img_1)
            self.eye_label_1.image = img_1

        if ret2:
            # Convert the frame to RGB
            frame_rgb_2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)
            
            # Detect body pose using MediaPipe
            results_2 = self.pose.process(frame_rgb_2)
            
            # Draw pose annotations on the frame
            if results_2.pose_landmarks:
                self.mp_drawing.draw_landmarks(frame_rgb_2, results_2.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
            
            # Convert frame to ImageTk format
            img_2 = ImageTk.PhotoImage(Image.fromarray(frame_rgb_2))
            self.eye_label_2.config(image=img_2)
            self.eye_label_2.image = img_2

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
            self.system_info_label.config(text="Information on the system:\nCurrently talking: No one is speaking\nTotal time of conversation:")
            return

        self.system_info_label.config(text="Information on the system:\nCurrently talking: User is speaking\nTotal time of conversation:")
        user_speech, akira_response = self.conversational_system.listen_and_respond()

        if user_speech and akira_response:
            # Update conversation history in the GUI
            self.conversation_history.insert(tk.END, f"{user_speech}\nAkira: {akira_response}\n")
            self.conversation_history.see(tk.END)
            self.system_info_label.config(text="Information on the system:\nCurrently talking: Akira is speaking\nTotal time of conversation:")
            self.conversational_system.talk(akira_response)

        # Schedule the next conversation update
        self.root.after(3000, self.update_conversation)

    def on_close(self):
        self.running = False
        self.eye_left.release()
        self.eye_right.release()
        self.camera_analyzer.release_camera()
        self.root.destroy()

# Main loop
if __name__ == "__main__":
    root = tk.Tk()
    app = AkiraInterface(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
