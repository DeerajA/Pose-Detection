<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Plank Timer</title>
  <script src="https://cdn.jsdelivr.net/npm/@mediapipe/pose/pose.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js"></script>
</head>
<body>
  <video id="video" playsinline style="display:none;"></video>
  <canvas id="canvas"></canvas>
  <script>
    const videoElement = document.getElementById('video');
    const canvasElement = document.getElementById('canvas');
    const ctx = canvasElement.getContext('2d');

    // Config
    const UPPER_THRESHOLD = 165;
    const LOWER_THRESHOLD = 155;
    const SMOOTH_WINDOW   = 15;
    const DEBOUNCE_FRAMES = 10;

    // State buffers
    const angleBuffer = [];
    const plankBuffer = [];
    let waitingForStart = true;
    let plankStarted = false;
    let startTime = 0;
    let holdTime = 0;
    let lastPose = null;
    let lastHands = null;

    // Initialize Pose
    const pose = new Pose.Pose({
      locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`,
      modelComplexity: 1,
      enableSegmentation: false,
      smoothLandmarks: true,
      minDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5
    });
    pose.onResults(onResults);

    // Initialize Hands
    const hands = new Hands.Hands({
      locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
      maxNumHands: 2,
      minDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5
    });
    hands.onResults(onResults);

    // Camera setup
    const camera = new Camera.Camera(videoElement, {
      onFrame: async () => {
        await hands.send({ image: videoElement });
        await pose.send({ image: videoElement });
      },
      width: 640,
      height: 480
    });
    camera.start();

    function onResults(results) {
      if (results.poseLandmarks) lastPose = results;
      if (results.multiHandLandmarks) lastHands = results;
      if (!lastPose) return;

      // Draw the frame
      canvasElement.width = videoElement.videoWidth;
      canvasElement.height = videoElement.videoHeight;
      ctx.save();
      ctx.drawImage(videoElement, 0, 0);
      // Draw pose skeleton
      if (lastPose.poseLandmarks) {
        drawConnectors(ctx, lastPose.poseLandmarks, Pose.POSE_CONNECTIONS);
        drawLandmarks(ctx, lastPose.poseLandmarks);
      }

      // Detect reset gesture (hands far apart)
      if (lastHands.multiHandLandmarks && lastHands.multiHandLandmarks.length >= 2) {
        const w1 = lastHands.multiHandLandmarks[0][HandLandmark.WRIST];
        const w2 = lastHands.multiHandLandmarks[1][HandLandmark.WRIST];
        if (Math.abs(w1.x - w2.x) > 0.30) {
          resetState();
        }
      }

      // Detect start gesture (hand near nose)
      if (waitingForStart && lastHands.multiHandLandmarks) {
        const nose = lastPose.poseLandmarks[Pose.PoseLandmark.NOSE];
        for (const hand of lastHands.multiHandLandmarks) {
          const wrist = hand[HandLandmark.WRIST];
          if (wrist.y < nose.y + 0.02) {
            waitingForStart = false;
            startTime = performance.now();
            angleBuffer.length = 0;
            plankBuffer.length = 0;
          }
        }
      }

      // Display prompt or timer
      if (waitingForStart) {
        drawText('Perform start gesture', 10, 50, 'yellow');
      } else {
        trackPlank();
      }

      ctx.restore();
    }

    function trackPlank() {
      // Compute hip angle
      const lm = lastPose.poseLandmarks;
      const avgAngle = ((angle(lm, 'LEFT') + angle(lm, 'RIGHT')) / 2);
      drawText(`Ang: ${avgAngle.toFixed(0)}°`, 10, 100, 'white');

      // Smooth + debounce
      angleBuffer.push(avgAngle);
      if (angleBuffer.length > SMOOTH_WINDOW) angleBuffer.shift();
      const smoothAngle = angleBuffer.reduce((a,b) => a+b)/angleBuffer.length;
      if (!plankStarted) plankBuffer.push(smoothAngle > UPPER_THRESHOLD);
      else plankBuffer.push(smoothAngle > LOWER_THRESHOLD);
      if (plankBuffer.length > DEBOUNCE_FRAMES) plankBuffer.shift();

      // Toggle after consistent reads
      if (!plankStarted && plankBuffer.every(v => v)) {
        plankStarted = true;
        startTime = performance.now();
        plankBuffer.length = 0;
      } else if (plankStarted && plankBuffer.every(v => !v)) {
        plankStarted = false;
        plankBuffer.length = 0;
      }

      // Update hold time
      if (plankStarted) {
        holdTime = (performance.now() - startTime) / 1000;
      }

      // Draw timer UI
      const mins = String(Math.floor(holdTime/60)).padStart(2, '0');
      const secs = String(Math.floor(holdTime % 60)).padStart(2, '0');
      ctx.fillStyle = 'black'; ctx.fillRect(0,0,250,90);
      drawText('PLANK', 10, 30, 'lime');
      drawText(`${mins}:${secs}`, 10, 80, 'white');
    }

    function angle(lm, side) {
      const S = Pose.PoseLandmark;
      const sh = lm[S[side + '_SHOULDER']];
      const hi = lm[S[side + '_HIP']];
      const kn = lm[S[side + '_KNEE']];
      return calculate_angle([sh.x, sh.y], [hi.x, hi.y], [kn.x, kn.y]);
    }

    function resetState() {
      waitingForStart = true;
      plankStarted = false;
      holdTime = 0;
      angleBuffer.length = 0;
      plankBuffer.length = 0;
    }

    function drawText(text, x, y, color) {
      ctx.fillStyle = color;
      ctx.font = '20px sans-serif';
      ctx.fillText(text, x, y);
    }
  </script>
</body>
</html>

