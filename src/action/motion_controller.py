from playsound import playsound
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import threading
import librosa
import random
import serial
import queue
import time
import os
import logging

# Set up logging: logs will be written to 'motion_controller.log' and output to the console.
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# File handler – logs to a file
fh = logging.FileHandler("motion_controller.log")
fh.setLevel(logging.DEBUG)
# Console handler – logs to the console
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

class MotionController:
    def __init__(
        self,
        left_port="/dev/ttyACM0",
        right_port="/dev/ttyACM1",
        baud_rate=9600,
        left_servos_file="servos_data_left.csv",
        right_servos_file="servos_data_right.csv",
        initialize_on_start=True,
        verbose=False
        ):

        self.verbose = verbose
        self.logger = logger  # use the module-level logger

        current_dir = os.path.dirname(os.path.abspath(__file__))
        left_servos_file = os.path.join(current_dir, left_servos_file)
        right_servos_file = os.path.join(current_dir, right_servos_file)
        
        self.left_port = left_port
        self.right_port = right_port
        
        self.ardunio_left = None
        self.arduino_right = None

        self.arduinos_connected = False
        self.baud_rate = baud_rate

        self.connection_status = False

        if initialize_on_start:
            self.initiate_connection()

        self.left_command_queue = queue.Queue()
        self.right_command_queue = queue.Queue()
        
        self.left_worker_thread = threading.Thread(target=self.process_queue, args=("left",), daemon=True)
        self.right_worker_thread = threading.Thread(target=self.process_queue, args=("right",), daemon=True)
        self.left_worker_thread.start()
        self.right_worker_thread.start()
        

        self.left_servos_list, self.right_servos_list = self.load_servo_info(left_servos_file, right_servos_file)
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
            "Open": self.akira_open_hand,
            "Close": self.akira_close_hand,
            "HalfClose": self.akira_half_close_hand,
            "IndexUp": self.akira_index_up,
            "ThumbsUp": self.akira_thumbs_up,
            "OtherUp": self.akira_raise_finger
            }
        self.hand_status = "Open"

        self.lock_left = threading.Lock()
        self.lock_right = threading.Lock()

        # To avoid too many commands being sent to each arduino
        self.command_counters = {
            "left": {"count": 0, "window_start": time.time()},
            "right": {"count": 0, "window_start": time.time()}
        }
        # Maximum commands allowed per time window (e.g., 10 per second)
        self.max_commands = 10
        # Length of the time window (in seconds)
        self.window_duration = 1.0

    def process_queue_slow(self, arduino):
        q = self.left_command_queue if arduino == "left" else self.right_command_queue
        while self.connection_status:
            try:
                command = q.get(timeout=1)
            except queue.Empty:
                continue
            if command is None:
                q.task_done()
                break

            servo_index, angle, servo_name = command

            if arduino == "left":
                with self.lock_left:
                    # Flush input buffer before sending the command
                    self.arduino_left.reset_input_buffer()
                    self.arduino_left.write(f"{servo_index} {angle}\n".encode())
                    # Wait a short period to allow Arduino to respond
                    time.sleep(0.05)
                    # Poll for a valid response
                    timeout = time.time() + 1.0  # wait up to one second
                    response = ""
                    while time.time() < timeout:
                        if self.arduino_left.in_waiting:
                            response = self.arduino_left.readline().decode().strip()
                            if response.strip().upper() == "OK":
                                break
                        else:
                            time.sleep(0.01)
            else:
                with self.lock_right:
                    self.arduino_right.reset_input_buffer()
                    self.arduino_right.write(f"{servo_index} {angle}\n".encode())
                    time.sleep(0.05)
                    timeout = time.time() + 1.0
                    response = ""
                    while time.time() < timeout:
                        if self.arduino_right.in_waiting:
                            response = self.arduino_right.readline().decode().strip()
                            if response.strip().upper() == "OK":
                                break
                        else:
                            time.sleep(0.01)

            self.logger.info(f"{arduino} command for {servo_name} sent with angle {angle}. Response: {response}")

            if response.strip().upper() != "OK":
                self.logger.warning(f"{arduino} command for {servo_name} did not receive an OK response.")
                # Optionally, re-enqueue the command for a retry

            q.task_done()

    def process_queue(self, arduino):
        """Worker thread for processing the command queue for the given Arduino."""
        q = self.left_command_queue if arduino == "left" else self.right_command_queue
        while self.connection_status:
            try:
                command = q.get(timeout=1)
            except queue.Empty:
                continue  # Try again to check connection_status
            
            if command is None:
                # Received sentinel value; break out of the loop.
                q.task_done()
                break

            servo_index, angle, servo_name = command

            # Send the command while ensuring only one thread is writing to the serial port
            if arduino == "left":
                with self.lock_left:
                    self.arduino_left.write(f"{servo_index} {angle}\n".encode())
                    response = self.arduino_left.readline().decode().strip()
            else:
                with self.lock_right:
                    self.arduino_right.write(f"{servo_index} {angle}\n".encode())
                    response = self.arduino_right.readline().decode().strip()

            self.logger.info(f"{arduino} command for {servo_name} sent with angle {angle}. Response: {response}")

            #if response != "OK":
            #    self.logger.warning(f"{arduino} command for {servo_name} did not receive an OK response.")
                # Optionally: re-enqueue command here if desired
            q.task_done()


    def send_command(self, servo_index, angle, arduino, servo_name):
        """
        Instead of immediately writing to the serial port,
        this method enqueues the command for processing.
        """
        if not self.connection_status:
            self.logger.warning(f"Connection status: {self.connection_status}")
            return

        sevo_index, _, min_pos, max_pos, _ = self.get_servo_positions(servo_name, arduino)

        if angle < min_pos:
            angle = min_pos
        elif angle > max_pos:
            angle = max_pos
        if not isinstance(angle, int):
            angle = int(angle)

        # Build the command tuple
        command = (servo_index, angle, servo_name)
        if arduino == "left":
            self.left_command_queue.put(command)
        elif arduino == "right":
            self.right_command_queue.put(command)
        else:
            self.logger.error(f"{arduino} arduino does not exist. Please try either 'left' or 'right'!")

    def load_servo_info(self, left_servos_file, right_servos_file):
            df_left = pd.read_csv(left_servos_file)
            df_right = pd.read_csv(right_servos_file)

            left_servos_list = df_left.to_dict(orient="records")
            right_servos_list = df_right.to_dict(orient="records")

            for index in range(len(left_servos_list)):
                left_servos_list[index]["index"] = index
                left_servos_list[index]["current"] = left_servos_list[index]["rest_pos"]
            left_servos_list = {left_servos_list[index]["name"]: left_servos_list[index] for index in range(len(left_servos_list))}
            for index in range(len(right_servos_list)):
                right_servos_list[index]["index"] = index
                right_servos_list[index]["current"] = right_servos_list[index]["rest_pos"]
            right_servos_list = {right_servos_list[index]["name"]: right_servos_list[index] for index in range(len(right_servos_list))}

            return left_servos_list, right_servos_list

        
    def initiate_connection(self):
        self.arduino_left = serial.Serial(self.left_port, self.baud_rate, timeout=1)
        self.arduino_right = serial.Serial(self.right_port, self.baud_rate, timeout=1)
        time.sleep(2)  # Give them time to initialize

        self.logger.info("Connection has been successfully initiated!")
        self.connection_status = True

    def close_connection(self):
        if self.arduino_left is not None and self.arduino_right is not None:
            time.sleep(5)
            self.all_rest()
            time.sleep(15)

            # Insert sentinel values into each queue so the workers can exit their loop.
            self.left_command_queue.put(None)
            self.right_command_queue.put(None)

            # Optionally wait for the queues to clear and join the threads.
            self.left_worker_thread.join(timeout=2)
            self.right_worker_thread.join(timeout=2)
            
            self.arduino_left.close()
            self.arduino_right.close()
            self.logger.info("Connection has been successfully closed!")
            self.connection_status = False
        else:
            self.logger.warning("Connection has not been initiated!")

    def get_servo_positions(self, servo_name, arduino):
        if arduino == "left":
            servo_list = self.left_servos_list
        elif arduino == "right":
            servo_list = self.right_servos_list
        else:
            self.logger.error(f"There is no {arduino} arduino. Please try either 'left' or 'right'.")
            return None
        try:
            min_pos = servo_list[servo_name]["min_pos"]
            max_pos = servo_list[servo_name]["max_pos"]
            rest_pos = servo_list[servo_name]["rest_pos"]
            servo_index = servo_list[servo_name]["index"]
            servo_current = servo_list[servo_name]["current"]
            
            return servo_index, rest_pos, min_pos, max_pos, servo_current
        
        except Exception as e:
            self.logger.exception("We have an exception: %s", e)
            return None

    def set_current_pos_servo(self, servo_name, arduino, angle):
        if arduino == "left":
            self.left_servos_list[servo_name]["current"] = angle
        elif arduino == "right":
            self.right_servos_list[servo_name]["current"] = angle

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
            
            distance = abs(neck_target - neck_rest)
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
        y, sr = librosa.load(audio_file, sr=None)
        frame_length = 1024
        hop_length = 512
        energy = np.array([
            sum(abs(y[i:i+frame_length]**2)) for i in range(0, len(y), hop_length)
        ])
        norm_energy = (energy - energy.min()) / (energy.max() - energy.min())
        jaw_name = "Jaw"
        jaw_index, jaw_rest, jaw_min, jaw_max, _ = self.get_servo_positions(jaw_name, arduino)
        upper_name = "Upper_Lip"
        upper_index, upper_rest, upper_min, upper_max, _ = self.get_servo_positions(upper_name, arduino)
        threshold_half = 0.1
        threshold_full = 0.3
        
        def determine_state(n_energy):
            if n_energy < threshold_half:
                return "closed"
            elif n_energy < threshold_full:
                return "half"
            else:
                return "full"
        
        state_angles = {
            "closed": {"jaw": jaw_min, "upper": upper_min},
            "half": {"jaw": int((jaw_min + jaw_max) / 2), "upper": int((upper_min + upper_max) / 2)},
            "full": {"jaw": jaw_max, "upper": upper_max}
        }
        frame_interval = hop_length / sr
        audio_duration = len(y) / sr
        audio_finished = threading.Event()
        current_state = None
        
        def move_mouth():
            nonlocal current_state
            start_time = time.time()
            while (time.time() - start_time) < audio_duration and not audio_finished.is_set():
                elapsed = time.time() - start_time
                frame_idx = int(elapsed / frame_interval)
                if frame_idx >= len(norm_energy):
                    break
                desired_state = determine_state(norm_energy[frame_idx])
                if desired_state != current_state:
                    angles = state_angles[desired_state]
                    self.send_command(jaw_index, angles["jaw"], arduino, jaw_name)
                    self.send_command(upper_index, angles["upper"], arduino, upper_name)
                    current_state = desired_state
                    self.logger.info(f"Elapsed {elapsed:.2f}s, frame {frame_idx}: Changed state to {desired_state}")
                time.sleep(0.005)
            final_state = state_angles["closed"]
            self.send_command(jaw_index, final_state["jaw"], arduino, jaw_name)
            self.send_command(upper_index, final_state["upper"], arduino, upper_name)
            self.logger.info("Audio finished, stopping mouth movement.")
        
        def play_audio():
            playsound(audio_file)
            audio_finished.set()
        
        jaw_thread = threading.Thread(target=move_mouth)
        audio_thread = threading.Thread(target=play_audio)
        
        jaw_thread.start()
        audio_thread.start()
        
        audio_thread.join()
        jaw_thread.join()
        
        if plot_debug:
            plt.figure(figsize=(10, 8))
            plt.subplot(4, 1, 1)
            plt.plot(y)
            plt.title("Audio Signal")
            plt.subplot(4, 1, 2)
            plt.plot(energy)
            plt.title("Energy")
            plt.subplot(4, 1, 3)
            plt.plot(norm_energy)
            plt.title("Normalized Energy")
            state_numeric = [0 if determine_state(ne) == "closed" 
                             else 1 if determine_state(ne) == "half" 
                             else 2 for ne in norm_energy]
            plt.subplot(4, 1, 4)
            plt.plot(state_numeric, 'o-')
            plt.title("Mouth State (0=closed, 1=half, 2=full)")
            plt.tight_layout()
            plt.show()

    def akira_open_hand(self, arduino):
        if self.verbose:
            self.logger.info(f"Opening {arduino} hand.")
        if arduino in ["left", "right"]:
            for servo_name in self.finger_servos:
                servo_index, servo_rest, servo_min, servo_max, servo_current = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
                self.send_command(servo_index, servo_rest, arduino, servo_name)
                self.hand_status = "Open"
                assert self.hand_status in list(self.hand_status_options.keys())
        else:
            self.logger.error(f"{arduino} arduino is not valid! Please try again!")

    def akira_half_close_hand(self, arduino):
        if self.verbose:
            self.logger.info(f"Half closing {arduino} hand.")
        if arduino in ["left", "right"]:
            for servo_name in self.finger_servos:
                servo_index, servo_rest, servo_min, servo_max, servo_current = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
                self.send_command(servo_index, int(((servo_max - servo_min) / 2) + servo_min), arduino, servo_name)
                self.hand_status = "HalfClose"
                assert self.hand_status in list(self.hand_status_options.keys())
        else:
            self.logger.error(f"{arduino} arduino is not valid! Please try again!")

    def akira_close_hand(self, arduino):
        if self.verbose:
            self.logger.info(f"Closing {arduino} hand.")
        if arduino in ["left", "right"]:
            for servo_name in self.finger_servos:
                servo_index, servo_rest, servo_min, servo_max, servo_current = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
                if servo_rest == servo_min:
                    self.send_command(servo_index, servo_max, arduino, servo_name)
                elif servo_rest == servo_max:
                    self.send_command(servo_index, servo_min, arduino, servo_name)
                self.hand_status = "Close"
                assert self.hand_status in list(self.hand_status_options.keys())
        else:
            self.logger.error(f"{arduino} arduino is not valid! Please try again!")

    def akira_thumbs_up(self, arduino):
        servo_name = "thumb"
        self.akira_raise_finger([servo_name], arduino)
        self.hand_status = "ThumbsUp"
        assert self.hand_status in list(self.hand_status_options.keys())

    def akira_index_up(self, arduino):
        servo_name = "index"
        self.akira_raise_finger([servo_name], arduino)
        self.hand_status = "IndexUp"
        assert self.hand_status in list(self.hand_status_options.keys())
        
    def akira_raise_finger(self, servo_name_list, arduino):
        self.akira_close_hand(arduino)
        if not isinstance(servo_name_list, list):
            servo_name_list = [servo_name_list]
        for servo_name in servo_name_list:
            if servo_name in self.finger_servos:
                servo_index, servo_rest, servo_min, servo_max, servo_current = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
                self.send_command(servo_index, servo_rest, arduino, servo_name)
        self.hand_status = "OtherUp"
        assert self.hand_status in list(self.hand_status_options.keys())

    def akira_move_hands_randomly(self, only_wrist=False):
        while self.move_hands_randomly:
            choice = random.choice(["left", "right", "both"])
            if choice == "both":
                arduinos_to_move = ["left", "right"]
            else:
                arduinos_to_move = [choice]
                
            for arduino in arduinos_to_move:
                wrist_name = "wrist"
                wrist_index, wrist_rest, wrist_min, wrist_max, wrist_current = self.get_servo_positions(servo_name=wrist_name, arduino=arduino)
                wrist_angle = np.random.normal(loc=wrist_rest, scale=wrist_max - wrist_rest)
                wrist_angle = int(max(wrist_min, min(wrist_max, wrist_angle)))
                self.send_command(wrist_index, wrist_angle, arduino, wrist_name)

                if not only_wrist:
                    finger_action = random.choice(list(self.hand_status_options.keys()))
                    if finger_action != "OtherUp":
                        self.hand_status_options[finger_action](arduino)                
            
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
                self.logger.warning(f"Warning: Could not retrieve data for {servo_name} on {arduino} side.")
        return shoulder_data

    def akira_move_arms_randomly(self):
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

                    self.send_command(shoulder_index, int(shoulder_current), arduino, shoulder_name)
                    self.send_command(omoplate_index, int(omoplate_current), arduino, omoplate_name)
                    self.send_command(rotate_index, int(rotate_current), arduino, rotate_name)
                    self.send_command(bicep_index, int(bicep_current), arduino, bicep_name)

                    time.sleep(0.1)

            time.sleep(random.uniform(2, 6))
            
    def start_move_arms_randomly(self):
        self.move_arms_randomly = True

    def stop_move_arms_randomly(self):
        self.move_arms_randomly = False

    def all_rest(self):
        self.logger.info(">>Setting all servos to their rest positions!")
        for arduino in ["left", "right"]:
            if arduino == "left":
                for servo_name in self.left_servos_list:
                    servo_index, servo_rest, servo_min, servo_max, servo_current = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
                    self.send_command(servo_index, servo_rest, arduino, servo_name)
                    time.sleep(0.1)
            if arduino == "right":
                for servo_name in self.right_servos_list:
                    servo_index, servo_rest, servo_min, servo_max, servo_current = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
                    self.send_command(servo_index, servo_rest, arduino, servo_name)
                    time.sleep(0.1)
                    
    def arms_rest(self):
        self.logger.info(">>Setting all servos to their rest positions!")
        for arduino in ["left", "right"]:
            for servo_name in self.shoulder_servos:
                servo_index, servo_rest, servo_min, servo_max, servo_current = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
                self.send_command(servo_index, servo_rest, arduino, servo_name)
                time.sleep(0.1)

    def neck_rest(self):
        self.logger.info(">>Setting all servos to their rest positions!")
        arduino = "left"
        for servo_name in self.neck_servos:
            servo_index, servo_rest, servo_min, servo_max, servo_current = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
            self.send_command(servo_index, servo_rest, arduino, servo_name)
            time.sleep(0.1)

    def test_any_servo_like_in_serial(self, servo_name, arduino, desired_position):
        servo_index, servo_rest, servo_min, servo_max, servo_current = self.get_servo_positions(servo_name=servo_name, arduino=arduino)
        desired_position = int(max(servo_min, min(servo_max, desired_position)))
        self.send_command(servo_index, desired_position, arduino, servo_name)

    def plot_shoulder_positions(self):      
        fig, (ax_left, ax_right) = plt.subplots(2, 1, figsize=(6, 8))
        x = range(len(self.shoulder_servos))
        all_positions = []
        
        for i, servo_name in enumerate(self.shoulder_servos):
            if servo_name in self.left_servos_list:
                servo_info = self.left_servos_list[servo_name]
                min_pos = servo_info["min_pos"]
                rest_pos = servo_info["rest_pos"]
                max_pos = servo_info["max_pos"]
                ax_left.scatter([i, i, i], [min_pos, rest_pos, max_pos])
                all_positions.extend([min_pos, rest_pos, max_pos])
            else:
                self.logger.warning(f"Warning: '{servo_name}' not in left_servos_list.")

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
                all_positions.extend([min_pos, rest_pos, max_pos])
            else:
                self.logger.warning(f"Warning: '{servo_name}' not in right_servos_list.")

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
        mc = MotionController(initialize_on_start=True, verbose=True)
    
        while True:
            command = input("Command: ")
            if command == "e":
                break
            elif command == "close hands":
                mc.akira_close_hand("left")
                mc.akira_close_hand("right")
            elif command == "open hands":
                mc.akira_open_hand("left")
                mc.akira_open_hand("right")
            elif command == "ok":
                mc.akira_thumbs_up("left")
                mc.akira_thumbs_up("right")
            elif command == "point":
                mc.akira_index_up("left")
                mc.akira_index_up("right")
            elif command == "half open":
                mc.akira_half_close_hand("left")
                mc.akira_half_close_hand("right")
            elif command == "open eyes":
                mc.akira_open_eyes()
            elif command == "close eyes":
                mc.akira_close_eyes()
            elif command == "random_hands":
                mc.akira_move_hands_randomly()
            elif command == "individual testing":
                while True:
                    user_input = input("Move servo: ")
                    if user_input == "e":
                        break
                    servo_name, arduino, desired_position = tuple(user_input.strip().split())
                    desired_position = int(desired_position)
                    mc.test_any_servo_like_in_serial(servo_name, arduino, desired_position)
            elif command == "random arm":
                mc.akira_move_arms_randomly()
            elif command == "talk":
                mc.move_jaw_and_play(plot_debug=True)
            elif command == "blink":
                proceed = True
                y = 0
                while proceed:
                    # Assuming you want to call a blink method here
                    mc.akira_close_eyes()
                    mc.akira_open_eyes()
                    if y == 5:
                        proceed = False
                        break
                    time.sleep(random.uniform(3, 6))
                    y += 1
            else:
                logger.info("Wrong command!")
    finally:
        mc.close_connection()
