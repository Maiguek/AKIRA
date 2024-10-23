import pandas as pd
import serial
import time
import tkinter as tk
from tkinter import ttk

# Set up the serial connection (adjust the port and baud rate as needed)
arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1) 
time.sleep(2)  # Wait for the connection to initialize

# Read the servo data from the CSV file
df = pd.read_csv("servos_data.csv")

servos_list = df.to_dict(orient="records")

current_servo = None

def set_servo_angle(index, angle):
    time.sleep(0.1)
    command = f"{index} {angle}\n"
    arduino.write(command.encode())

def update_angle(val):
    angle = int(float(val))
    if current_servo is not None:
        set_servo_angle(current_servo['index'], angle)
    angle_var.set(str(angle))

def entry_update_angle(*args):
    try:
        angle = int(angle_var.get())
        if current_servo and current_servo['min_pos'] <= angle <= current_servo['max_pos']:
            slider.set(angle)
            set_servo_angle(current_servo['index'], angle)
        else:
            raise ValueError
    except ValueError:
        pass

def select_servo(index):
    time.sleep(0.1)
    global current_servo
    current_servo = servos_list[index]
    current_servo['index'] = index  # Store the index for sending commands
    slider.config(from_=current_servo['min_pos'], to=current_servo['max_pos'])
    angle_var.set("")  # Clear the entry box
    slider.set(current_servo['rest_pos'])  # Set slider to the min position without sending command
    update_status(f"{current_servo['name'].capitalize()} selected.")

def update_status(message):
    status_label.config(text=message, foreground="blue")

# Set up the GUI
root = tk.Tk()
root.title("Servo Motor Control")

# Add a frame for better organization
frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W + tk.E))

# Add a label
ttk.Label(frame, text="Servo Angle Control", font=("Helvetica", 16)).grid(row=0, column=0, columnspan=4)

# Add buttons for each servo motor
for i, servo in enumerate(servos_list):
    button = ttk.Button(frame, text=servo['name'], command=lambda i=i: select_servo(i))
    button.grid(row=1 + (i // 4), column=i % 4, padx=5, pady=5)  # Adjusted to fit in multiple rows of 4 columns

# Add a slider
slider = ttk.Scale(frame, from_=0, to=180, orient='horizontal', command=update_angle)
slider.grid(row=2 + (len(servos_list) // 4), column=0, columnspan=4, sticky=(tk.W + tk.E))

# Add an entry box for typing the angle
angle_var = tk.StringVar()
entry = ttk.Entry(frame, textvariable=angle_var, width=5)
entry.grid(row=3 + (len(servos_list) // 4), column=1, sticky=(tk.W + tk.E))
entry.bind('<Return>', entry_update_angle)

# Add a button to set the angle from the entry box
set_button = ttk.Button(frame, text="Set Angle", command=entry_update_angle)
set_button.grid(row=3 + (len(servos_list) // 4), column=2, sticky=(tk.W + tk.E))

# Add a status label
status_label = ttk.Label(frame, text="Select a servo...", font=("Helvetica", 12), foreground="gray")
status_label.grid(row=4 + (len(servos_list) // 4), column=0, columnspan=4, pady=10)

# Initialize the interface without sending any commands to the servos
slider.set(current_servo['min_pos'] if current_servo else 0)  # Ensure slider set does not send command
angle_var.set("")

# Send initial rest positions to the servos
for index, servo in enumerate(servos_list):
    set_servo_angle(index, servo['rest_pos'])
    time.sleep(0.1)  # Give some time for each command to be processed

# Run the Tkinter event loop
root.mainloop()

# Close the serial connection when done
arduino.close()