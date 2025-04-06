from playsound import playsound
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import threading
import librosa
import random
import serial
import time

class MotionController:
    def __init__(
        self,
        left_port='/dev/ttyACM0',
        right_port='/dev/ttyACM1',
        baud_rate=9600,
        left_servos_file="servos_data_left.csv",
        right_servos_file="servos_data_right.csv",
        initialize_on_start=True,
        ):
        
        self.left_port = left_port
        self.right_port = right_port
        
        self.ardunio_left = None
        self.arduino_right = None

        self.arduinos_connected = False
        self.baud_rate = baud_rate

        if initialize_on_start:
            self.initiate_connection()

        def load_servo_info(left_servos_file, right_servos_file):
            df_left = pd.read_csv(left_servos_file)
            df_right = pd.read_csv(right_servos_file)

            left_servos_list = df_left.to_dict(orient="records")
            right_servos_list = df_right.to_dict(orient="records")

            for index in range(len(left_servos_list)):
                left_servos_list[index]["index"] = index
                left_servos_list[index]["current"] = left_servos_list[index]["rest_pos"]
            left_servos_list = {left_servos_list[index]["name"]:left_servos_list[index] for index in range(len(left_servos_list))}
            for index in range(len(right_servos_list)):
                right_servos_list[index]["index"] = index
                right_servos_list[index]["current"] = right_servos_list[index]["rest_pos"]
            right_servos_list = {right_servos_list[index]["name"]:right_servos_list[index] for index in range(len(right_servos_list))}

            return left_servos_list, right_servos_list

        self.left_servos_list, self.right_servos_list = load_servo_info(left_servos_file, right_servos_file)
        self.num_left_servos = len(self.left_servos_list)
        self.num_right_servos = len(self.right_servos_list)

        self.neck_servos = ("Neck", "Rollneck", "Rothead")
        self.shoulder_servos = ("shoulder", "omoplate", "rotate", "bicep")
        self.hand_servos = ("wrist", "ringfinger", "midfinger", "pinky", "index", "thumb")
        self.eyes_servos = ("Eyelid_Right_Upper", "Eyelid_Right_Lower", "Eyelid_Left_Down", "Eyelid_Left_UP")
        self.face_servos = ("Upper_Lip", "Check_L", "Check_R", "Forhead_R", "Forhead_L", "Jaw")
        self.mouth_servos = ("Upper_Lip", "Jaw")

        self.move_head_randomly = False
        self.flag_test = False
        self.blink_randomly = False
        
    def initiate_connection(self):
        self.arduino_left = serial.Serial(self.left_port , self.baud_rate, timeout=1)
        self.arduino_right = serial.Serial(self.right_port, self.baud_rate, timeout=1)

        time.sleep(2)  # Give them time to initialize
        print("Connection has been successfully initiated!")
        self.connection_status = True

    def close_connection(self):
        if self.arduino_left is not None and self.arduino_right is not None:
            self.arduino_left.close()
            self.arduino_right.close()
            print("Connection has been successfully closed!")
            self.connection_status = False
        else:
            print("Connection has not been initiated!")

    def get_servo_positions(self, servo_name, arduino):
        if arduino == "left":
            servo_list = self.left_servos_list
        elif arduino == "right":
            servo_list = self.right_servos_list
        else:
            print(f"There is no {arduino} arduino. Please try either 'left' or 'right'.")
            return None
        try:
            min_pos = servo_list[servo_name]["min_pos"]
            max_pos = servo_list[servo_name]["max_pos"]
            rest_pos = servo_list[servo_name]["rest_pos"]
            servo_index = servo_list[servo_name]["index"]
            servo_current = servo_list[servo_name]["current"]
            
            return servo_index, rest_pos, min_pos, max_pos, servo_current
        
        except Exception as e:
            print("We have an exception:", e)
            return None

    def send_command(self, servo_index, angle, arduino, servo_name, verbose=False):
        if self.connection_status:
            if arduino == "left":
                if isinstance(servo_index, int) and servo_index > 0 and servo_index < self.num_left_servos:
                    if isinstance(angle, int) and angle >= 0 and angle <= 180:
                        if verbose:
                            print(f">>Moving {servo_name} ({servo_index}) to {angle} on arduino {arduino}.")
                        self.arduino_left.write(f"{servo_index} {angle}\n".encode())
                        self.left_servos_list[servo_name]["current"] = angle
            elif arduino == "right":
                if isinstance(servo_index, int) and servo_index > 0 and servo_index < self.num_right_servos:
                    if isinstance(angle, int) and angle >= 0 and angle <= 180:
                        if verbose:
                            print(f">>Moving {servo_name} ({servo_index}) to {angle} on arduino {arduino}.")
                        self.arduino_right.write(f"{servo_index} {angle}\n".encode())
                        self.right_servos_list[servo_name]["current"] = angle
            else:
                print(f"{arduino} arduino does not exist. Please try either 'left' or 'right'!")
        else:
            print(f"Connection status: {self.connection_status}")

    def akira_open_eyes(self):
        arduino = "left"
        for servo_name in self.eyes_servos:
            servo_index, servo_rest, servo_min, servo_max, _ = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
            self.send_command(servo_index, servo_rest, arduino, servo_name)

    def akira_close_eyes(self):
        arduino = "left"
        for servo_name in self.eyes_servos:
            servo_index, servo_rest, servo_min, servo_max, _ = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
            if "Left" in servo_name:
                if "Up" in servo_name:
                    self.send_command(servo_index, servo_max, arduino, servo_name)
                else:
                    self.send_command(servo_index, servo_min, arduino, servo_name)
            elif "Right" in servo_name:
                if "Up" in servo_name:
                    self.send_command(servo_index, servo_min, arduino, servo_name)
                else:
                    self.send_command(servo_index, servo_max, arduino, servo_name)
                        
    def akira_blink_randomly(self, blink_duration=0.2):
        while self.blink_randomly:
            self.akira_close_eyes()
            time.sleep(blink_duration)
            self.akira_open_eyes()
            time.sleep(random.uniform(3, 7))

    def start_blink_randomly(self):
        self.blink_randomly = True

    def stop_blink_randomly(self):
        self.blink_randomly = False

    def move_head_randomly(self):
        arduino = "left"
        while self.move_head_randomly:
            for servo_name in self.neck_servos:
                servo_index, servo_rest, servo_min, servo_max, servo_current = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
                
                servo_target = random.randint(servo_min + 5, servo_max - 5)
                distance = abs(servo_target - servo_current)
                step_size = max(5, distance // 10)

                for _ in range(10):
                    servo_current += (servo_target - servo_current) / step_size
                    self.send_command(servo_index, servo_current, arduino, servo_name)
                    time.sleep(0.1)

                time.sleep(random.uniform(2, 6))

    def start_move_head_randomly(self):
        self.move_head_randomly = True
                    
    def stop_move_head_randomly(self):
        self.move_head_randomly = False

    def move_jaw_and_play(self, audio_file="output.wav", plot_debug=False):
        arduino = "left"
        
        y, sr = librosa.load(audio_file, sr=None)
        frame_length = 1024
        hop_length = 512
        energy = np.array([
            sum(abs(y[i:i+frame_length]**2)) for i in range(0, len(y), hop_length)
        ])
        
        jaw_name = "Jaw"
        jaw_index, jaw_rest, jaw_min, jaw_max, jaw_current = self.get_servo_positions(servo_name=jaw_name, arduino=arduino)
        upper_name = "Upper_Lip"
        upper_index, upper_rest, upper_min, upper_max, upper_current = self.get_servo_positions(servo_name=upper_name, arduino=arduino)
        
        jaw_angles = np.interp(energy, (energy.min(), energy.max()), (jaw_min, jaw_max))
        
        alpha = 0.1
        smoothed_jaw = np.zeros_like(jaw_angles)
        smoothed_jaw[0] = jaw_angles[0]
        for i in range(1, len(jaw_angles)):
            smoothed_jaw[i] = alpha * jaw_angles[i] + (1 - alpha) * smoothed_jaw[i - 1]
        
        def move_mouth():
            start_time = time.time()
            for i, raw_angle in enumerate(smoothed_jaw):
                jaw_angle = raw_angle + np.log1p(raw_angle - jaw_min) * 5
                jaw_angle = int(max(jaw_min, min(jaw_angle, jaw_max)))
                
                # Calculate normalized factor (0 = closed, 1 = open)
                factor = (jaw_angle - jaw_min) / float(jaw_max - jaw_min)
                # Map the factor to the upper lip's range
                upper_angle = int(upper_min + factor * (upper_max - upper_min))
                
                self.send_command(jaw_index, jaw_angle, arduino, jaw_name)
                self.send_command(upper_index, upper_angle, arduino, upper_name)              
                
                target_time = start_time + (i + 1) * (hop_length / sr)
                sleep_time = target_time - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        def play_audio():
            playsound(audio_file)
        
        jaw_thread = threading.Thread(target=move_mouth)
        audio_thread = threading.Thread(target=play_audio)
        jaw_thread.start()
        audio_thread.start()
        
        audio_thread.join()
        jaw_thread.join()
        
        if plot_debug:
            plt.subplot(5, 1, 1)
            plt.plot(y)
            plt.title("Audio Signal")
            plt.subplot(5, 1, 2)
            plt.plot(energy)
            plt.title("Energy")
            plt.subplot(5, 1, 3)
            plt.plot(jaw_angles)
            plt.title("Jaw Angles (Raw)")
            plt.subplot(5, 1, 4)
            plt.plot(smoothed_jaw)
            plt.title("Smoothed Jaw Angles")
            plt.subplot(5, 1, 5)
            factor_array = (smoothed_jaw - jaw_min) / (jaw_max - jaw_min)
            upper_angles = upper_min + factor_array * (upper_max - upper_min)
            plt.plot(upper_angles)
            plt.title("Upper Lip Angles")
            plt.tight_layout()
            plt.show()


if __name__ == "__main__":
    mc = MotionController(initialize_on_start=True)
    mc.move_jaw_and_play(plot_debug=True)
    mc.close_connection()
    

    
        

    

    """
    # Send commands
    arduino_left.write(b'MOVE_SERVO_1\n')
    arduino_right.write(b'MOVE_SERVO_2\n')

    # Optionally read responses
    response1 = arduino_left.readline().decode().strip()
    response2 = arduino_right.readline().decode().strip()

    print("Arduino Left:", response1)
    print("Arduino Right:", response2)
    """
