import cv2
import mediapipe as mp
import numpy as np
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, model_complexity=1)

cap = cv2.VideoCapture(1)

counter = 0
squatCount = 0
squatting = False

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = pose.process(rgb)
    if results.pose_landmarks:
        hip1 = results.pose_landmarks.landmark[23]
        hip2 = results.pose_landmarks.landmark[24]
        legL = results.pose_landmarks.landmark[29]
        legR = results.pose_landmarks.landmark[30]
        cv2.putText(frame, f"Squats: {squatCount}", (20,250), cv2.FONT_HERSHEY_PLAIN, 2, (0,255,0), 3)
        if counter % 3 == 0:
            
            if (abs(hip1.y - legL.y) < 0.25 and abs(hip2.y - legR.y) < 0.25 and not squatting):
                squatCount += 1
                squatting = True
                
            elif (abs(hip1.y - legL.y) > 0.3 and abs(hip2.y - legR.y) > 0.3):
                squatting = False

    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )
        counter += 1

    cv2.imshow("Pose Skeleton", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()