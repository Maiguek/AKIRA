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
const int Eye_Left_LR = 0; 
const int Eye_Right_LR = 1;
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

// Hand servos
Servo wrist; // Servo 23
Servo ringfinger; // Servo 24
Servo midfinger; // Servo 25
Servo pinky; // Servo 26
Servo index; // Servo 27
Servo thumb; // Servo 28 (this number represents the position in the external list file with starting index 0)

// Define min and max positions for each servo (YOU FILL IN THE VALUES)
int Eye_Left_LR_min = 90; 
int Eye_Left_LR_max = 170; 

int Eye_Right_LR_min = 81;
int Eye_Right_LR_max = 135;

int Eye_Right_UD_min = 80;
int Eye_Right_UD_max = 135;

int Check_L_min = 83;
int Check_L_max = 135;

int Check_R_min = 77;
int Check_R_max = 133;

int Upper_Lip_min = 65;
int Upper_Lip_max = 99;

int Eye_Left_UD_min = 54;
int Eye_Left_UD_max = 110;

int Eyelid_Right_Lower_min = 80; //
int Eyelid_Right_Lower_max = 130; //

int Eyebrow_R_min = 84;
int Eyebrow_R_max = 140;

int Eyelid_Right_Upper_min = 35; //
int Eyelid_Right_Upper_max = 100; //

int Forhead_R_min = 45;
int Forhead_R_max = 116;

int Forhead_L_min = 90;
int Forhead_L_max = 150;

int Eyebrow_L_min = 70;
int Eyebrow_L_max = 125;

int Eyelid_Left_Down_min = 40; //
int Eyelid_Left_Down_max = 100; //

int Eyelid_Left_Up_min = 40; //
int Eyelid_Left_Up_max = 165; //

int Rothead_min = 30;
int Rothead_max = 150;

// Min and max positions for the shoulder and jaw servos
int bicep_min = 0;
int bicep_max = 63;

int rotate_min = 40;
int rotate_max = 90;

int shoulder_min = 0;
int shoulder_max = 180;

int omoplate_min = 10;
int omoplate_max = 70;

int Neck_min = 50;
int Neck_max = 100;

int Jaw_min = 80;
int Jaw_max = 125;

int RollNeck_min = 50;
int RollNeck_max = 105;

//Min and max positions for the hand
int wrist_min = 0;
int wrist_max = 180;

int ringfinger_min = 10;
int ringfinger_max = 170;

int midfinger_min = 10;
int midfinger_max = 160;

int pinky_min = 10;
int pinky_max = 160;

int index_min = 0;
int index_max = 150;

int thumb_min = 60;
int thumb_max = 170;

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

  wrist.attach(7);
  ringfinger.attach(5);
  midfinger.attach(4);
  pinky.attach(6);
  index.attach(3);
  thumb.attach(2);

  // Set initial positions to rest positions
  bicep.write(33);      
  rotate.write(90);    
  shoulder.write(130); 
  omoplate.write(70);

  Neck.write(60);
  Jaw.write(80);
  RollNeck.write(70);

  wrist.write(90);
  ringfinger.write(170);
  midfinger.write(160);
  pinky.write(160);
  index.write(0);
  thumb.write(60);

  pwm.setPWM(Eye_Left_LR, 0, angleToPulse(120));
  pwm.setPWM(Eye_Right_LR, 0, angleToPulse(108));
  pwm.setPWM(Eye_Right_UD, 0, angleToPulse(112));
  pwm.setPWM(Check_L, 0, angleToPulse(118));

  pwm.setPWM(Check_R, 0, angleToPulse(101));
  pwm.setPWM(Upper_Lip, 0, angleToPulse(67));
  pwm.setPWM(Eye_Left_UD, 0, angleToPulse(90));
  pwm.setPWM(Eyelid_Right_Lower, 0, angleToPulse(90));

  pwm.setPWM(Eyebrow_R, 0, angleToPulse(115));
  pwm.setPWM(Eyelid_Right_Upper, 0, angleToPulse(80));
  pwm.setPWM(Forhead_R, 0, angleToPulse(90));
  pwm.setPWM(Forhead_L, 0, angleToPulse(120));

  pwm.setPWM(Eyebrow_L, 0, angleToPulse(96));
  pwm.setPWM(Eyelid_Left_Down, 0, angleToPulse(90));
  pwm.setPWM(Eyelid_Left_Up, 0, angleToPulse(72));
  pwm.setPWM(Rothead, 0, angleToPulse(90));
}

