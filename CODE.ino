#include "AccelStepper.h"

// Motor 1 Pins (Original)
#define dirPin1 2
#define stepPin1 3

// Motor 2 Pins (New)
#define dirPin2 4
#define stepPin2 10

// Interface type 1 is for a dedicated driver like the A4988
#define motorInterfaceType 1

// Create two instances of the AccelStepper class
AccelStepper stepper1 = AccelStepper(motorInterfaceType, stepPin1, dirPin1);
AccelStepper stepper2 = AccelStepper(motorInterfaceType, stepPin2, dirPin2);

void setup() {
  // Set Max Speed for both. 1000 is a solid high-speed target for 12V.
  stepper1.setMaxSpeed(1000);
  stepper2.setMaxSpeed(1000);

  // Set the constant speeds. 
  // Notice stepper2 is NEGATIVE to rotate the opposite way.
  stepper1.setSpeed(800);
  stepper2.setSpeed(-800); 
}

void loop() {
  // Execute the steps for both motors
  // runSpeed() must be called as fast as possible for both to avoid "jerking"
  stepper1.runSpeed();
  stepper2.runSpeed();
}