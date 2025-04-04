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
        #print(self.servos_list)

        # Initialize head positions with the rest positions for each head servo.
        self.head_positions = {
            "Neck": self.servos_list["Neck"]["rest_pos"],
            "Rollneck": self.servos_list["Rollneck"]["rest_pos"],
            "Rothead": self.servos_list["Rothead"]["rest_pos"]
        }
        
        self.move_head = True

    def move_head_relative(self, adjust_neck, adjust_rollneck, adjust_rothead):
        """
        Adjusts the head servos relative to their current positions.
        The adjustments are clamped within each servo's minimum and maximum values.
        """
        # Retrieve the current positions
        current_neck = self.head_positions["Neck"]
        current_rollneck = self.head_positions["Rollneck"]
        current_rothead = self.head_positions["Rothead"]

        # Calculate new positions based on relative adjustments
        new_neck = current_neck + adjust_neck
        new_rollneck = current_rollneck + adjust_rollneck
        new_rothead = current_rothead + adjust_rothead

        # Clamp the new positions within the allowed ranges
        neck_limits = (self.servos_list["Neck"]["min_pos"], self.servos_list["Neck"]["max_pos"])
        rollneck_limits = (self.servos_list["Rollneck"]["min_pos"], self.servos_list["Rollneck"]["max_pos"])
        rothead_limits = (self.servos_list["Rothead"]["min_pos"], self.servos_list["Rothead"]["max_pos"])
        
        new_neck = int(max(neck_limits[0], min(new_neck, neck_limits[1])))
        new_rollneck = int(max(rollneck_limits[0], min(new_rollneck, rollneck_limits[1])))
        new_rothead = int(max(rothead_limits[0], min(new_rothead, rothead_limits[1])))

        # Update the stored current positions
        self.head_positions["Neck"] = new_neck
        self.head_positions["Rollneck"] = new_rollneck
        self.head_positions["Rothead"] = new_rothead

        # Get the indices for the servos
        neck_index = self.servos_list["Neck"]["index"]
        rollneck_index = self.servos_list["Rollneck"]["index"]
        rothead_index = self.servos_list["Rothead"]["index"]

        # Send the new positions to the Arduino
        self.ser.write(f"{neck_index} {new_neck}\n".encode())
        self.ser.write(f"{rollneck_index} {new_rollneck}\n".encode())
        self.ser.write(f"{rothead_index} {new_rothead}\n".encode())


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
        """Plays the audio and moves the jaw in sync with an added oscillatory effect during speech."""
        
        # Load the audio file
        y, sr = librosa.load(audio_file, sr=None)
        
        # Compute short-time energy for jaw movement
        frame_length = 1024
        hop_length = 512
        energy = np.array([
            sum(abs(y[i:i+frame_length]**2)) for i in range(0, len(y), hop_length)
        ])
        
        # Apply gain to boost energy dynamic range
        gain = 3.0  # Adjust this factor as needed
        energy = energy * gain
        
        # Direct normalization to map energy to the servo range
        servo_min = self.servos_list["Jaw"]["min_pos"]
        servo_max = self.servos_list["Jaw"]["max_pos"]
        servo_index = self.servos_list["Jaw"]["index"]
        energy_norm = np.interp(energy, (energy.min(), energy.max()), (servo_min, servo_max))
        
        # Optionally, apply Exponential Moving Average (EMA) for smoother motion
        alpha = 0.3  # Increased responsiveness compared to 0.1
        smoothed_energy = np.zeros_like(energy_norm)
        smoothed_energy[0] = energy_norm[0]
        for i in range(1, len(energy_norm)):
            smoothed_energy[i] = alpha * energy_norm[i] + (1 - alpha) * smoothed_energy[i - 1]
        
        # Parameters for the oscillatory (open/close) movement
        blend_factor = 0.5  # 0 means use only the normalized value; 1 means full oscillation
        freq = 2.0        # Frequency in Hz for the open-close cycle
        # Define a threshold: when the base angle is above this, we assume speech is occurring.
        speech_threshold = servo_min + 0.1 * (servo_max - servo_min)
        
        # Function to move the jaw in a separate thread
        def move_jaw():
            for i, base_angle in enumerate(smoothed_energy):
                # Time in seconds for the current frame
                t = i * hop_length / sr  
                # Compute an oscillatory component (sine wave, normalized to [0, 1])
                oscillation = (np.sin(2 * np.pi * freq * t) + 1) / 2  
                
                # If the base angle indicates speech (i.e. above our threshold), blend in the oscillation.
                if base_angle > speech_threshold:
                    # Oscillatory value mapping fully from closed (servo_min) to open (servo_max)
                    oscillated_angle = servo_min + oscillation * (servo_max - servo_min)
                    # Blend the base angle and oscillatory movement
                    angle = (1 - blend_factor) * base_angle + blend_factor * oscillated_angle
                else:
                    angle = base_angle  # No oscillation if below threshold
                
                # Clamp the angle within the servo limits
                angle = max(servo_min, min(angle, servo_max))
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
    
