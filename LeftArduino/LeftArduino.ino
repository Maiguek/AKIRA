#include <Servo.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

#define SERVOMIN  1353 // Minimum pulse length count (0 degrees)
#define SERVOMAX  2706 // Maximum pulse length count (180 degrees)

// Function to map angle to PWM pulse length
int angleToPulse(int angle) {
  return map(angle, 0, 180, SERVOMIN, SERVOMAX);
}

// Face Servos (Using PCA9685)
const int Eye_Left_LR = 0; // currently inactive - possible damage in the PCA9685 that burns this specific motor
const int Eye_Right_LR = 1; // works but due to the above's problem I might not use it...
const int Eye_Right_UD = 2;
const int Check_L = 3;

const int Check_R = 4;
const int Upper_Lip = 5;
const int Eye_Left_UD = 6;
const int Eyelid_Right_Lower = 7;

const int Eyebrow_R = 8;
const int Eyelid_Right_Upper = 9;
const int Forhead_R = 10;
const int Forhead_L = 11;

const int Eyebrow_L = 12;
const int Eyelid_Left_Down = 13;
const int Eyelid_Left_Up = 14;
const int Rothead = 15;

// Shoulder Servos
Servo bicep; // Servo 16
Servo rotate; // Servo 17
Servo shoulder; // Servo 18
Servo omoplate; // Servo 19

// Other servos
Servo Neck; // Servo 20
Servo Jaw; // Servo 21
Servo RollNeck; // Servo 22

void setup() {
  Serial.begin(9600);
  pwm.begin();
  pwm.setPWMFreq(330); 

  bicep.attach(8);
  rotate.attach(9);
  shoulder.attach(10);
  omoplate.attach(11);
  
  Neck.attach(12);
  Jaw.attach(41);
  RollNeck.attach(13);

  // Set initial positions to rest positions
  bicep.write(0);      
  rotate.write(90);    
  shoulder.write(130); 
  omoplate.write(70);

  Neck.write(60);
  Jaw.write(100);
  RollNeck.write(40);

  pwm.setPWM(Eye_Left_LR, 0, angleToPulse(100));
  pwm.setPWM(Eye_Right_LR, 0, angleToPulse(108));
  pwm.setPWM(Eye_Right_UD, 0, angleToPulse(90));
  pwm.setPWM(Check_L, 0, angleToPulse(118));

  pwm.setPWM(Check_R, 0, angleToPulse(90));
  pwm.setPWM(Upper_Lip, 0, angleToPulse(67));
  pwm.setPWM(Eye_Left_UD, 0, angleToPulse(90));
  pwm.setPWM(Eyelid_Right_Lower, 0, angleToPulse(90));

  pwm.setPWM(Eyebrow_R, 0, angleToPulse(90));
  pwm.setPWM(Eyelid_Right_Upper, 0, angleToPulse(80));
  pwm.setPWM(Forhead_R, 0, angleToPulse(90));
  pwm.setPWM(Forhead_L, 0, angleToPulse(120));

  pwm.setPWM(Eyebrow_L, 0, angleToPulse(90));
  pwm.setPWM(Eyelid_Left_Down, 0, angleToPulse(90));
  pwm.setPWM(Eyelid_Left_Up, 0, angleToPulse(55));
  pwm.setPWM(Rothead, 0, angleToPulse(90));
}

void loop() {
  if (Serial.available() > 0) {
    int servoNum = Serial.parseInt(); // Read the first integer (servo number)
    int angle = Serial.parseInt(); // Read the second integer (angle)

    // Ensure angle is within range
    if (angle < 0) angle = 0;
    if (angle > 180) angle = 180;

    int pulseLength = angleToPulse(angle); // For the Servos of the Face

    switch (servoNum) {
      case 0: pwm.setPWM(Eye_Left_LR, 0, pulseLength); break;
      case 1: pwm.setPWM(Eye_Right_LR, 0, pulseLength); break;
      case 2: pwm.setPWM(Eye_Right_UD, 0, pulseLength); break;
      case 3: pwm.setPWM(Check_L, 0, pulseLength); break;
      case 4: pwm.setPWM(Check_R, 0, pulseLength); break;
      case 5: pwm.setPWM(Upper_Lip, 0, pulseLength); break;
      case 6: pwm.setPWM(Eye_Left_UD, 0, pulseLength); break;
      case 7: pwm.setPWM(Eyelid_Right_Lower, 0, pulseLength); break;
      case 8: pwm.setPWM(Eyebrow_R, 0, pulseLength); break;
      case 9: pwm.setPWM(Eyelid_Right_Upper, 0, pulseLength); break;
      case 10: pwm.setPWM(Forhead_R, 0, pulseLength); break;
      case 11: pwm.setPWM(Forhead_L, 0, pulseLength); break;
      case 12: pwm.setPWM(Eyebrow_L, 0, pulseLength); break;
      case 13: pwm.setPWM(Eyelid_Left_Down, 0, pulseLength); break;
      case 14: pwm.setPWM(Eyelid_Left_Up, 0, pulseLength); break;
      case 15: pwm.setPWM(Rothead, 0, pulseLength); break;
      case 16: bicep.write(angle); break;
      case 17: rotate.write(angle); break;
      case 18: shoulder.write(angle); break;
      case 19: omoplate.write(angle); break;
      case 20: Neck.write(angle); break;
      case 21: Jaw.write(angle); break;
      case 22: RollNeck.write(angle); break;
      default: break;  // Ignore invalid servo numbers
    }
  }
}
