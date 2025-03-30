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


//Min and max positions for the hand
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
  Serial.begin(9600);

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
  
  // Set initial positions to rest positions
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
  if (Serial.available() > 0) {
    int servoNum = Serial.parseInt(); // Read the first integer (servo number)
    int angle = Serial.parseInt(); // Read the second integer (angle)

    // Ensure the angle stays within valid bounds
    if (angle < 0) angle = 0;
    if (angle > 180) angle = 180;

    switch (servoNum) {
      case 0:
        break;
      
      // Shoulder and Jaw Servos
      case 1:
        if (angle < bicep_min) angle = bicep_min;
        if (angle > bicep_max) angle = bicep_max;
        bicep.write(angle);
        break;

      case 2:
        if (angle < rotate_min) angle = rotate_min;
        if (angle > rotate_max) angle = rotate_max;
        rotate.write(angle);
        break;

      case 3:
        if (angle < shoulder_min) angle = shoulder_min;
        if (angle > shoulder_max) angle = shoulder_max;
        shoulder.write(angle);
        break;

      case 4:
        if (angle < omoplate_min) angle = omoplate_min;
        if (angle > omoplate_max) angle = omoplate_max;
        omoplate.write(angle);
        break;

      case 5:
        if (angle < wrist_min) angle = wrist_min;
        if (angle > wrist_max) angle = wrist_max;
        wrist.write(angle);
        break;

      case 6:
        if (angle < ringfinger_min) angle = ringfinger_min;
        if (angle > ringfinger_max) angle = ringfinger_max;
        ringfinger.write(angle);
        break;

      case 7:
        if (angle < midfinger_min) angle = midfinger_min;
        if (angle > midfinger_max) angle = midfinger_max;
        midfinger.write(angle);
        break;

      case 8:
        if (angle < pinky_min) angle = pinky_min;
        if (angle > pinky_max) angle = pinky_max;
        pinky.write(angle);
        break;

      case 9:
        if (angle < index_min) angle = index_min;
        if (angle > index_max) angle = index_max;
        index.write(angle);
        break;

      case 10:
        if (angle < thumb_min) angle = thumb_min;
        if (angle > thumb_max) angle = thumb_max;
        thumb.write(angle);
        break;
        
      default:
        break;  // Ignore invalid servo numbers
    }
  }
}
