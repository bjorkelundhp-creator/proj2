import serial
import time
import os
import sys

# Change 'COM3' to your actual Arduino port (e.g., 'COM5' or '/dev/ttyUSB0')
ports = 'COM4' 
baud = 9600
script_dir = os.path.dirname(os.path.abspath(__file__))
FILENAME = os.path.join(script_dir, "coordinates.txt")

try:
    ser = serial.Serial(ports, baud, timeout=1)
    time.sleep(2) # Wait for Arduino to reset
    print("Connected to Arduino.")

    with open(FILENAME, "r") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            
            print(f"Sending: {line}")
            ser.write((line + '\n').encode()) # Send coordinate to Arduino
            
            # Wait for the Arduino to send "OK" back
            while True:
                response = ser.readline().decode().strip()
                if response == "OK":
                    print("Movement finished.")
                    break
    
    print("Sequence Complete!")
    ser.close()

except Exception as e:
    print(f"Error: {e}")