import cv2
import mediapipe as mp
import numpy as np
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, model_complexity=1)

cap = cv2.VideoCapture(1)

counter = 0
pushupsCount = 0
pushups = False

def calculate_angle(a, b, c):
    a = np.array([a.x, a.y])
    b = np.array([b.x, b.y])
    c = np.array([c.x, c.y])

    ba = a - b
    bc = c - b

    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(cosine_angle)
    return np.degrees(angle)

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = pose.process(rgb)
    if results.pose_landmarks:
        shoulderR = results.pose_landmarks.landmark[11]
        elbowR = results.pose_landmarks.landmark[13]
        wristR = results.pose_landmarks.landmark[15]

        shoulderL = results.pose_landmarks.landmark[12]
        elbowL = results.pose_landmarks.landmark[14]
        wristL = results.pose_landmarks.landmark[16]

        cv2.putText(frame, f"Push-ups: {pushupsCount}", (20,250), cv2.FONT_HERSHEY_PLAIN, 2, (0,255,0), 3)
        if counter % 3 == 0:
            angleR = calculate_angle(shoulderR, elbowR, wristR)
            angleL = calculate_angle(shoulderL, elbowL, wristL)
            if angleR < 95 and angleL < 95 and not pushups:
                pushupsCount += 1
                pushups = True
                
            elif angleR > 100 and angleL > 100:
                pushups = False
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
