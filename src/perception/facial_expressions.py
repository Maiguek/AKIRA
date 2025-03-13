import time
import random
import csv
import json
from motion_controller import MotionController
from vision_model import get_emotion

def get_random_face_positions(mc, servo_names):
    positions = {}
    for name in servo_names:
        servo = mc.servos_list[name]
        random_pos = random.randint(servo["min_pos"], servo["max_pos"])
        positions[name] = random_pos
    return positions

def set_servo_positions(mc, positions):
    for name, pos in positions.items():
        servo = mc.servos_list[name]
        index = servo["index"]
        mc.ser.write(f"{index} {pos}\n".encode())

def save_configs_to_csv(mean_config, mode_config, filename="configs.csv"):
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Servo", "Mean_Position", "Mode_Position"])
        all_servos = sorted(mean_config.keys())
        for servo_name in all_servos:
            writer.writerow([servo_name, mean_config[servo_name], mode_config[servo_name]])

def save_configs_to_json(mean_config, mode_config, filename="configs.json"):
    data = {
        "mean_config": mean_config,
        "mode_config": mode_config
    }
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def main():
    mc = MotionController(serial_port="/dev/ttyACM0", baud_rate=9600,
                          servos_file="servos_data_left.csv")
    
    servo_names = [
        "Upper_Lip", "Check_L", "Check_R", "Eyebrow_R", "Eyebrow_L",
        "Eyelid_Right_Lower", "Eyelid_Right_Upper", "Eyelid_Left_Down", 
        "Eyelid_Left_Up", "Forhead_R", "Forhead_L", "Jaw"
    ]
    
    target_emotion = "happy"
    num_trials = 50
    found_configs = []

    for i in range(num_trials):
        print(f"\n===== TRIAL {i+1}/{num_trials} =====")
        random_positions = get_random_face_positions(mc, servo_names)
        set_servo_positions(mc, random_positions)
        time.sleep(2.0)
        
        detected_emotion = get_emotion()
        print(f"Detected emotion: {detected_emotion}")
        
        if detected_emotion == target_emotion:
            print(f"Configuration found for '{target_emotion}'!")
            found_configs.append(random_positions)
    
    print("\n==== RESULTS ====")
    if not found_configs:
        print(f"No configuration found for '{target_emotion}'.")
        mc.close_connection()
        return
    else:
        print(f"Found {len(found_configs)} configuration(s) for '{target_emotion}'")
        for idx, cfg in enumerate(found_configs, start=1):
            print(f"  Config #{idx}: {cfg}")
    
    # Calculate the mean configuration
    mean_config = {}
    for servo in servo_names:
        mean_config[servo] = sum(cfg[servo] for cfg in found_configs) // len(found_configs)
    
    # Calculate frequency of each config and determine the mode
    # Convert dicts to tuples so we can count them
    freq_map = {}
    for cfg in found_configs:
        as_tuple = tuple(sorted(cfg.items()))
        freq_map[as_tuple] = freq_map.get(as_tuple, 0) + 1
    
    most_repeated_tuple = max(freq_map, key=freq_map.get)
    mode_config = dict(most_repeated_tuple)
    
    print("\n==== FINAL MAPPINGS ====")
    print("Mean Configuration:")
    print(mean_config)
    print("\nMost Repeated Configuration:")
    print(mode_config)

    # Save to CSV and JSON
    save_configs_to_csv(mean_config, mode_config, filename="happy_configs.csv")
    save_configs_to_json(mean_config, mode_config, filename="happy_configs.json")

    mc.close_connection()

if __name__ == "__main__":
    main()
