import cv2
import numpy as np
import serial
import time
import os

# --- 1. SETTINGS: THE "GOLDILOCKS" ZONE ---
SERIAL_PORT = 'COM6' 
BOARD_SIZE_MM = 280.0
SAMPLE_INTERVAL = 0.12     

# LOOSENED FILTERS
BRIGHTNESS_THRESHOLD = 175 # Lowered from 200 to catch blurred/dimmer balls
CIRCULARITY_CUTOFF = 0.25  # Lowered from 0.45 to allow for ovals/smears

# Memory
curr_x, curr_y = 140.0, 140.0 
last_raw_x, last_raw_y = 140.0, 140.0 
has_initial_lock = False   
last_sample_time = 0

script_dir = os.path.dirname(os.path.abspath(__file__))
VIDEO_PATH = os.path.join(script_dir, 'attacking_pattern.mp4') 

try:
    ser = serial.Serial(SERIAL_PORT, 9600, timeout=0.1)
    time.sleep(3)
except:
    ser = None

cap = cv2.VideoCapture(VIDEO_PATH)
kernel = np.ones((3, 3), np.uint8) # Back to 3x3 so we don't "rub out" the ball

while cap.isOpened():
    ret, frame = cap.read()
    if not ret or frame is None:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0); continue

    current_time = time.time()
    h, w = frame.shape[:2]
    roi = frame[int(h*0.05):int(h*0.95), int(w*0.05):int(w*0.95)] 

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([0, 0, BRIGHTNESS_THRESHOLD]), np.array([180, 60, 255]))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel) 

    if current_time - last_sample_time >= SAMPLE_INTERVAL:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        ball_found = False
        best_candidate = None
        highest_score = -1 
        
        diag_msg = "No white dots in mask"

        for cnt in contours:
            area = cv2.contourArea(cnt)
            
            # Filter 1: Size
            if area < 30:
                diag_msg = f"Blob too small ({int(area)})"
                continue
            if area > 2000:
                diag_msg = f"Blob too big ({int(area)})"
                continue
                
            # Filter 2: Circularity
            (cx_f, cy_f), radius = cv2.minEnclosingCircle(cnt)
            circle_area = np.pi * (radius ** 2)
            if circle_area == 0: continue
            circularity = area / circle_area
            
            if circularity < CIRCULARITY_CUTOFF:
                diag_msg = f"Rejected Line (Circ: {round(circularity, 2)})"
                continue

            # Calculate Physics
            tx = round(BOARD_SIZE_MM - ((cx_f / w) * BOARD_SIZE_MM), 1)
            ty = round(BOARD_SIZE_MM - ((cy_f / h) * BOARD_SIZE_MM), 1)
            dist = np.sqrt((tx-last_raw_x)**2 + (ty-last_raw_y)**2)
            
            # If we pass filters, this is a valid ball candidate
            # We score it: Higher is Rounder + Closer
            score = circularity / (dist + 1)

            if not has_initial_lock or dist < 250:
                if score > highest_score:
                    highest_score = score
                    best_candidate = (tx, ty, int(cx_f), int(cy_f))
                    ball_found = True

        if ball_found:
            tx, ty, cx, cy = best_candidate
            last_raw_x, last_raw_y = tx, ty
            
            # Smoothing (EMA)
            curr_x = (0.4 * tx) + (0.6 * curr_x)
            curr_y = (0.4 * ty) + (0.6 * curr_y)
            has_initial_lock = True
            
            if ser: ser.write(f"{round(curr_x, 1)},{round(curr_y, 1)}\n".encode())
            print(f"[{time.strftime('%H:%M:%S')}] LOCK -> X:{round(curr_x,1)} (Circ: {round(highest_score,2)})")
            cv2.circle(frame, (cx + int(w*0.05), cy + int(h*0.05)), 20, (0, 255, 0), 3)
        else:
            print(f"[{time.strftime('%H:%M:%S')}] SEARCHING: {diag_msg}")

        last_sample_time = current_time

    cv2.imshow("PitchPoint Tracker", frame)
    cv2.imshow("Mask View", mask)
    if cv2.waitKey(15) & 0xFF == ord('q'): break

cap.release()
if ser: ser.close()
cv2.destroyAllWindows()