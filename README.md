# Exercise Tracker

This is a fitness tracking web application that utilizes a computer’s webcam, along with Python and OpenCV, to monitor body movements and accurately count repetitions for common exercises such as squats, push-ups, sit-ups, and planks.

This was built with Flask for navigation and MediaPipe for pose detection.


## Features

- Exercises the program tracks:
  - Squats
  - Push-Ups
  - Sit-Ups
  - Plank (with timer)
- Gesture detection:
  - Hand on head to start
  - Hands apart to reset
- Browser interface using Flask
- Pose detection with OpenCV and MediaPipe
- Runs locally on your machine — no data sent to servers


## Project Structure

exercise-tracker/
├── app.py             
├── squat.py           
├── pushup.py         
├── situp.py           
├── plank.py           
├── templates/
│   ├── index.html     
│   └── track.html     
└── static/            
```


## How to Run

1. **Install dependencies**

```bash
pip install flask opencv-python mediapipe
```

2. **Start the Flask app**

```bash
python app.py
```

3. **Open your browser** and visit:  
   [http://localhost:5000](http://localhost:5000)

4. **Choose an exercise**, and grant camera permission


## Requirements

- Python 3.8+
- Webcam
- Flask
- OpenCV
- MediaPipe


## Tips

- If your exercise window opens behind the browser, add this to your Python scripts:

```python
cv2.namedWindow("Pose", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("Pose", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
```

- To avoid hardcoding your Python path in `app.py`, replace:

```python
"/Users/you/path/to/python3"
```

with:

```python
import sys
sys.executable
```



## Credits

- [MediaPipe](https://mediapipe.dev) for pose detection
- [Flask](https://flask.palletsprojects.com/) for routing
- Built by students and fitness tech enthusiasts
