from flask import Flask, render_template
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start')
def start_camera():
    subprocess.Popen("python3 Pushups.py", shell=True)
    return "Camera started. Close the camera window to return."
    
if __name__ == "__main__":
    app.run(debug=True)