void loop() {
  if (Serial.available() > 0) {
    int servoNum = Serial.parseInt(); // Read the first integer (servo number)
    int angle = Serial.parseInt(); // Read the second integer (angle)

    // Ensure the angle stays within valid bounds
    if (angle < 0) angle = 0;
    if (angle > 180) angle = 180;

    int pulseLength = angleToPulse(angle); // Convert angle to PWM pulse

    switch (servoNum) {
      case 0:
        if (angle < Eye_Left_LR_min) angle = Eye_Left_LR_min;
        if (angle > Eye_Left_LR_max) angle = Eye_Left_LR_max;
        pwm.setPWM(Eye_Left_LR, 0, pulseLength);
        break;

      case 1:
        if (angle < Eye_Right_LR_min) angle = Eye_Right_LR_min;
        if (angle > Eye_Right_LR_max) angle = Eye_Right_LR_max;
        pwm.setPWM(Eye_Right_LR, 0, pulseLength);
        break;

      case 2:
        if (angle < Eye_Right_UD_min) angle = Eye_Right_UD_min;
        if (angle > Eye_Right_UD_max) angle = Eye_Right_UD_max;
        pwm.setPWM(Eye_Right_UD, 0, pulseLength);
        break;

      case 3:
        if (angle < Check_L_min) angle = Check_L_min;
        if (angle > Check_L_max) angle = Check_L_max;
        pwm.setPWM(Check_L, 0, pulseLength);
        break;

      case 4:
        if (angle < Check_R_min) angle = Check_R_min;
        if (angle > Check_R_max) angle = Check_R_max;
        pwm.setPWM(Check_R, 0, pulseLength);
        break;

      case 5:
        if (angle < Upper_Lip_min) angle = Upper_Lip_min;
        if (angle > Upper_Lip_max) angle = Upper_Lip_max;
        pwm.setPWM(Upper_Lip, 0, pulseLength);
        break;

      case 6:
        if (angle < Eye_Left_UD_min) angle = Eye_Left_UD_min;
        if (angle > Eye_Left_UD_max) angle = Eye_Left_UD_max;
        pwm.setPWM(Eye_Left_UD, 0, pulseLength);
        break;

      case 7:
        if (angle < Eyelid_Right_Lower_min) angle = Eyelid_Right_Lower_min;
        if (angle > Eyelid_Right_Lower_max) angle = Eyelid_Right_Lower_max;
        pwm.setPWM(Eyelid_Right_Lower, 0, pulseLength);
        break;

      case 8:
        if (angle < Eyebrow_R_min) angle = Eyebrow_R_min;
        if (angle > Eyebrow_R_max) angle = Eyebrow_R_max;
        pwm.setPWM(Eyebrow_R, 0, pulseLength);
        break;

      case 9:
        if (angle < Eyelid_Right_Upper_min) angle = Eyelid_Right_Upper_min;
        if (angle > Eyelid_Right_Upper_max) angle = Eyelid_Right_Upper_max;
        pwm.setPWM(Eyelid_Right_Upper, 0, pulseLength);
        break;

      case 10:
        if (angle < Forhead_R_min) angle = Forhead_R_min;
        if (angle > Forhead_R_max) angle = Forhead_R_max;
        pwm.setPWM(Forhead_R, 0, pulseLength);
        break;

      case 11:
        if (angle < Forhead_L_min) angle = Forhead_L_min;
        if (angle > Forhead_L_max) angle = Forhead_L_max;
        pwm.setPWM(Forhead_L, 0, pulseLength);
        break;

      case 12:
        if (angle < Eyebrow_L_min) angle = Eyebrow_L_min;
        if (angle > Eyebrow_L_max) angle = Eyebrow_L_max;
        pwm.setPWM(Eyebrow_L, 0, pulseLength);
        break;

      case 13:
        if (angle < Eyelid_Left_Down_min) angle = Eyelid_Left_Down_min;
        if (angle > Eyelid_Left_Down_max) angle = Eyelid_Left_Down_max;
        pwm.setPWM(Eyelid_Left_Down, 0, pulseLength);
        break;

      case 14:
        if (angle < Eyelid_Left_Up_min) angle = Eyelid_Left_Up_min;
        if (angle > Eyelid_Left_Up_max) angle = Eyelid_Left_Up_max;
        pwm.setPWM(Eyelid_Left_Up, 0, pulseLength);
        break;

      case 15:
        if (angle < Rothead_min) angle = Rothead_min;
        if (angle > Rothead_max) angle = Rothead_max;
        pwm.setPWM(Rothead, 0, pulseLength);
        break;

      // Shoulder and Jaw Servos
      case 16:
        if (angle < bicep_min) angle = bicep_min;
        if (angle > bicep_max) angle = bicep_max;
        bicep.write(angle);
        break;

      case 17:
        if (angle < rotate_min) angle = rotate_min;
        if (angle > rotate_max) angle = rotate_max;
        rotate.write(angle);
        break;

      case 18:
        if (angle < shoulder_min) angle = shoulder_min;
        if (angle > shoulder_max) angle = shoulder_max;
        shoulder.write(angle);
        break;

      case 19:
        if (angle < omoplate_min) angle = omoplate_min;
        if (angle > omoplate_max) angle = omoplate_max;
        omoplate.write(angle);
        break;

      case 20:
        if (angle < Neck_min) angle = Neck_min;
        if (angle > Neck_max) angle = Neck_max;
        Neck.write(angle);
        break;

      case 21:
        if (angle < Jaw_min) angle = Jaw_min;
        if (angle > Jaw_max) angle = Jaw_max;
        Jaw.write(angle);
        break;

      case 22:
        if (angle < RollNeck_min) angle = RollNeck_min;
        if (angle > RollNeck_max) angle = RollNeck_max;
        RollNeck.write(angle);
        break;

      case 23:
        if (angle < wrist_min) angle = wrist_min;
        if (angle > wrist_max) angle = wrist_max;
        wrist.write(angle);
        break;

      case 24:
        if (angle < ringfinger_min) angle = ringfinger_min;
        if (angle > ringfinger_max) angle = ringfinger_max;
        ringfinger.write(angle);
        break;

      case 25:
        if (angle < midfinger_min) angle = midfinger_min;
        if (angle > midfinger_max) angle = midfinger_max;
        midfinger.write(angle);
        break;

      case 26:
        if (angle < pinky_min) angle = pinky_min;
        if (angle > pinky_max) angle = pinky_max;
        pinky.write(angle);
        break;

      case 27:
        if (angle < index_min) angle = index_min;
        if (angle > index_max) angle = index_max;
        index.write(angle);
        break;

      case 28:
        if (angle < thumb_min) angle = thumb_min;
        if (angle > thumb_max) angle = thumb_max;
        thumb.write(angle);
        break;

      default:
        break;  // Ignore invalid servo numbers
    }
  }
}
