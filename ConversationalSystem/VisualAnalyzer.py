import cv2
from deepface import DeepFace

# TODO: Find models that can be used with Coral TPU (tensorflow lite) and update the CameraAnalyzer class

class CameraAnalyzer:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(camera_index)
    
    def update_camera_index(self, camera_index):
        self.cap.release()
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(camera_index)

    def get_analysis_string(self):
        ret, frame = self.cap.read()
        if not ret:
            return "Unable to capture frame"
        
        try:
            analysis = DeepFace.analyze(frame, actions=['age', 'gender', 'race', 'emotion'])
            analysis = analysis[0]
            age = analysis["age"]
            dominant_gender = analysis["dominant_gender"]
            dominant_race = analysis["dominant_race"]
            dominant_emotion = analysis["dominant_emotion"]
            
            return f"Age: {age}, Gender: {dominant_gender}, Race: {dominant_race}, Emotion: {dominant_emotion}"
        except:
            return "No face detected"

    def release_camera(self):
        self.cap.release()

# Example usage
if __name__ == "__main__":
    analyzer = CameraAnalyzer()
    while True:
        analysis_result = analyzer.get_analysis_string()
        print(analysis_result)
        
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    
    analyzer.release_camera()
    cv2.destroyAllWindows()
