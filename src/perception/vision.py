import mediapipe as mp
import collections
import numpy as np
import logging
import random
import torch
import time
import cv2
import sys
import os

from transformers import BlipProcessor, BlipForConditionalGeneration
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from action.motion_controller import MotionController


class Akira_See:
    def __init__(self, motion_controller=None):
        if motion_controller is None:
            print("Initializing Motion Controller...")
            try:
                self.motion_controller = MotionController()
                print("Motion Controller Initialized.")
                time.sleep(1)
            except Exception as e:
                print(f"Error initializing Motion Controller: {e}")
                print("Proceeding without motion control.")
                self.motion_controller = None
        else:
            self.motion_controller = motion_controller

        self.face_detected = False
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        #blip
        model_name = "Salesforce/blip-image-captioning-base"
        self.processor = BlipProcessor.from_pretrained(model_name)
        self.model = BlipForConditionalGeneration.from_pretrained(model_name)

        # Configure logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

        self.looking_at_person = True

    def list_cameras(self, max_tested=5):
        """
        Returns a list of indices for cameras that can be opened.
        By default, it checks camera indices 0 through 4.
        """
        available_cameras = []
        for index in range(max_tested):
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                available_cameras.append(index)
                cap.release()
        return available_cameras

    def test_camera(index):
        """
        Opens the camera at `index`, displays a live feed,
        and waits until 'q' is pressed to quit.
        """
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            print(f"Could not open camera {index}.")
            return

        print(f"Testing camera index {index}. Press 'q' to quit this camera.")
        while True:
            ret, frame = cap.read()
            if not ret:
                print(f"Failed to read frame from camera {index}.")
                break

            cv2.imshow(f"Camera {index}", frame)

            # Press 'q' to close the current camera window
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyWindow(f"Camera {index}")

    def try_both(self):
        cap0 = cv2.VideoCapture(0)
        cap1 = cv2.VideoCapture(2)

        # Check if both cameras opened successfully
        if not cap0.isOpened():
            print("Camera 0 could not be opened.")
        if not cap1.isOpened():
            print("Camera 1 could not be opened.")

        if cap0.isOpened() and cap1.isOpened():
            print("Both cameras opened successfully. Press 'q' to quit.")
            while True:
                ret0, frame0 = cap0.read()
                ret1, frame1 = cap1.read()

                if ret0 and ret1:
                    # Resize for display purposes (optional)
                    frame0 = cv2.resize(frame0, (320, 240))
                    frame1 = cv2.resize(frame1, (320, 240))

                    # Concatenate the two frames horizontally
                    combined = cv2.hconcat([frame0, frame1])

                    cv2.imshow("Camera 0 and 1", combined)
                else:
                    print("Could not read frames from both cameras.")
                    break

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        # Release everything when done
        cap0.release()
        cap1.release()
        cv2.destroyAllWindows()

    def describe_what_akira_sees(self, image_input, eliminate_photo=True, annotate_photo=False) -> str:
        """
        Generate a caption for the given image.
        
        Args:
            image_input: Can be a file path (str) or a PIL.Image.Image instance.
        
        Returns:
            A string describing the image.
        """
        if image_input is None:
            return None
        if isinstance(image_input, str):
            image = Image.open(image_input)
        else:
            image = image_input
        
        # Load image from file path if needed
        if isinstance(image_input, str):
            image = Image.open(image_input)
        else:
            image = image_input

        # Preprocess the image and generate the caption
        inputs = self.processor(images=image, return_tensors="pt")
        outputs = self.model.generate(**inputs)
        caption = self.processor.decode(outputs[0], skip_special_tokens=True)

        if eliminate_photo:
            try:
                os.remove(image_input)
                print("Deleted!")
            except FileNotFoundError:
                print("That file doesn't exist.")
            except PermissionError:
                print("You don't have permission to delete this file.")
            except Exception as e:
                print(f"Unexpected error: {e}")
        else:
            if annotate_photo:
                self.add_text_top_left(image_input, caption, image_input)
        
        return caption

    def add_text_top_left(self, image_path, text, output_path, padding=10, font_size=24):
        image = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

        position = (padding, padding)
        draw.text(position, text, fill="white", font=font)

        image.save(output_path)
        print(f"Text added to top-left corner and saved to {output_path}")      


    def take_photo(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        photos_folder = "photos"
        script_dir = os.path.join(script_dir, photos_folder)
        
        filename = "photo_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
        file_path = os.path.join(script_dir, filename)

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Camera index 0 cannot be accessed, trying camera index 2.")
            cap = cv2.VideoCapture(2)
            if not cap.isOpened():
                print("Camera index 2 cannot be accessed either.")
                return None

        print("Taking a picture!")

        ret, frame = cap.read()
        cap.release()

        if not ret:
            print("Picture was not able to be taken...")
            return None

        cv2.imwrite(file_path, frame)
        print(f"Picture saved in: {file_path}")
        return file_path

    def look_at_face(self, camera_index: int = 0, show_video: bool = False, exit_when_centered: bool = True) -> None:
        while self.looking_at_person:
            # Configuration parameters
            SLEEP_INTERVAL = 0.1
            STEP_SIZE_YAW = 5
            STEP_SIZE_PITCH = -5
            TOLERANCE_RATIO = 0.10

            arduino = "left"
            neck_name, _, rot_name = self.motion_controller.neck_servos
            neck_index, neck_rest, neck_min, neck_max, neck_current = self.motion_controller.get_servo_positions(
                servo_name=neck_name, arduino=arduino)
            rot_index, rot_rest, rot_min, rot_max, rot_current = self.motion_controller.get_servo_positions(
                servo_name=rot_name, arduino=arduino)

            self.logger.info(f"Starting face tracking on camera index {camera_index}...")

            # Initialize the camera
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                self.logger.error(f"Could not open camera {camera_index}. Trying alternative camera index 2.")
                alternative_index = 2
                cap = cv2.VideoCapture(alternative_index)
                if not cap.isOpened():
                    self.logger.error(f"Could not open camera {alternative_index}.")
                    return
                else:
                    camera_index = alternative_index

            ret, frame = cap.read()
            if not ret:
                self.logger.error("Could not read initial frame from camera.")
                cap.release()
                return

            frame_height, frame_width, _ = frame.shape
            frame_center_x = frame_width // 2
            frame_center_y = frame_height // 2
            center_tolerance_x = int(frame_width * TOLERANCE_RATIO)
            center_tolerance_y = int(frame_height * TOLERANCE_RATIO)

            # Use a context manager for the face detection module
            with self.mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detection:
                try:
                    while True:
                        time.sleep(SLEEP_INTERVAL)
                        ret, frame = cap.read()
                        if not ret:
                            self.logger.error("Failed to capture frame.")
                            break

                        # Flip and convert color space for face detection
                        frame = cv2.flip(frame, 1)
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        results = face_detection.process(rgb_frame)

                        face_detected = False
                        face_center_x = None
                        face_center_y = None

                        # Process detections if a face is found
                        if results.detections:
                            face_detected = True
                            detection = results.detections[0]
                            bboxC = detection.location_data.relative_bounding_box
                            ih, iw, _ = frame.shape
                            xmin = int(bboxC.xmin * iw)
                            ymin = int(bboxC.ymin * ih)
                            width = int(bboxC.width * iw)
                            height = int(bboxC.height * ih)
                            face_center_x = xmin + width // 2
                            face_center_y = ymin + height // 2

                            if show_video:
                                cv2.rectangle(frame, (xmin, ymin), (xmin + width, ymin + height), (0, 255, 0), 2)
                                cv2.circle(frame, (face_center_x, face_center_y), 5, (0, 0, 255), -1)

                        self.face_detected = face_detected

                        # Calculate error and determine adjustment
                        if face_detected and self.motion_controller is not None:
                            error_x = frame_center_x - face_center_x
                            error_y = frame_center_y - face_center_y

                            adjust_rothead = int(STEP_SIZE_YAW * np.sign(error_x)) if abs(error_x) > center_tolerance_x else 0
                            adjust_neck = int(STEP_SIZE_PITCH * np.sign(error_y)) if abs(error_y) > center_tolerance_y else 0

                            if adjust_neck != 0 or adjust_rothead != 0:
                                self.logger.info(f"Error X: {error_x}, Error Y: {error_y} -> Adjust Neck: {adjust_neck}, Adjust Rothead: {adjust_rothead}")
                                try:
                                    neck_current += adjust_neck
                                    rot_current += adjust_rothead

                                    # Ensure servo angles remain within defined limits
                                    neck_current = max(neck_min, min(neck_current, neck_max))
                                    rot_current = max(rot_min, min(rot_current, rot_max))

                                    self.motion_controller.set_current_pos_servo(neck_name, arduino, neck_current)
                                    self.motion_controller.set_current_pos_servo(rot_name, arduino, rot_current)
                                    self.motion_controller.send_command(neck_index, neck_current, arduino, neck_name)
                                    self.motion_controller.send_command(rot_index, rot_current, arduino, rot_name)

                                    time.sleep(SLEEP_INTERVAL)
                                except Exception as e:
                                    self.logger.error(f"Error sending command to motion controller: {e}")

                            # Exit if the face is centered within tolerance
                            if exit_when_centered and abs(error_x) <= center_tolerance_x and abs(error_y) <= center_tolerance_y:
                                self.logger.info("Face is centered. Exiting face tracking.")
                                break

                        # Draw center tolerance region and display the video
                        if show_video:
                            cv2.rectangle(frame,
                                          (frame_center_x - center_tolerance_x, frame_center_y - center_tolerance_y),
                                          (frame_center_x + center_tolerance_x, frame_center_y + center_tolerance_y),
                                          (255, 255, 0), 1)
                            cv2.circle(frame, (frame_center_x, frame_center_y), 5, (255, 255, 255), -1)
                            cv2.imshow('Face Tracking', frame)

                        if cv2.waitKey(5) & 0xFF == ord('q'):
                            self.logger.info("'q' pressed, exiting.")
                            break
                finally:
                    self.logger.info("Releasing camera and destroying windows...")
                    cap.release()
                    if show_video:
                        cv2.destroyAllWindows()

            self.logger.info("Face tracking finished.")
            time.sleep(random.uniform(1, 3))

    def start_looking_at(self):
        self.looking_at_person = True

    def stop_looking_at(self):
        self.looking_at_person = False



# --- Main execution block ---
if __name__ == "__main__":
    akira_vision = Akira_See()
    #akira_vision.look_at_face(camera_index=0, exit_when_centered=False)
    
    for _ in range(3):
        print(akira_vision.describe_what_akira_sees(akira_vision.take_photo()))
        time.sleep(5)
    
    
