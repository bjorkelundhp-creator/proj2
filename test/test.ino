#include <AccelStepper.h>
#include <MultiStepper.h>

// PIN ASSIGNMENTS
#define xStepPin 11
#define xDirPin 12
#define yStepPin 3
#define yDirPin 2
const int msPin = 13; // Microstepping Enable

// CALCULATIONS
// 66.6667 steps per mm for a 2mm pitch GT2 belt with 24-tooth pulley
const float stepsPerMm = 66.6667; 
const float maxLimitMm = 280.0;

AccelStepper stepperX(1, xStepPin, xDirPin);
AccelStepper stepperY(1, yStepPin, yDirPin);
MultiStepper steppers;

void setup() {
  Serial.begin(9600);
  
  pinMode(msPin, OUTPUT);
  digitalWrite(msPin, HIGH); // Enable 1/16 microstepping for smooth motion

  // MOTOR DIRECTION
  // If Y moves the wrong way, change 'true' to 'false'
  stepperY.setPinsInverted(false, false, false); 
  stepperX.setPinsInverted(false, false, false);

  // PERFORMANCE SETTINGS
  stepperX.setMaxSpeed(3000); 
  stepperY.setMaxSpeed(3000);
  stepperX.setAcceleration(1000); 
  stepperY.setAcceleration(1000);

  steppers.addStepper(stepperX);
  steppers.addStepper(stepperY);

  // Set home position
  stepperX.setCurrentPosition(0);
  stepperY.setCurrentPosition(0);

  // Handshake: Signal to Python that we are powered up and ready
  delay(1000);
  Serial.println("READY"); 
}

void loop() {
  if (Serial.available() > 0) {
    // Read the X-coordinate
    float tx = Serial.parseFloat();
    
    // Look for the comma separating X and Y
    if (Serial.find(",")) {
      float ty = Serial.parseFloat();

      // Constrain within physical board limits
      tx = constrain(tx, 0, maxLimitMm);
      ty = constrain(ty, 0, maxLimitMm);

      long positions[2];
      positions[0] = (long)(tx * stepsPerMm); 
      positions[1] = (long)(ty * stepsPerMm); 

      // Execute coordinated linear move
      steppers.moveTo(positions);
      steppers.runSpeedToPosition(); 
      
      // Handshake: Signal to Python that the move is complete
      Serial.println("OK"); 
      
      // Clear any junk data in the buffer
      while(Serial.available() > 0) { Serial.read(); }
    }
  }
}