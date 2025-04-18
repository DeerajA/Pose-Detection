from flask import Flask, render_template, redirect, url_for
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/track/<exercise>')
def track_exercise(exercise):
    # no more count logic!
    return render_template(
        'track.html',
        exercise=exercise.capitalize()
    )

@app.route('/start/<exercise>')
def start_exercise(exercise):
    script_map = {
        'plank': 'plank.py',
        'pushup': 'pushup.py',
        'situp': 'situps.py',
        'squat': 'squat.py'
    }
    if exercise in script_map:
        subprocess.Popen([
            "/Users/Sid/.pyenv/versions/3.10.12/bin/python3.10",
            script_map[exercise]
        ])
    return redirect(url_for('track_exercise', exercise=exercise))

if __name__ == '__main__':
    app.run(debug=True)
