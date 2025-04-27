import cv2
import mediapipe as mp
import numpy as np
import time
import json

# Configuration
RECORD_DURATION = 30  # seconds
OUTPUT_FILE = 'recorded_positions.json'

# Initialize MediaPipe Holistic model for pose and hands
mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic

# Utility to calculate angle between three points
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    ba = a - b
    bc = c - b
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return np.degrees(angle)

# Utility to extract keypoints for shoulders, elbows, wrists
def extract_keypoints(landmarks, width, height):
    def get_point(lm):
        return [lm.x * width, lm.y * height]

    points = {}
    points['left_shoulder'] = get_point(landmarks[mp_holistic.PoseLandmark.LEFT_SHOULDER])
    points['left_elbow']    = get_point(landmarks[mp_holistic.PoseLandmark.LEFT_ELBOW])
    points['left_wrist']    = get_point(landmarks[mp_holistic.PoseLandmark.LEFT_WRIST])
    points['right_shoulder'] = get_point(landmarks[mp_holistic.PoseLandmark.RIGHT_SHOULDER])
    points['right_elbow']    = get_point(landmarks[mp_holistic.PoseLandmark.RIGHT_ELBOW])
    points['right_wrist']    = get_point(landmarks[mp_holistic.PoseLandmark.RIGHT_WRIST])
    return points

# Main capture and processing
cap = cv2.VideoCapture(4)
recordings = []
start_time = time.time()
next_record_time = start_time
with mp_holistic.Holistic(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5) as holistic:

    while cap.isOpened():
        current_time = time.time()
        elapsed = current_time - start_time
        ret, frame = cap.read()
        if not ret:
            break

        # Flip and convert BGR to RGB
        image = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = holistic.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Draw landmarks
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS)
        if results.left_hand_landmarks:
            mp_drawing.draw_landmarks(image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
        if results.right_hand_landmarks:
            mp_drawing.draw_landmarks(image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS)

        # Show elapsed time on screen
        cv2.putText(image, f'Time: {int(elapsed)}s', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Record keypoints each second
        if elapsed <= RECORD_DURATION and current_time >= next_record_time:
            h, w, _ = image.shape
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                keypoints = extract_keypoints(landmarks, w, h)
                keypoints['timestamp'] = int(elapsed)
                recordings.append(keypoints)
            next_record_time += 1

        # Display image
        cv2.imshow('Arm & Hand Gesture Analysis', image)

        # Stop if duration exceeded or user quits
        if elapsed > RECORD_DURATION or (cv2.waitKey(5) & 0xFF == ord('q')):
            break

# Release resources
cap.release()
cv2.destroyAllWindows()

# Save recordings to file
with open(OUTPUT_FILE, 'w') as f:
    json.dump(recordings, f, indent=2)

print(f'Recording complete. Saved {len(recordings)} entries to {OUTPUT_FILE}')
