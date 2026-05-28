import cv2
import numpy as np
import serial
import time
import os

# --- 1. CALIBRATION ---
SERIAL_PORT = 'COM4' 
BOARD_SIZE_MM = 280.0
SAMPLE_INTERVAL = 0.15     

# SATURATION IS KEY: 
# Lower bound: Neutral colors (0 saturation)
# Upper bound: Max saturation 60 (This deletes the vivid red/blue of players)
LOWER_BALL = np.array([0, 0, 100]) 
UPPER_BALL = np.array([180, 60, 255]) 

# Memory
curr_x, curr_y = 140.0, 140.0 
last_known_tx, last_known_ty = 140.0, 140.0
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
kernel = np.ones((6, 6), np.uint8)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret or frame is None:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0); continue

    current_time = time.time()
    h, w = frame.shape[:2]
    # Wide ROI to cover the whole tactical view
    roi = frame[int(h*0.02):int(h*0.98), int(w*0.02):int(w*0.98)]

    # --- 2. HSV SATURATION FILTER ---
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    # This specifically targets 'grayscale' objects and ignores 'colored' objects
    mask = cv2.inRange(hsv, LOWER_BALL, UPPER_BALL)
    
    # Cleaning the mask
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel) 

    if current_time - last_sample_time >= SAMPLE_INTERVAL:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        ball_found = False
        best_candidate = None
        min_dist = 9999 

        for cnt in contours:
            area = cv2.contourArea(cnt)
            
            # In tactical view, ball area is usually 150-600 pixels
            if 100 < area < 1000: 
                x_b, y_b, w_b, h_b = cv2.boundingRect(cnt)
                aspect = float(w_b) / h_b
                
                # The ball is almost perfectly square/circular (1.0 ratio)
                if 0.7 < aspect < 1.4:
                    M = cv2.moments(cnt)
                    if M["m00"] != 0:
                        cx, cy = int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])
                        
                        # Mapping to Physical Board
                        tx = round(BOARD_SIZE_MM - ((cx / w) * BOARD_SIZE_MM), 1)
                        ty = round(BOARD_SIZE_MM - ((cy / h) * BOARD_SIZE_MM), 1)
                        
                        dist = np.sqrt((tx-last_known_tx)**2 + (ty-last_known_ty)**2)

                        # Logic: Pick the candidate closest to where the ball was last
                        if not has_initial_lock or dist < 200:
                            if dist < min_dist:
                                min_dist = dist
                                best_candidate = (tx, ty, cx, cy)
                                ball_found = True

        if ball_found:
            tx, ty, cx, cy = best_candidate
            # Exponential Smoothing (0.8 = high trust in new movement)
            curr_x = (0.8 * tx) + (0.2 * curr_x)
            curr_y = (0.8 * ty) + (0.2 * curr_y)
            
            last_known_tx, last_known_ty = tx, ty
            has_initial_lock = True
            
            if ser: ser.write(f"{round(curr_x, 1)},{round(curr_y, 1)}\n".encode())
            print(f"[{time.strftime('%H:%M:%S')}] BALL LOCK -> X:{round(curr_x, 1)} Y:{round(curr_y, 1)}")
            
            # Visual Feedback
            cv2.circle(frame, (cx + int(w*0.02), cy + int(h*0.02)), 20, (0, 255, 0), 3)
        
        last_sample_time = current_time

    cv2.imshow("PitchPoint: Tactical View", frame)
    cv2.imshow("Mask (Should be ONLY the ball)", mask)
    
    if cv2.waitKey(15) & 0xFF == ord('q'): break

cap.release()
if ser: ser.close()
cv2.destroyAllWindows()