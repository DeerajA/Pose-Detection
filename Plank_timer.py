import cv2
import mediapipe as mp
import numpy as np
import math
import time
from collections import deque

# ─── Config ───────────────────────────────────────────────────────────────
UPPER_THRESHOLD = 165    # degrees to start counting plank
LOWER_THRESHOLD = 155    # degrees to stop counting plank
SMOOTH_WINDOW   = 15     # number of frames to average for smoothing
DEBOUNCE_FRAMES = 10     # number of consistent frames needed to toggle plank state

# ─── Setup MediaPipe modules ─────────────────────────────────────────────────
mp_pose  = mp.solutions.pose
mp_hands = mp.solutions.hands
mp_draw  = mp.solutions.drawing_utils

pose = mp_pose.Pose(min_detection_confidence=0.5,
                    min_tracking_confidence=0.5)
hands = mp_hands.Hands(static_image_mode=False,
                       max_num_hands=2,
                       min_detection_confidence=0.5,
                       min_tracking_confidence=0.5)

# ─── Helper functions ────────────────────────────────────────────────────────
def calculate_angle(a, b, c):
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    cosang = (ba[0]*bc[0] + ba[1]*bc[1]) / (math.hypot(*ba) * math.hypot(*bc))
    cosang = max(min(cosang, 1.0), -1.0)
    return math.degrees(math.acos(cosang))

# Movement detection based on hand landmarks
def detect_start_movement(results_pose, results_hands):
    if not results_hands.multi_hand_landmarks or not results_pose.pose_landmarks:
        return False
    nose = results_pose.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE]
    for hand in results_hands.multi_hand_landmarks:
        wrist = hand.landmark[mp_hands.HandLandmark.WRIST]
        if wrist.y < nose.y + 0.02:
            return True
    return False

def detect_reset_movement(results_hands):
    if not results_hands.multi_hand_landmarks or len(results_hands.multi_hand_landmarks) < 2:
        return False
    w1 = results_hands.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.WRIST]
    w2 = results_hands.multi_hand_landmarks[1].landmark[mp_hands.HandLandmark.WRIST]
    return abs(w1.x - w2.x) > 0.30

# ─── State buffers and flags ─────────────────────────────────────────────────
angle_buffer      = deque(maxlen=SMOOTH_WINDOW)
plank_buffer      = deque(maxlen=DEBOUNCE_FRAMES)
waiting_for_start = True
plank_started     = False
start_time        = 0.0
hold_time         = 0.0

cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results_pose  = pose.process(rgb)
    results_hands = hands.process(rgb)

    # Reset gesture clears all state
    if detect_reset_movement(results_hands):
        waiting_for_start = True
        plank_started     = False
        hold_time         = 0.0
        angle_buffer.clear()
        plank_buffer.clear()

    # Start gesture arms start detection
    if waiting_for_start and detect_start_movement(results_pose, results_hands):
        waiting_for_start = False
        start_time        = time.time()
        hold_time         = 0.0
        angle_buffer.clear()
        plank_buffer.clear()

    # Show prompt until start gesture
    if waiting_for_start:
        cv2.putText(frame, "Perform start gesture", (10,50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 2)
    else:
        # Compute average hip angle only when pose detected
        raw_angle = None
        if results_pose.pose_landmarks:
            lm = results_pose.pose_landmarks.landmark
            def hip_angle(side):
                sh = lm[getattr(mp_pose.PoseLandmark, side + "_SHOULDER")]
                hi = lm[getattr(mp_pose.PoseLandmark, side + "_HIP")]
                kn = lm[getattr(mp_pose.PoseLandmark, side + "_KNEE")]
                return calculate_angle((sh.x, sh.y), (hi.x, hi.y), (kn.x, kn.y))
            left_ang  = hip_angle('LEFT')
            right_ang = hip_angle('RIGHT')
            raw_angle = (left_ang + right_ang) / 2.0
            cv2.putText(frame, f"Ang: {int(raw_angle)}°", (10,100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

        # Only smooth if angle valid
        if raw_angle is not None:
            angle_buffer.append(raw_angle)
            avg_angle = sum(angle_buffer) / len(angle_buffer)
            # Debounce with hysteresis
            if not plank_started:
                plank_buffer.append(avg_angle > UPPER_THRESHOLD)
            else:
                plank_buffer.append(avg_angle > LOWER_THRESHOLD)
        else:
            plank_buffer.append(False)

        # Only toggle after consistent readings
        if len(plank_buffer) == DEBOUNCE_FRAMES:
            if not plank_started and all(plank_buffer):
                plank_started = True
                start_time    = time.time()
                plank_buffer.clear()
            elif plank_started and not any(plank_buffer):
                plank_started = False
                plank_buffer.clear()

        # Count hold time if started
        if plank_started:
            hold_time = time.time() - start_time

        # Draw skeleton
        if results_pose.pose_landmarks:
            mp_draw.draw_landmarks(frame, results_pose.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        # Display timer
        mins, secs = divmod(int(hold_time), 60)
        cv2.rectangle(frame, (0,0), (250,90), (0,0,0), -1)
        cv2.putText(frame, "PLANK", (10,30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
        cv2.putText(frame, f"{mins:02d}:{secs:02d}", (10,80),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2)

    cv2.imshow("Plank Timer", frame)
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
