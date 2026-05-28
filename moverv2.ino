#include <AccelStepper.h>
#include <MultiStepper.h>

// --- PIN CONFIGURATION ---
const int msPin = 13;      // MS1, MS2, MS3 all tied here for 1/16 step

#define xStepPin 11
#define xDirPin 12
#define yStepPin 3
#define yDirPin 2

// --- CALIBRATED SYSTEM CONFIGURATION ---
// Math: 3200 steps / 48mm per rev (24 teeth * 2mm pitch) = 66.6667
const float stepsPerMm = 66.6667; 
const float maxLimitMm = 280.0;

// Create stepper objects
AccelStepper stepperX(1, xStepPin, xDirPin);
AccelStepper stepperY(1, yStepPin, yDirPin);

// Create MultiStepper manager
MultiStepper steppers;

void setup() {
  Serial.begin(9600);

  // 1. Setup Microstepping (Pin 13)
  // This keeps both drivers in 1/16 mode constantly
  pinMode(msPin, OUTPUT);
  digitalWrite(msPin,HIGH); 

  // 2. Configure Speed 
  // You can increase these if the movement feels too slow
  stepperX.setMaxSpeed(2500);
  stepperY.setMaxSpeed(2500);

  // 3. Register steppers with the manager
  steppers.addStepper(stepperX);
  steppers.addStepper(stepperY);

  // 4. Set Home (0,0) at current physical location
  stepperX.setCurrentPosition(0);
  stepperY.setCurrentPosition(0);

  Serial.println("--- SYSTEM READY (No Enable Pin) ---");
  Serial.println("Units: mm | Pulley: 24-Tooth | Microstep: 1/16");
  Serial.println("Enter target as: X,Y (e.g., 100,50)");
}

void loop() {
  if (Serial.available() > 0) {
    // Read X coordinate
    float targetX = Serial.parseFloat();
    
    // Look for the comma before reading Y
    if (Serial.find(",")) {
      float targetY = Serial.parseFloat();

      // Constrain within the 280mm x 280mm work area
      targetX = constrain(targetX, 0, maxLimitMm);
      targetY = constrain(targetY, 0, maxLimitMm);

      // Convert target mm to absolute step positions
      long positions[2];
      positions[0] = (long)(targetX * stepsPerMm); 
      positions[1] = (long)(targetY * stepsPerMm); 

      Serial.print("Moving to Absolute: ");
      Serial.print(targetX); Serial.print("mm, ");
      Serial.print(targetY); Serial.println("mm");

      // Execute the move
      // MultiStepper ensures both axes finish at the same time
      steppers.moveTo(positions);
      steppers.runSpeedToPosition(); 
      
      Serial.println("Target Reached.");
      
      // Clear anything extra in the Serial buffer
      while(Serial.available() > 0) { Serial.read(); }
    }
  }
}