import { Pose } from 'https://cdn.jsdelivr.net/npm/@mediapipe/pose';
import { Hands } from 'https://cdn.jsdelivr.net/npm/@mediapipe/hands';
import { Camera } from 'https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils';

let counter = 0;
let squatting = false;
let gestureCooldown = 0;
let showMessage = false;
let messageTimer = 0;
let active = false;

const videoElement = document.getElementById('video');
const canvasElement = document.getElementById('output');
const canvasCtx = canvasElement.getContext('2d');

function onResults(results) {
  canvasCtx.save();
  canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
  canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);

  // ✋ Hand on head = start
  if (results.poseLandmarks && results.multiHandLandmarks && !active) {
    const head = results.poseLandmarks[0]; // Nose
    for (const hand of results.multiHandLandmarks) {
      const wrist = hand[0]; // WRIST
      if (Math.abs(wrist.y - head.y) < 0.1) {
        active = true;
        showMessage = true;
        messageTimer = 60;
        console.log("🟢 Gesture detected — Counting enabled");
      }
    }
  }

  // 🏋️ Squat counting logic
  if (active && results.poseLandmarks) {
    const lm = results.poseLandmarks;
    const hip1 = lm[23], hip2 = lm[24], legL = lm[29], legR = lm[30];

    if (Math.abs(hip1.y - legL.y) < 0.25 && Math.abs(hip2.y - legR.y) < 0.25 && !squatting) {
      counter++;
      squatting = true;
    } else if (Math.abs(hip1.y - legL.y) > 0.3 && Math.abs(hip2.y - legR.y) > 0.3) {
      squatting = false;
    }
  }

  // 🔁 Hands apart = reset
  if (results.multiHandLandmarks && results.multiHandLandmarks.length === 2 && gestureCooldown === 0) {
    const wrist1 = results.multiHandLandmarks[0][0];
    const wrist2 = results.multiHandLandmarks[1][0];
    const dx = Math.abs(wrist1.x - wrist2.x);

    if (dx > 0.3) {
      counter = 0;
      squatting = false;
      active = false;
      showMessage = true;
      messageTimer = 60;
      console.log("🔁 Counter reset — waiting for hand on head");
      gestureCooldown = 30;
    }
  }

  if (gestureCooldown > 0) gestureCooldown--;

  // 🖼️ UI feedback
  canvasCtx.font = '24px Arial';
  canvasCtx.fillStyle = active ? 'lime' : 'yellow';
  canvasCtx.fillText(active ? `Squats: ${counter}` : "✋ Put hand on head to begin", 20, 40);

  if (showMessage) {
    canvasCtx.fillStyle = 'red';
    canvasCtx.fillText(active ? "🟢 Started" : "🔁 Counter Reset", 20, 80);
    messageTimer--;
    if (messageTimer <= 0) showMessage = false;
  }

  canvasCtx.restore();
}

// MediaPipe setup
const pose = new Pose({ locateFile: file => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}` });
pose.setOptions({
  modelComplexity: 1,
  smoothLandmarks: true,
  minDetectionConfidence: 0.5,
  minTrackingConfidence: 0.5
});

const hands = new Hands({ locateFile: file => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}` });
hands.setOptions({
  maxNumHands: 2,
  minDetectionConfidence: 0.5,
  minTrackingConfidence: 0.5
});

pose.onResults(onResults);
hands.onResults(onResults);

// Start the camera
const camera = new Camera(videoElement, {
  onFrame: async () => {
    await pose.send({ image: videoElement });
    await hands.send({ image: videoElement });
  },
  width: 640,
  height: 480
});
camera.start();

