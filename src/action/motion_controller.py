import numpy as np
import pandas as pd
import serial
import time
import librosa
import sounddevice as sd
import threading
import random
from playsound import playsound

class MotionController:
    def __init__(self, serial_port='/dev/ttyACM0', baud_rate=9600, servos_file="/home/maiguek/Documents/PROJECTS/AKIRA/src/action/servos_data_left.csv"):
        self.serial_port = serial_port
        self.ser = serial.Serial(serial_port, baud_rate)
        time.sleep(2)  # Wait for Arduino connection

        df = pd.read_csv(servos_file)
        servos_list = df.to_dict(orient="records")
        for index in range(len(servos_list)):
            servos_list[index]["index"] = index 
        self.servos_list = {servos_list[index]["name"]:servos_list[index] for index in range(len(servos_list))}
        self.move_head = True
        #print(self.servos_list)

    def move_head_randomly(self):
        """
        Moves Akira's head and tilts it randomly but smoothly.
        This function will be run inside a separate thread from `main()`.
        """
        neck = self.servos_list["Neck"]
        roll_neck = self.servos_list["Rollneck"]
        rot_head = self.servos_list["Rothead"]

        neck_index, roll_neck_index, rot_head_index = neck["index"], roll_neck["index"], rot_head["index"]

        while self.move_head:
            # Generate random angles within a reasonable range for smooth motion
            neck_target = random.randint(neck["min_pos"] + 5, neck["max_pos"] - 5)
            roll_neck_target = random.randint(roll_neck["min_pos"] + 5, roll_neck["max_pos"] - 5)
            rot_head_target = random.randint(rot_head["min_pos"] + 5, rot_head["max_pos"] - 5)

            # Get current positions
            neck_current = neck["rest_pos"]
            roll_neck_current = roll_neck["rest_pos"]
            rot_head_current = rot_head["rest_pos"]

            # Smooth transition
            distance = abs(neck_target - neck_current)  # How far we need to move
            step_size = max(5, distance // 10)  # Adjust smoothness dynamically

            for _ in range(10):  # Gradually move over 10 steps
                neck_current += (neck_target - neck_current) / step_size
                roll_neck_current += (roll_neck_target - roll_neck_current) / step_size
                rot_head_current += (rot_head_target - rot_head_current) / step_size
                
                self.ser.write(f"{neck_index} {int(neck_current)}\n".encode())
                self.ser.write(f"{roll_neck_index} {int(roll_neck_current)}\n".encode())
                self.ser.write(f"{rot_head_index} {int(rot_head_current)}\n".encode())
                
                time.sleep(0.1)  # Small delay for smooth motion

            # Wait for a random time before next movement
            time.sleep(random.uniform(2, 6))

    def stop_head(self):
        self.move_head = False

    def start_head(self):
        self.move_head = True

    def move_jaw_and_play(self, audio_file="output.wav"):
        """Plays the audio and moves the jaw in sync."""

        # Load the audio file
        y, sr = librosa.load(audio_file, sr=None)

        # Compute short-time energy for jaw movement
        frame_length = 1024
        hop_length = 512
        energy = np.array([
            sum(abs(y[i:i+frame_length]**2)) for i in range(0, len(y), hop_length)
        ])

        # Normalize to servo range
        servo_min, servo_max, servo_index = self.servos_list["Jaw"]["min_pos"], self.servos_list["Jaw"]["max_pos"], self.servos_list["Jaw"]["index"]
        energy_norm = np.interp(energy, (energy.min(), energy.max()), (servo_min, servo_max))

        # Apply Exponential Moving Average (EMA) for smoothness
        alpha = 0.3
        smoothed_energy = np.zeros_like(energy_norm)
        smoothed_energy[0] = energy_norm[0]

        for i in range(1, len(energy_norm)):
            smoothed_energy[i] = alpha * energy_norm[i] + (1 - alpha) * smoothed_energy[i - 1]

        # Function to move the jaw in a separate thread
        def move_jaw():
            for angle in smoothed_energy:
                self.ser.write(f"{servo_index} {int(angle)}\n".encode())
                time.sleep(hop_length / sr)

        # Start jaw movement in a separate thread
        jaw_thread = threading.Thread(target=move_jaw)
        jaw_thread.start()

        # Play the audio
        playsound(audio_file)

        # Ensure the jaw movement finishes
        jaw_thread.join()

    def blink_eyes(self, blink_duration=0.2):
        """
        Makes Akira blink by closing and reopening the eyelids.
        """
        eyelid_left_up = self.servos_list["Eyelid_Left_Up"]
        eyelid_left_down = self.servos_list["Eyelid_Left_Down"]
        eyelid_right_up = self.servos_list["Eyelid_Right_Upper"]
        eyelid_right_down = self.servos_list["Eyelid_Right_Lower"]

        eyelid_left_up_index = eyelid_left_up["index"]
        eyelid_left_down_index = eyelid_left_down["index"]
        eyelid_right_up_index = eyelid_right_up["index"]
        eyelid_right_down_index = eyelid_right_down["index"]

        # Define closed positions
        eyelid_left_up_closed = eyelid_left_up["max_pos"]  # Max for upper eyelid
        eyelid_left_down_closed = eyelid_left_down["min_pos"]  # Min for lower eyelid
        eyelid_right_up_closed = eyelid_right_up["min_pos"] # Max for upper eyelid
        eyelid_right_down_closed = eyelid_right_down["max_pos"]  # Min for lower eyelid

        # Define rest (open) positions
        eyelid_left_up_open = eyelid_left_up["rest_pos"]
        eyelid_left_down_open = eyelid_left_down["rest_pos"]
        eyelid_right_up_open = eyelid_right_up["rest_pos"]
        eyelid_right_down_open = eyelid_right_down["rest_pos"]

        # Close eyelids
        self.ser.write(f"{eyelid_left_up_index} {eyelid_left_up_closed}\n".encode())
        self.ser.write(f"{eyelid_left_down_index} {eyelid_left_down_closed}\n".encode())
        self.ser.write(f"{eyelid_right_up_index} {eyelid_right_up_closed}\n".encode())
        self.ser.write(f"{eyelid_right_down_index} {eyelid_right_down_closed}\n".encode())
        time.sleep(blink_duration)

        # Open eyelids (return to rest positions)
        self.ser.write(f"{eyelid_left_up_index} {eyelid_left_up_open}\n".encode())
        self.ser.write(f"{eyelid_left_down_index} {eyelid_left_down_open}\n".encode())
        self.ser.write(f"{eyelid_right_up_index} {eyelid_right_up_open}\n".encode())
        self.ser.write(f"{eyelid_right_down_index} {eyelid_right_down_open}\n".encode())
        time.sleep(blink_duration)

    def close_connection(self):
        # Close serial connection
        self.ser.close()
        print(f"Connection with Arduino at {self.serial_port} successfully closed!")

if __name__ == "__main__":
    # Just for testing...
    mc = MotionController()
    mc.blink_eyes(0.25)
    mc.blink_eyes(0.25)
    mc.move_jaw_and_play()
    mc.blink_eyes(0.25)
    mc.close_connection()
    
