import cv2
import mediapipe as mp

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands

pose = mp_pose.Pose()
hands = mp_hands.Hands(max_num_hands=2)
cap = cv2.VideoCapture(0)

# Optional: Increase resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

counter = 0
squatting = False
gesture_cooldown = 0
show_message = False
message_timer = 0

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results_pose = pose.process(rgb)
    results_hands = hands.process(rgb)

    # Draw pose
    if results_pose.pose_landmarks:
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

    # Detect hand gesture for reset
    if results_hands.multi_hand_landmarks and gesture_cooldown == 0:
        if len(results_hands.multi_hand_landmarks) == 2:
            wrist1 = results_hands.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.WRIST]
            wrist2 = results_hands.multi_hand_landmarks[1].landmark[mp_hands.HandLandmark.WRIST]

            dx = abs(wrist1.x - wrist2.x)
            # print(f"dx = {dx:.2f}")

            if dx > 0.30:  # Reduced threshold for further distance
                counter = 0
                squatting = False
                show_message = True
                message_timer = 60  # Show for ~2 seconds
                print("🔁 Counter reset")
                gesture_cooldown = 30

    if gesture_cooldown > 0:
        gesture_cooldown -= 1

    # Display counter
    cv2.putText(frame, f"Squats: {counter}", (20, 250), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

    # Temporary reset message
    if show_message:
        cv2.putText(frame, "🔁 Counter Reset", (20, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        message_timer -= 1
        if message_timer <= 0:
            show_message = False

    cv2.imshow("Squat Counter with Gesture Reset", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
