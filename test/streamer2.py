import cv2
import numpy as np
import serial
import time
import os

# --- SETTINGS ---
VIDEO_PATH = 'attacking_pattern.mp4' 
SERIAL_PORT = 'COM4' # Updated based on your previous error
BOARD_SIZE_MM = 280.0

# HSV color for the white ball (Adjust if needed)
LOWER_WHITE = np.array([0, 0, 220]) 
UPPER_WHITE = np.array([180, 30, 255])

try:
    ser = serial.Serial(SERIAL_PORT, 9600, timeout=0.01)
    time.sleep(2)
    print(f"Connected to {SERIAL_PORT}. Displaying Video...")
except:
    print(f"Serial Error: Is {SERIAL_PORT} open in Arduino IDE?")
    exit()

cap = cv2.VideoCapture(VIDEO_PATH)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Loop video
        continue

    v_h, v_w = frame.shape[:2]

    # 1. Image Processing
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LOWER_WHITE, UPPER_WHITE)
    
    # 2. Find the Ball
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        best_cnt = max(contours, key=cv2.contourArea)
        if cv2.contourArea(best_cnt) > 5:
            M = cv2.moments(best_cnt)
            if M["m00"] != 0:
                px = int(M["m10"] / M["m00"]) 
                py = int(M["m01"] / M["m00"]) 

                # --- 1:1 CENTERED MAPPING ---
                tx = (py / v_h) * BOARD_SIZE_MM
                physical_width_mm = (v_w / v_h) * BOARD_SIZE_MM
                margin_y = (BOARD_SIZE_MM - physical_width_mm) / 2
                ty = margin_y + ((px / v_w) * physical_width_mm)

                # Send to Arduino
                command = f"{round(tx, 1)},{round(ty, 1)}\n"
                ser.write(command.encode())
                
                # DRAWING: Draw a green circle on the "Ball"
                cv2.circle(frame, (px, py), 15, (0, 255, 0), 2)
                cv2.putText(frame, f"X:{round(tx)} Y:{round(ty)}", (px+20, py), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # --- SHOW THE VIDEO ---
    cv2.imshow("PitchPoint Live Tracking", frame) # Main Video
    cv2.imshow("Computer Vision Mask", mask)      # What the AI sees (White = Detected)

    # Press 'q' on your keyboard to stop
    if cv2.waitKey(20) & 0xFF == ord('q'):
        break

cap.release()
ser.close()
cv2.destroyAllWindows()