import cv2
import mediapipe as mp
import math
import time
from collections import deque

# ─── Config ───────────────────────────────────────────────────────────────
UPPER_THRESHOLD = 165    # start plank only when above this angle
LOWER_THRESHOLD = 155    # stop plank when below this angle
SMOOTH_WINDOW   = 10     # frames to average for smoothing
DEBOUNCE_FRAMES = 5      # frames to confirm entry/exit

# ─── Setup ───────────────────────────────────────────────────────────────
mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils

# Movement detection placeholders
# These should be replaced with your actual movement-detection logic

def detect_start_movement(results):
    """Return True when the "start" movement is detected."""
    # TODO: implement detection of the specific start movement
    return False

def detect_reset_movement(results):
    """Return True when the "reset" movement is detected."""
    # TODO: implement detection of the specific reset movement
    return False

# Angle calculation helper
def calculate_angle(a, b, c):
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    cosang = (ba[0]*bc[0] + ba[1]*bc[1]) / (math.hypot(*ba) * math.hypot(*bc))
    cosang = max(min(cosang, 1.0), -1.0)
    return math.degrees(math.acos(cosang))

# State buffers and flags
angle_buffer     = deque(maxlen=SMOOTH_WINDOW)
plank_buffer     = deque(maxlen=DEBOUNCE_FRAMES)
waiting_for_start = True
plank_started     = False
start_time        = 0.0
hold_time         = 0.0

cap = cv2.VideoCapture(0)
with mp_pose.Pose(min_detection_confidence=0.5,
                  min_tracking_confidence=0.5) as pose:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Mirror and process frame
        image   = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        results = pose.process(image)
        image   = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Check for start/reset movements each frame
        if detect_reset_movement(results):
            # Reset timer state
            waiting_for_start = True
            plank_started     = False
            hold_time         = 0.0
            angle_buffer.clear()
            plank_buffer.clear()
        elif waiting_for_start and detect_start_movement(results):
            # Begin plank detection
            waiting_for_start = False
            start_time        = time.time()
            plank_started     = False
            hold_time         = 0.0

        # If not yet started, skip angle/pHank detection
        if waiting_for_start:
            cv2.putText(image, "Waiting for start movement", (10,50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
        else:
            # Compute hip angle if pose detected
            raw_angle = None
            if results.pose_landmarks:
                lm = results.pose_landmarks.landmark
                def hip_angle(side):
                    s = side.upper()
                    sh = [lm[getattr(mp_pose.PoseLandmark, f"{s}_SHOULDER")].x,
                          lm[getattr(mp_pose.PoseLandmark, f"{s}_SHOULDER")].y]
                    hi = [lm[getattr(mp_pose.PoseLandmark, f"{s}_HIP")].x,
                          lm[getattr(mp_pose.PoseLandmark, f"{s}_HIP")].y]
                    kn = [lm[getattr(mp_pose.PoseLandmark, f"{s}_KNEE")].x,
                          lm[getattr(mp_pose.PoseLandmark, f"{s}_KNEE")].y]
                    return calculate_angle(sh, hi, kn)

                left_ang  = hip_angle("LEFT")
                right_ang = hip_angle("RIGHT")
                raw_angle = (left_ang + right_ang) / 2.0
                cv2.putText(image, f"{int(raw_angle)}°", (10,50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

            # Smooth and debounce if we have an angle
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

            # Start or stop the timer
            if is_plank and not plank_started:
                plank_started = True
            elif not is_plank and plank_started:
                plank_started = False

            # Update hold_time only while in plank
            if plank_started:
                hold_time = time.time() - start_time

            # Draw skeleton if available
            if results.pose_landmarks:
                mp_draw.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            # Display timer
            mins, secs = divmod(int(hold_time), 60)
            timer_text = f"{mins:02d}:{secs:02d}"
            cv2.rectangle(image, (0,0), (220,90), (0,0,0), -1)
            cv2.putText(image, "PLANK", (10,30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
            cv2.putText(image, timer_text, (10,80),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2)

        cv2.imshow("Plank Timer", image)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
