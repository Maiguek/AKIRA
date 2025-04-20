import mediapipe as mp
import collections
import numpy as np
import threading
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
        
    @staticmethod
    def list_cameras(max_tested=5):
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

    @staticmethod
    def try_both():                
        #cv2.namedWindow("Camera 0 and 1", cv2.WINDOW_NORMAL)
        #cv2.resizeWindow("Camera 0 and 1", 640, 240)
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

                if cv2.waitKey(30) & 0xFF == ord('q'):
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

    def look_at_face_main(self, camera_index: int = 0, show_video: bool = False, exit_when_centered: bool = True) -> None:
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

    def look_at_face(self, camera_index: int = 0, show_video: bool = False, exit_when_centered: bool = True) -> None:
        # Configuration parameters
        SLEEP_INTERVAL = 0.05   # faster loop for smoother control
        TOLERANCE_RATIO = 0.05  # tighter deadzone

        # PID gains — you’ll need to tune these for your hardware!
        Kp_yaw, Ki_yaw, Kd_yaw = 0.03, 0.0001, 0.005
        Kp_pitch, Ki_pitch, Kd_pitch = 0.03, 0.0001, 0.005

        # State for PID
        integral_x = 0.0
        integral_y = 0.0
        prev_error_x = 0.0
        prev_error_y = 0.0
        last_time = time.time()

        arduino = "left"
        neck_name, _, rot_name = self.motion_controller.neck_servos
        neck_index, neck_rest, neck_min, neck_max, neck_current = self.motion_controller.get_servo_positions(
            servo_name=neck_name, arduino=arduino)
        rot_index, rot_rest, rot_min, rot_max, rot_current = self.motion_controller.get_servo_positions(
            servo_name=rot_name, arduino=arduino)

        self.logger.info(f"Starting face tracking on camera index {camera_index}...")

        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            self.logger.error(f"Could not open camera {camera_index}.")
            return

        ret, frame = cap.read()
        if not ret:
            self.logger.error("Could not read initial frame from camera.")
            cap.release()
            return

        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2
        tol_x = int(w * TOLERANCE_RATIO)
        tol_y = int(h * TOLERANCE_RATIO)

        with self.mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detection:
            try:
                while True:
                    now = time.time()
                    dt = now - last_time
                    last_time = now

                    time.sleep(SLEEP_INTERVAL)
                    ret, frame = cap.read()
                    if not ret:
                        self.logger.error("Failed to capture frame.")
                        break

                    frame = cv2.flip(frame, 1)
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = face_detection.process(rgb)

                    if results.detections:
                        # get the first face
                        bbox = results.detections[0].location_data.relative_bounding_box
                        x = int((bbox.xmin + bbox.width / 2) * w)
                        y = int((bbox.ymin + bbox.height / 2) * h)

                        if show_video:
                            cv2.rectangle(frame, (int(bbox.xmin*w), int(bbox.ymin*h)),
                                          (int((bbox.xmin+bbox.width)*w), int((bbox.ymin+bbox.height)*h)),
                                          (0,255,0), 2)
                            cv2.circle(frame, (x,y), 5, (0,0,255), -1)

                        # compute error
                        error_x = cx - x
                        error_y = cy - y

                        # deadzone
                        if abs(error_x) > tol_x or abs(error_y) > tol_y:
                            # PID for yaw (rothead)
                            integral_x += error_x * dt
                            derivative_x = (error_x - prev_error_x) / dt if dt > 0 else 0.0
                            command_x = (Kp_yaw * error_x +
                                         Ki_yaw * integral_x +
                                         Kd_yaw * derivative_x)

                            # PID for pitch (neck)
                            integral_y += error_y * dt
                            derivative_y = (error_y - prev_error_y) / dt if dt > 0 else 0.0
                            command_y = (Kp_pitch * error_y +
                                         Ki_pitch * integral_y +
                                         Kd_pitch * derivative_y)

                            prev_error_x, prev_error_y = error_x, error_y

                            # round and clamp to servo limits
                            d_rot = int(np.clip(command_x, rot_min - rot_current, rot_max - rot_current))
                            d_neck = int(np.clip(command_y, neck_min - neck_current, neck_max - neck_current))

                            rot_current  += d_rot
                            neck_current += d_neck

                            self.logger.debug(f"PID dx={command_x:.2f}, dy={command_y:.2f} → Δrot={d_rot}, Δneck={d_neck}")

                            # send commands
                            try:
                                self.motion_controller.set_current_pos_servo(rot_name, arduino, rot_current)
                                self.motion_controller.set_current_pos_servo(neck_name, arduino, neck_current)
                                self.motion_controller.send_command(rot_index, rot_current, arduino, rot_name)
                                self.motion_controller.send_command(neck_index, neck_current, arduino, neck_name)
                            except Exception as e:
                                self.logger.error(f"Motion controller error: {e}")
                        else:
                            # centered within tolerance?
                            if exit_when_centered:
                                self.logger.info("Centered; exiting.")
                                break

                    # draw the deadzone
                    if show_video:
                        cv2.rectangle(frame,
                                      (cx - tol_x, cy - tol_y),
                                      (cx + tol_x, cy + tol_y),
                                      (255,255,0), 1)
                        cv2.circle(frame, (cx, cy), 5, (255,255,255), -1)
                        cv2.imshow('Face Tracking', frame)
                        if cv2.waitKey(5) & 0xFF == ord('q'):
                            self.logger.info("'q' pressed, exiting.")
                            break

            finally:
                self.logger.info("Cleaning up...")
                cap.release()
                if show_video:
                    cv2.destroyAllWindows()

        self.logger.info("Face tracking finished.")

    def look_at_face_stereo(self,
                        left_cam: int = 0,
                        right_cam: int = 2,
                        show_video: bool = False,
                        exit_when_centered: bool = False) -> None:
        print("Looking at face stereo!")
        # PID gains (tune these!)
        Kp, Ki, Kd = 0.03, 0.0001, 0.005
        SLEEP = 0.05
        TOLERANCE = 0.05  # as fraction of frame dims

        # PID state
        int_x = int_y = 0.0
        prev_err_x = prev_err_y = 0.0
        last = time.time()

        # open both cameras
        capL = cv2.VideoCapture(left_cam)
        capR = cv2.VideoCapture(right_cam)
        if not capL.isOpened() or not capR.isOpened():
            self.logger.error("Cannot open both cameras.")
            return

        # grab one frame to get size
        retL, frameL = capL.read()
        retR, frameR = capR.read()
        if not (retL and retR):
            self.logger.error("Failed to read initial frames.")
            return
        h, w, _ = frameL.shape
        cx, cy = w//2, h//2
        tol_x = int(w * TOLERANCE)
        tol_y = int(h * TOLERANCE)

        # servo setup (same as before)…
        arduino = "left"
        neck_name, _, rot_name = self.motion_controller.neck_servos
        neck_idx, neck_rest, neck_min, neck_max, neck_cur = \
            self.motion_controller.get_servo_positions(neck_name, arduino)
        rot_idx, rot_rest, rot_min, rot_max, rot_cur = \
            self.motion_controller.get_servo_positions(rot_name, arduino)

        with self.mp_face_detection.FaceDetection(model_selection=0,
                                                  min_detection_confidence=0.5) as fd:
            try:
                while self.looking_at_person:
                    now = time.time()
                    dt = now - last
                    last = now

                    time.sleep(SLEEP)
                    retL, fL = capL.read()
                    retR, fR = capR.read()
                    if not (retL and retR):
                        break

                    fL = cv2.flip(fL, 1)
                    fR = cv2.flip(fR, 1)
                    rgbL = cv2.cvtColor(fL, cv2.COLOR_BGR2RGB)
                    rgbR = cv2.cvtColor(fR, cv2.COLOR_BGR2RGB)

                    resL = fd.process(rgbL)
                    resR = fd.process(rgbR)

                    # only proceed if both see a face
                    if not (resL.detections and resR.detections):
                        continue

                    def get_center(detection, frame):
                        bbox = detection.location_data.relative_bounding_box
                        x = int((bbox.xmin + bbox.width/2) * w)
                        y = int((bbox.ymin + bbox.height/2) * h)
                        return x, y

                    xL, yL = get_center(resL.detections[0], fL)
                    xR, yR = get_center(resR.detections[0], fR)

                    # optionally draw
                    if show_video:
                        for (f, x,y, res) in [(fL,xL,yL,resL),(fR,xR,yR,resR)]:
                            bb = res.detections[0].location_data.relative_bounding_box
                            x0, y0 = int(bb.xmin*w), int(bb.ymin*h)
                            x1, y1 = int((bb.xmin+bb.width)*w), int((bb.ymin+bb.height)*h)
                            cv2.rectangle(f, (x0,y0), (x1,y1), (0,255,0),2)
                            cv2.circle(f, (x,y), 4, (0,0,255), -1)
                            cv2.imshow('L', fL)
                            cv2.imshow('R', fR)

                    # compute and average errors
                    err_x = ((cx - xL) + (cx - xR)) / 2.0
                    err_y = ((cy - yL) + (cy - yR)) / 2.0

                    # only act if outside deadzone in *either* camera
                    if abs(cx - xL) > tol_x or abs(cx - xR) > tol_x \
                       or abs(cy - yL) > tol_y or abs(cy - yR) > tol_y:

                        # PID
                        int_x  += err_x * dt
                        deriv_x = (err_x - prev_err_x) / dt if dt>0 else 0
                        cmd_x   = Kp*err_x + Ki*int_x + Kd*deriv_x

                        int_y  += err_y * dt
                        deriv_y = (err_y - prev_err_y) / dt if dt>0 else 0
                        cmd_y   = - (Kp*err_y + Ki*int_y + Kd*deriv_y)

                        prev_err_x, prev_err_y = err_x, err_y

                        # clamp and apply
                        delta_rothead = int(np.clip(cmd_x, rot_min-rot_cur, rot_max-rot_cur))
                        delta_neck   = int(np.clip(cmd_y, neck_min-neck_cur, neck_max-neck_cur))

                        prev_rot_cur = rot_cur
                        prev_neck_cur = neck_cur
                        
                        rot_cur  += delta_rothead
                        neck_cur += delta_neck

                        if rot_cur != prev_rot_cur:
                            self.motion_controller.set_current_pos_servo(rot_name, arduino, rot_cur)
                            self.motion_controller.send_command(rot_idx, rot_cur, arduino, rot_name)
                        if neck_cur != prev_neck_cur:
                            self.motion_controller.set_current_pos_servo(neck_name, arduino, neck_cur)
                            self.motion_controller.send_command(neck_idx, neck_cur, arduino, neck_name)
                    else:
                        # both are centered
                        if exit_when_centered:
                            break

                    if show_video and cv2.waitKey(1) & 0xFF == ord('q'):
                        break

            finally:
                capL.release()
                capR.release()
                if show_video:
                    cv2.destroyAllWindows()


    def start_looking_at(self):
        self.looking_at_person = True

    def stop_looking_at(self):
        self.looking_at_person = False



# --- Main execution block ---
if __name__ == "__main__":
    
    try:
        akira_vision = Akira_See()
        #akira_vision.look_at_face(camera_index=0, show_video=False, exit_when_centered=False)
        akira_vision.look_at_face_stereo()
    finally:
        akira_vision.motion_controller.close_connection()
    
##    for _ in range(3):
##        print(akira_vision.describe_what_akira_sees(akira_vision.take_photo()))
##        time.sleep(5)
    
    
