import cv2
import numpy as np
import serial
import time
import os

# --- 1. SETTINGS ---
SERIAL_PORT = 'COM4' 
BOARD_SIZE_MM = 280.0
SAMPLE_INTERVAL = 0.25     
BRIGHTNESS_THRESHOLD = 190 

last_known_tx, last_known_ty = 140.0, 140.0
has_initial_lock = False   
last_sample_time = 0

script_dir = os.path.dirname(os.path.abspath(__file__))
VIDEO_PATH = os.path.join(script_dir, 'attacking_pattern.mp4') 

# --- 2. SERIAL ---
try:
    ser = serial.Serial(SERIAL_PORT, 9600, timeout=0.1)
    time.sleep(3) 
    while True:
        line = ser.readline().decode().strip()
        if line == "READY": break
        time.sleep(0.5)
except:
    ser = None

cap = cv2.VideoCapture(VIDEO_PATH)
kernel = np.ones((5, 5), np.uint8)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret or frame is None:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue

    current_time = time.time()
    h, w = frame.shape[:2]
    top_c, bot_c = int(h * 0.05), int(h * 0.95)
    left_c, right_c = int(w * 0.05), int(w * 0.95)
    roi = frame[top_c:bot_c, left_c:right_c]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([0, 0, BRIGHTNESS_THRESHOLD]), np.array([180, 50, 255]))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel) 

    if current_time - last_sample_time >= SAMPLE_INTERVAL:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        ball_found = False
        best_candidate = None
        rejection_reason = "No dots"

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 40 < area < 3000:
                # --- SAFE ASPECT RATIO ---
                x_b, y_b, w_b, h_b = cv2.boundingRect(cnt)
                if h_b > 0 and w_b > 0:
                    aspect = float(w_b) / h_b
                    if 0.3 < aspect < 3.0:
                        M = cv2.moments(cnt)
                        if M["m00"] != 0:
                            cx, cy = int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])
                            tx = round(BOARD_SIZE_MM - ((cx / w) * BOARD_SIZE_MM), 1)
                            ty = round(BOARD_SIZE_MM - ((cy / h) * BOARD_SIZE_MM), 1)
                            dist = np.sqrt((tx-last_known_tx)**2 + (ty-last_known_ty)**2)
                            
                            if not has_initial_lock or dist < 250:
                                best_candidate = (tx, ty, cx, cy)
                                ball_found = True
                                break
                            else: rejection_reason = f"Jump {round(dist)}mm"
                    else: rejection_reason = "Zero moment"
                else: continue # Skip 0-height noise
            else: rejection_reason = "Size"

        if ball_found:
            tx, ty, cx, cy = best_candidate
            last_known_tx, last_known_ty = tx, ty
            has_initial_lock = True
            if ser: ser.write(f"{tx},{ty}\n".encode())
            print(f"[{time.strftime('%H:%M:%S')}] LOCK -> X:{tx} Y:{ty}")
            cv2.circle(frame, (cx + left_c, cy + top_c), 20, (0, 255, 0), 3)
        else:
            if ser: ser.write(f"{last_known_tx},{last_known_ty}\n".encode())
            print(f"[{time.strftime('%H:%M:%S')}] FLICKER: {rejection_reason}")

        last_sample_time = current_time

    cv2.imshow("PitchPoint Tracker", frame)
    if cv2.waitKey(20) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()