#include <Servo.h>
#include <Wire.h>

// Shoulder Servos
Servo bicep; // Servo 1
Servo rotate; // Servo 2
Servo shoulder; // Servo 3
Servo omoplate; // Servo 4

// Hand servos
Servo wrist; // Servo 5
Servo ringfinger; // Servo 6
Servo midfinger; // Servo 7
Servo pinky; // Servo 8
Servo index; // Servo 9
Servo thumb; // Servo 10

// Min and max positions for the shoulder and jaw servos
int bicep_min = 15;
int bicep_max = 45;

int rotate_min = 40;
int rotate_max = 90;

int shoulder_min = 0;
int shoulder_max = 110;

int omoplate_min = 70;
int omoplate_max = 125;

// Min and max positions for the hand
int wrist_min = 0;
int wrist_max = 180;

int ringfinger_min = 10;
int ringfinger_max = 160;

int midfinger_min = 10;
int midfinger_max = 160;

int pinky_min = 25;
int pinky_max = 170;

int index_min = 5;
int index_max = 160;

int thumb_min = 90;
int thumb_max = 170;

void setup() {
  Serial.begin(9600); // Updated baud rate

  // Attach servos
  bicep.attach(8);
  rotate.attach(9);
  shoulder.attach(10);
  omoplate.attach(11);
  wrist.attach(7);
  ringfinger.attach(5);
  midfinger.attach(4);
  pinky.attach(6);
  index.attach(3);
  thumb.attach(2);

  // Set initial positions
  bicep.write(33);      
  rotate.write(90);    
  shoulder.write(72); 
  omoplate.write(125);

  wrist.write(90);
  ringfinger.write(10);
  midfinger.write(10);
  pinky.write(25);
  index.write(160);
  thumb.write(170);
}

void loop() {
  if (Serial.available()) {
    int servoNum = Serial.parseInt(); // Get servo number
    int angle = Serial.parseInt();    // Get angle

    // Clear remaining input to avoid leftover characters (optional)
    while (Serial.available()) Serial.read();

    // Clamp the angle to [0,180]
    angle = constrain(angle, 0, 180);

    switch (servoNum) {
      case 1:
        bicep.write(constrain(angle, bicep_min, bicep_max));
        break;
      case 2:
        rotate.write(constrain(angle, rotate_min, rotate_max));
        break;
      case 3:
        shoulder.write(constrain(angle, shoulder_min, shoulder_max));
        break;
      case 4:
        omoplate.write(constrain(angle, omoplate_min, omoplate_max));
        break;
      case 5:
        wrist.write(constrain(angle, wrist_min, wrist_max));
        break;
      case 6:
        ringfinger.write(constrain(angle, ringfinger_min, ringfinger_max));
        break;
      case 7:
        midfinger.write(constrain(angle, midfinger_min, midfinger_max));
        break;
      case 8:
        pinky.write(constrain(angle, pinky_min, pinky_max));
        break;
      case 9:
        index.write(constrain(angle, index_min, index_max));
        break;
      case 10:
        thumb.write(constrain(angle, thumb_min, thumb_max));
        break;
      default:
        // Optional: send an error message
        Serial.println("Invalid servo number");
        break;
    }

    // Optional: confirm the action (for Jetson to sync)
    Serial.print("OK ");
    Serial.print(servoNum);
    Serial.print(" ");
    Serial.println(angle);
  }
}
