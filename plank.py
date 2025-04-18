import cv2
import mediapipe as mp
import math
import time
from collections import deque

UPPER_THRESHOLD = 165
LOWER_THRESHOLD = 155
SMOOTH_WINDOW = 10
DEBOUNCE_FRAMES = 5

mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

angle_buffer = deque(maxlen=SMOOTH_WINDOW)
plank_buffer = deque(maxlen=DEBOUNCE_FRAMES)
waiting_for_start = True
plank_started = False
start_time = 0.0
hold_time = 0.0

# ─── Gesture Detection ──────────────────────────────────────────────────

def detect_start_movement(results_pose, results_hands):
    if not results_pose.pose_landmarks or not results_hands.multi_hand_landmarks:
        return False
    nose_y = results_pose.pose_landmarks.landmark[0].y
    for hand in results_hands.multi_hand_landmarks:
        wrist_y = hand.landmark[mp_hands.HandLandmark.WRIST].y
        if abs(wrist_y - nose_y) < 0.1:
            return True
    return False

def detect_reset_movement(results_hands):
    if not results_hands.multi_hand_landmarks or len(results_hands.multi_hand_landmarks) != 2:
        return False
    wrist1 = results_hands.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.WRIST]
    wrist2 = results_hands.multi_hand_landmarks[1].landmark[mp_hands.HandLandmark.WRIST]
    dx = abs(wrist1.x - wrist2.x)
    return dx > 0.3

# ─── Angle Helper ────────────────────────────────────────────────────────

def calculate_angle(a, b, c):
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    cosang = (ba[0]*bc[0] + ba[1]*bc[1]) / (math.hypot(*ba) * math.hypot(*bc))
    cosang = max(min(cosang, 1.0), -1.0)
    return math.degrees(math.acos(cosang))

# ─── Main Loop ───────────────────────────────────────────────────────────

cap = cv2.VideoCapture(0)
with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose, \
     mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        image = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        results_pose = pose.process(image)
        results_hands = hands.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # ── Gesture Logic ──
        if detect_reset_movement(results_hands):
            waiting_for_start = True
            plank_started = False
            hold_time = 0.0
            angle_buffer.clear()
            plank_buffer.clear()
            print("🔁 Reset detected")

        elif waiting_for_start and detect_start_movement(results_pose, results_hands):
            waiting_for_start = False
            start_time = time.time()
            plank_started = False
            hold_time = 0.0
            print("🟢 Start detected")

        # ── Visual Feedback ──
        if waiting_for_start:
            cv2.putText(image, "✋ Hand on head to start plank", (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        else:
            raw_angle = None
            if results_pose.pose_landmarks:
                lm = results_pose.pose_landmarks.landmark
                def hip_angle(side):
                    s = side.upper()
                    sh = [lm[getattr(mp_pose.PoseLandmark, f"{s}_SHOULDER")].x,
                          lm[getattr(mp_pose.PoseLandmark, f"{s}_SHOULDER")].y]
                    hi = [lm[getattr(mp_pose.PoseLandmark, f"{s}_HIP")].x,
                          lm[getattr(mp_pose.PoseLandmark, f"{s}_HIP")].y]
                    kn = [lm[getattr(mp_pose.PoseLandmark, f"{s}_KNEE")].x,
                          lm[getattr(mp_pose.PoseLandmark, f"{s}_KNEE")].y]
                    return calculate_angle(sh, hi, kn)

                left_ang = hip_angle("LEFT")
                right_ang = hip_angle("RIGHT")
                raw_angle = (left_ang + right_ang) / 2.0
                cv2.putText(image, f"{int(raw_angle)}°", (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            if raw_angle is not None:
                angle_buffer.append(raw_angle)
                avg_angle = sum(angle_buffer) / len(angle_buffer)
                if not plank_started:
                    plank_buffer.append(avg_angle > UPPER_THRESHOLD)
                else:
                    plank_buffer.append(avg_angle > LOWER_THRESHOLD)
            else:
                plank_buffer.append(False)

            is_plank = len(plank_buffer) == DEBOUNCE_FRAMES and all(plank_buffer)

            if is_plank and not plank_started:
                plank_started = True
            elif not is_plank and plank_started:
                plank_started = False

            if plank_started:
                hold_time = time.time() - start_time

            if results_pose.pose_landmarks:
                mp_draw.draw_landmarks(image, results_pose.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            mins, secs = divmod(int(hold_time), 60)
            timer_text = f"{mins:02d}:{secs:02d}"
            cv2.rectangle(image, (0, 0), (220, 90), (0, 0, 0), -1)
            cv2.putText(image, "PLANK", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            cv2.putText(image, timer_text, (10, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)

        cv2.imshow("Plank Timer", image)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
