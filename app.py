from flask import Flask, render_template, redirect, url_for
import subprocess


app = Flask(__name__)


@app.route('/')
def index():
   return render_template('index.html')


@app.route('/start/<exercise>')
def start_exercise(exercise):
   script_map = {
       'plank': 'plank.py',
       'pushup': 'pushup.py',
       'situp': 'situp.py',
       'squat': 'squat.py'
   }
   if exercise in script_map:
       subprocess.Popen(["python", script_map[exercise]])
   return redirect(url_for('index'))


if __name__ == '__main__':
   app.run(debug=True)
