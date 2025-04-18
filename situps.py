import cv2
import mediapipe as mp
import numpy as np

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands

pose = mp_pose.Pose(static_image_mode=False, model_complexity=1, min_detection_confidence=0.5, min_tracking_confidence=0.5)
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

counter = 0
situpsCount = 0
situps = False
gesture_cooldown = 0
show_message = False
message_timer = 0

def calculate_angle(a, b, c):
    a = np.array([a.x, a.y])
    b = np.array([b.x, b.y])
    c = np.array([c.x, c.y])
    ba = a - b
    bc = c - b
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return np.degrees(angle)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results_pose = pose.process(rgb)
    results_hands = hands.process(rgb)

    if results_pose.pose_landmarks:
        shoulderL = results_pose.pose_landmarks.landmark[11]
        waistL = results_pose.pose_landmarks.landmark[23]
        kneeL = results_pose.pose_landmarks.landmark[25]

        shoulderR = results_pose.pose_landmarks.landmark[12]
        waistR = results_pose.pose_landmarks.landmark[24]
        kneeR = results_pose.pose_landmarks.landmark[26]

        if counter % 3 == 0:
            angleL = calculate_angle(shoulderL, waistL, kneeL)
            angleR = calculate_angle(shoulderR, waistR, kneeR)
            if angleR < 95 and angleL < 95 and not situps:
                situpsCount += 1
                situps = True
            elif angleR > 100 and angleL > 100:
                situps = False

        counter += 1
        mp_drawing.draw_landmarks(frame, results_pose.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    if results_hands.multi_hand_landmarks and gesture_cooldown == 0:
        if len(results_hands.multi_hand_landmarks) == 2:
            wrist1 = results_hands.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.WRIST]
            wrist2 = results_hands.multi_hand_landmarks[1].landmark[mp_hands.HandLandmark.WRIST]
            dx = abs(wrist1.x - wrist2.x)

            if dx > 0.30:
                situpsCount = 0
                situps = False
                show_message = True
                message_timer = 60
                print(" Counter reset")
                gesture_cooldown = 30

    if gesture_cooldown > 0:
        gesture_cooldown -= 1

    cv2.putText(frame, f"Sit-ups: {situpsCount}", (20, 250), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 3)

    if show_message:
        cv2.putText(frame, " Counter Reset", (20, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        message_timer -= 1
        if message_timer <= 0:
            show_message = False

    cv2.imshow("Sit-up Counter with Gesture Reset", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
