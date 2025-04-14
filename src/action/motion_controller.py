from playsound import playsound
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import threading
import librosa
import random
import serial
import time
import os

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

        current_dir = os.path.dirname(os.path.abspath(__file__))
        left_servos_file = os.path.join(current_dir, left_servos_file)
        right_servos_file = os.path.join(current_dir, right_servos_file)
        
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
        self.finger_servos = ("ringfinger", "midfinger", "pinky", "index", "thumb")
        self.eyes_servos = ("Eyelid_Right_Upper", "Eyelid_Right_Lower", "Eyelid_Left_Down", "Eyelid_Left_Up")
        self.face_servos = ("Upper_Lip", "Check_L", "Check_R", "Forhead_R", "Forhead_L", "Jaw")
        self.mouth_servos = ("Upper_Lip", "Jaw")

        self.move_head_randomly = True
        self.blink_randomly = True
        self.move_hands_randomly = True
        self.move_arms_randomly = True
        
        self.hand_status_options = {
            "Open":self.akira_open_hand,
            "Close":self.akira_close_hand,
            "HalfClose":self.akira_half_close_hand,
            "IndexUp":self.akira_index_up,
            "ThumbsUp":self.akira_thumbs_up,
            "OtherUp":self.akira_raise_finger
            }
        self.hand_status = "Open"

        self.lock_left = threading.Lock()
        self.lock_right = threading.Lock()
        
    def initiate_connection(self):
        self.arduino_left = serial.Serial(self.left_port , self.baud_rate, timeout=1)
        self.arduino_right = serial.Serial(self.right_port, self.baud_rate, timeout=1)

        time.sleep(2)  # Give them time to initialize
        print("Connection has been successfully initiated!")
        self.connection_status = True

    def close_connection(self):
        if self.arduino_left is not None and self.arduino_right is not None:
            self.all_rest()
            time.sleep(15)
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

    def set_current_pos_servo(self, servo_name, arduino, angle):
        if arduino == "left":
            self.left_servos_list[servo_name]["current"] = angle
        elif arduino == "right":
            self.right_servos_list[servo_name]["current"] = angle

    def send_command(self, servo_index, angle, arduino, servo_name, verbose=False):
        if self.connection_status:
            if arduino == "left":
                if isinstance(servo_index, int) and servo_index > 0 and servo_index < self.num_left_servos:
                    if isinstance(angle, int) and angle >= 0 and angle <= 180:
                        if verbose:
                            print(f">>Moving {servo_name} ({servo_index}) to {angle} on arduino {arduino}.")
                        with self.lock_left:
                            self.arduino_left.write(f"{servo_index} {angle}\n".encode())
                            if verbose:
                                response = self.arduino_left.readline().decode().strip()
                                print("Left arduino response:", response)
                        self.left_servos_list[servo_name]["current"] = angle
            elif arduino == "right":
                if isinstance(servo_index, int) and servo_index > 0 and servo_index < self.num_right_servos:
                    if isinstance(angle, int) and angle >= 0 and angle <= 180:
                        if verbose:
                            print(f">>Moving {servo_name} ({servo_index}) to {angle} on arduino {arduino}.")
                        with self.lock_right:
                            self.arduino_right.write(f"{servo_index} {angle}\n".encode())
                            if verbose:
                                response = self.arduino_right.readline().decode().strip()
                                print("Right arduino response:", response)
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

    def akira_move_head_randomly(self):
        arduino = "left"

        neck_name, roll_name, rot_name = self.neck_servos
        neck_index, neck_rest, neck_min, neck_max, neck_current = self.get_servo_positions(servo_name=neck_name, arduino=arduino)
        roll_index, roll_rest, roll_min, roll_max, roll_current = self.get_servo_positions(servo_name=roll_name, arduino=arduino)
        rot_index, rot_rest, rot_min, rot_max, rot_current = self.get_servo_positions(servo_name=rot_name, arduino=arduino)
        
        while self.move_head_randomly:            
            neck_target = random.randint(neck_min + 5, neck_max - 5)
            roll_target = random.randint(roll_min + 5, roll_max - 5)
            rot_target = random.randint(rot_min + 5, rot_max - 5)
            
            distance = abs(neck_target - neck_rest) # for some reason this distance works very nice :)
            step_size = max(5, distance // 10)

            for _ in range(10):
                neck_current += (neck_target - neck_current) / step_size
                roll_current += (roll_target - roll_current) / step_size
                rot_current += (rot_target - rot_current) / step_size
                
                neck_angle = int(max(neck_min, min(neck_current, neck_max)))
                roll_angle = int(max(roll_min, min(roll_current, roll_max)))
                rot_angle = int(max(rot_min, min(rot_current, rot_max)))
                
                self.send_command(neck_index, neck_angle, arduino, neck_name)
                self.send_command(roll_index, roll_angle, arduino, roll_name)
                self.send_command(rot_index, rot_angle, arduino, rot_name)
                
                time.sleep(0.1)

            time.sleep(random.uniform(2, 6))

    def start_move_head_randomly(self):
        self.move_head_randomly = True
                    
    def stop_move_head_randomly(self):
        self.move_head_randomly = False

    def move_jaw_and_play(self, audio_file="output.wav", plot_debug=False):
        arduino = "left"
        
        # Load audio and extract energy profile (same as before)
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
            # Wait until the event is triggered so that start time is synchronized
            frame_interval = hop_length / sr
            prev_time = time.time()
            for i, raw_angle in enumerate(smoothed_jaw):
                jaw_angle = raw_angle + np.log1p(raw_angle - jaw_min) * 5
                jaw_angle = int(max(jaw_min, min(jaw_angle, jaw_max)))
                
                # Calculate normalized factor (0 = closed, 1 = open)
                factor = (jaw_angle - jaw_min) / float(jaw_max - jaw_min)
                # Map the factor to the upper lip's range
                upper_angle = int(upper_min + factor * (upper_max - upper_min))
                
                self.send_command(jaw_index, jaw_angle, arduino, jaw_name)
                self.send_command(upper_index, upper_angle, arduino, upper_name)              

                current_time = time.time()
                elapsed = current_time - prev_time
                sleep_time = frame_interval - elapsed
                print(f"Frame {i}: sleep for {sleep_time:.4f} seconds")
                if sleep_time > 0:
                    time.sleep(sleep_time)
                prev_time = time.time()
        
        def play_audio():
            playsound(audio_file)
        
        jaw_thread = threading.Thread(target=move_mouth)
        audio_thread = threading.Thread(target=play_audio)
        
        # Start both threads
        jaw_thread.start()
        audio_thread.start()
        
        audio_thread.join()
        jaw_thread.join()
        
        if plot_debug:
            import matplotlib.pyplot as plt
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


    def akira_open_hand(self, arduino, verbose=False):
        if verbose:
            print(f"Opening {arduino} hand.")
        if arduino in ["left", "right"]:
            for servo_name in self.finger_servos:
                servo_index, servo_rest, servo_min, servo_max, servo_current = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
                self.send_command(servo_index, servo_rest, arduino, servo_name, verbose=verbose)
                self.hand_status = "Open"
                assert self.hand_status in list(self.hand_status_options.keys())
        else:
            print(f"{arduino} arduino is not valid! Please try again!")

    def akira_half_close_hand(self, arduino, verbose=False):
        if verbose:
            print(f"Half closing {arduino} hand.")
        if arduino in ["left", "right"]:
            for servo_name in self.finger_servos:
                servo_index, servo_rest, servo_min, servo_max, servo_current = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
                self.send_command(servo_index, int(((servo_max - servo_min) / 2) + servo_min), arduino, servo_name, verbose=verbose)
                self.hand_status = "HalfClose"
                assert self.hand_status in list(self.hand_status_options.keys())
        else:
            print(f"{arduino} arduino is not valid! Please try again!")

    def akira_close_hand(self, arduino, verbose=False):
        if verbose:
            print(f"Closing {arduino} hand.")
        if arduino in ["left", "right"]:
            for servo_name in self.finger_servos:
                servo_index, servo_rest, servo_min, servo_max, servo_current = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
                if servo_rest == servo_min:
                    self.send_command(servo_index, servo_max, arduino, servo_name, verbose=verbose)
                elif servo_rest == servo_max:
                    self.send_command(servo_index, servo_min, arduino, servo_name, verbose=verbose)

                self.hand_status = "Close"
                assert self.hand_status in list(self.hand_status_options.keys())
        else:
            print(f"{arduino} arduino is not valid! Please try again!")

    def akira_thumbs_up(self, arduino, verbose=False):
        servo_name = "thumb"
        self.akira_raise_finger([servo_name], arduino, verbose)
        self.hand_status = "ThumbsUp"
        assert self.hand_status in list(self.hand_status_options.keys())

    def akira_index_up(self, arduino, verbose=False):
        servo_name = "index"
        self.akira_raise_finger([servo_name], arduino, verbose)
        self.hand_status = "IndexUp"
        assert self.hand_status in list(self.hand_status_options.keys())
        
    def akira_raise_finger(self, servo_name_list, arduino, verbose=False):
        self.akira_close_hand(arduino, verbose)

        if not isinstance(servo_name_list, list):
            servo_name_list = [servo_name_list]
            
        for servo_name in servo_name_list:
            if servo_name in self.finger_servos:
                servo_index, servo_rest, servo_min, servo_max, servo_current = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
                self.send_command(servo_index, servo_rest, arduino, servo_name, verbose=verbose)
        self.hand_status = "OtherUp"
        assert self.hand_status in list(self.hand_status_options.keys())

    def akira_move_hands_randomly(self, only_wrist=False, verbose=False):
        while self.move_hands_randomly:
            choice = random.choice(["left", "right", "both"])
            if choice == "both":
                arduinos_to_move = ["left", "right"]
            else:
                arduinos_to_move = [choice]
                
            for arduino in arduinos_to_move:
                wrist_name = "wrist"
                wrist_index, wrist_rest, wrist_min, wrist_max, wrist_current = self.get_servo_positions(servo_name=wrist_name, arduino=arduino)
                wrist_angle = np.random.normal(loc = wrist_rest, scale = wrist_max - wrist_rest)
                wrist_angle = int(max(wrist_min, min(wrist_max, wrist_angle)))
                self.send_command(wrist_index, wrist_angle, arduino, wrist_name, verbose=verbose)

                if not only_wrist:
                    finger_action = random.choice(list(self.hand_status_options.keys()))
                    if finger_action != "OtherUp":
                        self.hand_status_options[finger_action](arduino, verbose)                
            
            time.sleep(random.uniform(3, 7))

    def start_move_hands_randomly(self):
        self.move_hands_randomly = True

    def stop_move_hands_randomly(self):
        self.move_hands_randomly = False

    def get_shoulder_servo_data(self, arduino):
        shoulder_data = {}

        for servo_name in self.shoulder_servos:
            data = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
            if data is not None:
                shoulder_data[servo_name] = data
            else:
                print(f"Warning: Could not retrieve data for {servo_name} on {arduino} side.")

        return shoulder_data

    def akira_move_arms_randomly(self, verbose=False):
        while self.move_arms_randomly:
            choice = random.choice(["left", "right", "both"])
            if choice == "both":
                arduinos_to_move = ["left", "right"]
            else:
                arduinos_to_move = [choice]
        
            for arduino in arduinos_to_move:
                shoulder_name, omoplate_name, rotate_name, bicep_name = self.shoulder_servos

                shoulder_index, shoulder_rest, shoulder_min, shoulder_max, shoulder_current = self.get_servo_positions(servo_name=shoulder_name, arduino=arduino)
                omoplate_index, omoplate_rest, omoplate_min, omoplate_max, omoplate_current = self.get_servo_positions(servo_name=omoplate_name, arduino=arduino)
                rotate_index, rotate_rest, rotate_min, rotate_max, rotate_current = self.get_servo_positions(servo_name=rotate_name, arduino=arduino)
                bicep_index, bicep_rest, bicep_min, bicep_max, bicep_current = self.get_servo_positions(servo_name=bicep_name, arduino=arduino)

                shoulder_target = random.randint(shoulder_min + 5, shoulder_max - 5)
                omoplate_target = random.randint(omoplate_min + 5, omoplate_max - 5)
                rotate_target = random.randint(rotate_min + 5, rotate_max - 5)
                bicep_target = random.randint(bicep_min + 5, bicep_max - 5)

                steps = 2
                for _ in range(steps):
                    shoulder_current += (shoulder_target - shoulder_current) / steps
                    omoplate_current += (omoplate_target - omoplate_current) / steps
                    rotate_current += (rotate_target - rotate_current) / steps
                    bicep_current += (bicep_target - bicep_current) / steps

                    self.send_command(shoulder_index, int(shoulder_current), arduino, shoulder_name, verbose=verbose)
                    self.send_command(omoplate_index, int(omoplate_current), arduino, omoplate_name, verbose=verbose)
                    self.send_command(rotate_index, int(rotate_current), arduino, rotate_name, verbose=verbose)
                    self.send_command(bicep_index, int(bicep_current), arduino, bicep_name, verbose=verbose)

                    time.sleep(0.1)

            time.sleep(random.uniform(2, 6))
            
    def start_move_arms_randomly(self):
        self.move_arms_randomly = True

    def stop_move_arms_randomly(self):
        self.move_arms_randomly = False

    def all_rest(self, verbose=False):
        print(">>Setting all servos to their rest positions!")
        for arduino in ["left", "right"]:
            if arduino == "left":
                for servo_name in self.left_servos_list:
                    servo_index, servo_rest, servo_min, servo_max, servo_current = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
                    self.send_command(servo_index, servo_rest, arduino, servo_name, verbose=verbose)
                    time.sleep(0.1)
            if arduino == "right":
                for servo_name in self.right_servos_list:
                    servo_index, servo_rest, servo_min, servo_max, servo_current = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
                    self.send_command(servo_index, servo_rest, arduino, servo_name, verbose=verbose)
                    time.sleep(0.1)
                    
    def arms_rest(self, verbose=False):
        print(">>Setting all servos to their rest positions!")
        for arduino in ["left", "right"]:
            for servo_name in self.shoulder_servos :
                servo_index, servo_rest, servo_min, servo_max, servo_current = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
                self.send_command(servo_index, servo_rest, arduino, servo_name, verbose=verbose)
                time.sleep(0.1)

    def neck_rest(self, verbose=False):
        print(">>Setting all servos to their rest positions!")
        arduino = "left"
        for servo_name in self.neck_servos :
            servo_index, servo_rest, servo_min, servo_max, servo_current = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
            self.send_command(servo_index, servo_rest, arduino, servo_name, verbose=verbose)
            time.sleep(0.1)

    def test_any_servo_like_in_serial(self, servo_name, arduino, desired_position, verbose=True):
        servo_index, servo_rest, servo_min, servo_max, servo_current = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
        desired_position = int(max(servo_min, min(servo_max, desired_position)))
        self.send_command(servo_index, desired_position, arduino, servo_name, verbose=verbose)

    def plot_shoulder_positions(self):      
        fig, (ax_left, ax_right) = plt.subplots(2, 1, figsize=(6, 8))
        x = range(len(self.shoulder_servos))  # e.g. 0,1,2,3 for 4 shoulder servos
        all_positions = []
        
        for i, servo_name in enumerate(self.shoulder_servos):
            if servo_name in self.left_servos_list:
                servo_info = self.left_servos_list[servo_name]
                min_pos = servo_info["min_pos"]
                rest_pos = servo_info["rest_pos"]
                max_pos = servo_info["max_pos"]

                # Plot three points for the servo at x = i
                ax_left.scatter([i, i, i], [min_pos, rest_pos, max_pos])

                # Collect for global y-limits
                all_positions.extend([min_pos, rest_pos, max_pos])
            else:
                print(f"Warning: '{servo_name}' not in left_servos_list.")

        ax_left.set_title("Left Shoulder Servos")
        ax_left.set_ylabel("Position")
        ax_left.set_xticks(list(x))
        ax_left.set_xticklabels(self.shoulder_servos)

        for i, servo_name in enumerate(self.shoulder_servos):
            if servo_name in self.right_servos_list:
                servo_info = self.right_servos_list[servo_name]
                min_pos = servo_info["min_pos"]
                rest_pos = servo_info["rest_pos"]
                max_pos = servo_info["max_pos"]

                ax_right.scatter([i, i, i], [min_pos, rest_pos, max_pos])
                
                # Collect for global y-limits
                all_positions.extend([min_pos, rest_pos, max_pos])
            else:
                print(f"Warning: '{servo_name}' not in right_servos_list.")

        ax_right.set_title("Right Shoulder Servos")
        ax_right.set_ylabel("Position")
        ax_right.set_xticks(list(x))
        ax_right.set_xticklabels(self.shoulder_servos)

        if all_positions:
            margin = 5
            y_min = min(all_positions) - margin
            y_max = max(all_positions) + margin
            ax_left.set_ylim([y_min, y_max])
            ax_right.set_ylim([y_min, y_max])

        plt.tight_layout()
        plt.show()

        

if __name__ == "__main__":
    try:
        mc = MotionController(initialize_on_start=True)
        mc.move_jaw_and_play(plot_debug=True)
    finally:
        mc.close_connection()
    
    #mc.akira_close_eyes()
    #time.sleep(5)
    #mc.akira_open_eyes()
    #mc.start_move_head_randomly()
    #head_thread = threading.Thread(target=mc.akira_move_head_randomly)
    #head_thread.start()

    #mc.plot_shoulder_positions()
    
##    while True:
##        command = input("Command: ")
##        if command == "e":
##            break
##        elif command == "close hands":
##            mc.akira_close_hand("left", True)
##            mc.akira_close_hand("right", True)
##        elif command == "open hands":
##            mc.akira_open_hand("left", True)
##            mc.akira_open_hand("right", True)
##        elif command == "ok":
##            mc.akira_thumbs_up("left", True)
##            mc.akira_thumbs_up("right", True)
##        elif command == "point":
##            mc.akira_index_up("left", True)
##            mc.akira_index_up("right", True)
##        elif command == "half open":
##            mc.akira_half_close_hand("left", True)
##            mc.akira_half_close_hand("right", True)
##        elif command == "random_hands":
##            mc.akira_move_hands_randomly(True)
##        elif command == "individual testing":
##            while True:
##                user_input = input("Move servo: ")
##                if user_input == "e":
##                    break
##                servo_name, arduino, desired_position = tuple(user_input.strip().split())
##                desired_position = int(desired_position)
##                mc.test_any_servo_like_in_serial(servo_name, arduino, desired_position)
##
##        elif command == "random arm":
##            mc.akira_move_arms_randomly(True)
            
            
            
    
    
    
