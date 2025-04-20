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

int shoulder_min = 75;
int shoulder_max = 180;

int omoplate_min = 10;
int omoplate_max = 70;

int Neck_min = 50;
int Neck_max = 90;

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
  shoulder.write(145); 
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
  if (Serial.available()) {
    int servoNum = Serial.parseInt(); // Read servo number
    int angle = Serial.parseInt();    // Read angle

    // Clear any extra characters from the buffer
    while (Serial.available()) Serial.read();

    // Clamp angle to [0, 180]
    angle = constrain(angle, 0, 180);

    switch (servoNum) {
      case 0:
        pwm.setPWM(Eye_Left_LR, 0, angleToPulse(constrain(angle, Eye_Left_LR_min, Eye_Left_LR_max)));
        break;
      case 1:
        pwm.setPWM(Eye_Right_LR, 0, angleToPulse(constrain(angle, Eye_Right_LR_min, Eye_Right_LR_max)));
        break;
      case 2:
        pwm.setPWM(Eye_Right_UD, 0, angleToPulse(constrain(angle, Eye_Right_UD_min, Eye_Right_UD_max)));
        break;
      case 3:
        pwm.setPWM(Check_L, 0, angleToPulse(constrain(angle, Check_L_min, Check_L_max)));
        break;
      case 4:
        pwm.setPWM(Check_R, 0, angleToPulse(constrain(angle, Check_R_min, Check_R_max)));
        break;
      case 5:
        pwm.setPWM(Upper_Lip, 0, angleToPulse(constrain(angle, Upper_Lip_min, Upper_Lip_max)));
        break;
      case 6:
        pwm.setPWM(Eye_Left_UD, 0, angleToPulse(constrain(angle, Eye_Left_UD_min, Eye_Left_UD_max)));
        break;
      case 7:
        pwm.setPWM(Eyelid_Right_Lower, 0, angleToPulse(constrain(angle, Eyelid_Right_Lower_min, Eyelid_Right_Lower_max)));
        break;
      case 8:
        pwm.setPWM(Eyebrow_R, 0, angleToPulse(constrain(angle, Eyebrow_R_min, Eyebrow_R_max)));
        break;
      case 9:
        pwm.setPWM(Eyelid_Right_Upper, 0, angleToPulse(constrain(angle, Eyelid_Right_Upper_min, Eyelid_Right_Upper_max)));
        break;
      case 10:
        pwm.setPWM(Forhead_R, 0, angleToPulse(constrain(angle, Forhead_R_min, Forhead_R_max)));
        break;
      case 11:
        pwm.setPWM(Forhead_L, 0, angleToPulse(constrain(angle, Forhead_L_min, Forhead_L_max)));
        break;
      case 12:
        pwm.setPWM(Eyebrow_L, 0, angleToPulse(constrain(angle, Eyebrow_L_min, Eyebrow_L_max)));
        break;
      case 13:
        pwm.setPWM(Eyelid_Left_Down, 0, angleToPulse(constrain(angle, Eyelid_Left_Down_min, Eyelid_Left_Down_max)));
        break;
      case 14:
        pwm.setPWM(Eyelid_Left_Up, 0, angleToPulse(constrain(angle, Eyelid_Left_Up_min, Eyelid_Left_Up_max)));
        break;
      case 15:
        pwm.setPWM(Rothead, 0, angleToPulse(constrain(angle, Rothead_min, Rothead_max)));
        break;

      // Shoulder and body servos
      case 16:
        bicep.write(constrain(angle, bicep_min, bicep_max));
        break;
      case 17:
        rotate.write(constrain(angle, rotate_min, rotate_max));
        break;
      case 18:
        shoulder.write(constrain(angle, shoulder_min, shoulder_max));
        break;
      case 19:
        omoplate.write(constrain(angle, omoplate_min, omoplate_max));
        break;
      case 20:
        Neck.write(constrain(angle, Neck_min, Neck_max));
        break;
      case 21:
        Jaw.write(constrain(angle, Jaw_min, Jaw_max));
        break;
      case 22:
        RollNeck.write(constrain(angle, RollNeck_min, RollNeck_max));
        break;
      case 23:
        wrist.write(constrain(angle, wrist_min, wrist_max));
        break;
      case 24:
        ringfinger.write(constrain(angle, ringfinger_min, ringfinger_max));
        break;
      case 25:
        midfinger.write(constrain(angle, midfinger_min, midfinger_max));
        break;
      case 26:
        pinky.write(constrain(angle, pinky_min, pinky_max));
        break;
      case 27:
        index.write(constrain(angle, index_min, index_max));
        break;
      case 28:
        thumb.write(constrain(angle, thumb_min, thumb_max));
        break;

      default:
        Serial.println("Invalid servo number");
        break;
    }

    // Confirm back to Jetson
    Serial.print("OK ");
    Serial.print(servoNum);
    Serial.print(" ");
    Serial.println(angle);
  }
}
