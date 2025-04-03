import cv2
import mediapipe as mp
import time
import collections
from datetime import datetime
import numpy as np
import sys
import os
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer
import torch
from PIL import Image

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
        
        self.descriptor_model = VisionEncoderDecoderModel.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
        self.descriptor_model.to(self.device)
        self.descriptor_feature_extractor = ViTImageProcessor.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
        self.descriptor_tokenizer = AutoTokenizer.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
        

    def describe_what_akira_sees(self):
        """
        This captioning model works, but is not too precise. It is fast though, but I will have to
        continue with some testing....
        I am also trying to implement NanoLLM. We'll see :D
        """
        max_length = 16
        num_beams = 4
        gen_kwargs = {"max_length": max_length, "num_beams": num_beams}
        def predict_step(image_paths):
            images = []
            for image_path in image_paths:
                i_image = Image.open(image_path)
                if i_image.mode != "RGB":
                    i_image = i_image.convert(mode="RGB")

                images.append(i_image)

            pixel_values = self.descriptor_feature_extractor(images=images, return_tensors="pt").pixel_values
            pixel_values = pixel_values.to(self.device)

            output_ids = self.descriptor_model.generate(pixel_values, **gen_kwargs)

            preds = self.descriptor_tokenizer.batch_decode(output_ids, skip_special_tokens=True)
            preds = [pred.strip() for pred in preds]
            return preds

        instant_photo = self.take_photo()
        return predict_step([instant_photo])

    def take_photo(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        filename = "photo_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
        file_path = os.path.join(script_dir, filename)

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Camera cannot be accessed")
            return None

        print("Taking a picture!")

        ret, frame = cap.read()
        cap.release()

        if not ret:
            print("Picture was not able to be taken...")
            return None

        # Guardar la imagen
        cv2.imwrite(file_path, frame)
        print(f"Picture saved in: {file_path}")
        return file_path


    def look_at_face(self, camera_index=0, show_video=True, once_found_close=True):
        print(f"Starting keeping_the_gaze on camera index {camera_index}...")

        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            print(f"Error: Could not open camera {camera_index}.")
            return

        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read initial frame.")
            cap.release()
            return
        frame_height, frame_width, _ = frame.shape
        frame_center_x = frame_width // 2
        frame_center_y = frame_height // 2

        center_tolerance_x = int(frame_width * 0.10)
        center_tolerance_y = int(frame_height * 0.10)

        # --- Error tracking buffer ---
        error_history = collections.deque(maxlen=10)  # Track last 10 errors (x, y)
        stuck_threshold = 5  # If 5 or more errors are too similar, consider it stuck
        delta_threshold = 2  # Minimum difference to consider a change (in pixels)

        with self.mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detection:
            print("Entering main loop. Press 'q' to quit.")
            while True:
                time.sleep(0.1)
                ret, frame = cap.read()
                if not ret:
                    print("Error: Failed to capture frame.")
                    break

                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_detection.process(rgb_frame)

                current_face_detected_this_frame = False
                face_center_x = None
                face_center_y = None

                if results.detections:
                    current_face_detected_this_frame = True
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

                self.face_detected = current_face_detected_this_frame

                step_size_yaw = 5
                step_size_pitch = -5
                adjust_rothead = 0
                adjust_neck = 0

                if self.face_detected and self.motion_controller is not None:
                    error_x = frame_center_x - face_center_x
                    error_y = frame_center_y - face_center_y

                    # Save errors to history
                    error_history.append((error_x, error_y))

                    # Check if robot is stuck (errors not changing much)
                    if len(error_history) == error_history.maxlen:
                        deltas = [
                            abs(error_history[i][0] - error_history[i-1][0]) +
                            abs(error_history[i][1] - error_history[i-1][1])
                            for i in range(1, len(error_history))
                        ]
                        similar_count = sum(d < delta_threshold for d in deltas)
                        if similar_count >= stuck_threshold:
                            print("Head seems to be stuck (no significant change in error). Stopping movements temporarily.")
                            # You can break the loop, reset servos, or just wait
                            time.sleep(1)
                            error_history.clear()
                            continue  # Skip sending commands this round

                    if abs(error_x) > center_tolerance_x:
                        adjust_rothead = int(step_size_yaw * np.sign(error_x))
                    if abs(error_y) > center_tolerance_y:
                        adjust_neck = int(step_size_pitch * np.sign(error_y))

                    if adjust_neck != 0 or adjust_rothead != 0:
                        print(f"Error X: {error_x}, Error Y: {error_y} -> Adjust Neck: {adjust_neck}, Adjust Rothead: {adjust_rothead}")
                        try:
                            self.motion_controller.move_head_relative(
                                adjust_neck=adjust_neck,
                                adjust_rollneck=0,
                                adjust_rothead=adjust_rothead
                            )
                        except Exception as e:
                            print(f"Error sending command to motion controller: {e}")
                    if once_found_close:
                        if abs(error_x) <= center_tolerance_x and abs(error_y) <= center_tolerance_y:
                            print("Face is centered. Exiting keeping_the_gaze.")
                            break
                    
                if show_video:
                    cv2.rectangle(frame,
                                  (frame_center_x - center_tolerance_x, frame_center_y - center_tolerance_y),
                                  (frame_center_x + center_tolerance_x, frame_center_y + center_tolerance_y),
                                  (255, 255, 0), 1)
                    cv2.circle(frame, (frame_center_x, frame_center_y), 5, (255, 255, 255), -1)
                    cv2.imshow('Akira - Keeping Gaze', frame)

                if cv2.waitKey(5) & 0xFF == ord('q'):
                    print("'q' pressed, exiting.")
                    break

        print("Releasing camera and destroying windows...")
        cap.release()
        if show_video:
            cv2.destroyAllWindows()
        print("keeping_the_gaze finished.")


# --- Main execution block ---
if __name__ == "__main__":
    akira_vision = Akira_See()
    for _ in range(5):
        print(akira_vision.describe_what_akira_sees())
        time.sleep(1)
    #akira_vision.look_at_face(camera_index=0, show_video=True, once_found_close=True)
    
