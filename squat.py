import cv2
import mediapipe as mp

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands

pose = mp_pose.Pose()
hands = mp_hands.Hands(max_num_hands=2)
cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

counter = 0
squatting = False
gesture_cooldown = 0
show_message = False
message_timer = 0
active = False

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results_pose = pose.process(rgb)
    results_hands = hands.process(rgb)

    if results_hands.multi_hand_landmarks and results_pose.pose_landmarks:
        head = results_pose.pose_landmarks.landmark[0] 
        for hand in results_hands.multi_hand_landmarks:
            wrist = hand.landmark[mp_hands.HandLandmark.WRIST]
            distance = abs(wrist.y - head.y)
            if distance < 0.1:
                active = True
                show_message = True
                message_timer = 60
                print(" Gesture detected — Counting enabled")

    if active and results_pose.pose_landmarks:
        mp_drawing.draw_landmarks(frame, results_pose.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        hip1 = results_pose.pose_landmarks.landmark[23]
        hip2 = results_pose.pose_landmarks.landmark[24]
        legL = results_pose.pose_landmarks.landmark[29]
        legR = results_pose.pose_landmarks.landmark[30]

        if abs(hip1.y - legL.y) < 0.25 and abs(hip2.y - legR.y) < 0.25 and not squatting:
            counter += 1
            squatting = True
        elif abs(hip1.y - legL.y) > 0.3 and abs(hip2.y - legR.y) > 0.3:
            squatting = False

    if results_hands.multi_hand_landmarks and gesture_cooldown == 0:
        if len(results_hands.multi_hand_landmarks) == 2:
            wrist1 = results_hands.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.WRIST]
            wrist2 = results_hands.multi_hand_landmarks[1].landmark[mp_hands.HandLandmark.WRIST]

            dx = abs(wrist1.x - wrist2.x)

            if dx > 0.30:
                counter = 0
                squatting = False
                active = False  
                show_message = True
                message_timer = 60
                print(" Counter reset — waiting for hand on head")
                gesture_cooldown = 30

    if gesture_cooldown > 0:
        gesture_cooldown -= 1

    if active:
        cv2.putText(frame, f"Squats: {counter}", (20, 250), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
    else:
        cv2.putText(frame, " Put hand on head to begin", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

    if show_message:
        cv2.putText(frame, " Started" if active else "Counter Reset", (20, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        message_timer -= 1
        if message_timer <= 0:
            show_message = False

    cv2.imshow("Squat Counter (Hand-on-Head to Start)", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
