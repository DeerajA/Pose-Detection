<!DOCTYPE html>
<html>
<head>
  <title>Push-Up Counter</title>
  <style>
    canvas { position: absolute; top: 0; left: 0; }
    #counter { position: absolute; top: 10px; left: 20px; font-size: 24px; color: lime; font-family: sans-serif; }
  </style>
</head>
<body>
  <video id="video" playsinline style="display:none;"></video>
  <canvas id="canvas"></canvas>
  <div id="counter">Push-ups: 0</div>

  <script type="module">
    import { Pose } from 'https://cdn.jsdelivr.net/npm/@mediapipe/pose/pose.js';
    import { Hands } from 'https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js';
    import { Camera } from 'https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js';
    import { drawConnectors, drawLandmarks } from 'https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js';

    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    let pushups = 0;
    let active = false;
    let pushupState = false;
    let cooldown = 0;
    let showMessage = "";
    let messageTimer = 0;

    function calculateAngle(a, b, c) {
      const ab = [a.x - b.x, a.y - b.y];
      const cb = [c.x - b.x, c.y - b.y];
      const dot = ab[0]*cb[0] + ab[1]*cb[1];
      const magAB = Math.hypot(...ab);
      const magCB = Math.hypot(...cb);
      const cosine = dot / (magAB * magCB);
      const angle = Math.acos(Math.min(Math.max(cosine, -1.0), 1.0));
      return angle * 180 / Math.PI;
    }

    const pose = new Pose({
      locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`
    });

    const hands = new Hands({
      locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
    });

    pose.setOptions({
      modelComplexity: 1,
      minDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5
    });

    hands.setOptions({
      maxNumHands: 2,
      minDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5
    });

    let poseResults = null;
    let handResults = null;

    pose.onResults(results => {
      poseResults = results;
    });

    hands.onResults(results => {
      handResults = results;
    });

    const camera = new Camera(video, {
      onFrame: async () => {
        await pose.send({ image: video });
        await hands.send({ image: video });
        draw();
      },
      width: 1280,
      height: 720
    });
    camera.start();

    function draw() {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      if (poseResults && poseResults.poseLandmarks) {
        drawConnectors(ctx, poseResults.poseLandmarks, Pose.POSE_CONNECTIONS, { color: '#00FF00', lineWidth: 2 });
        drawLandmarks(ctx, poseResults.poseLandmarks, { color: '#FF0000', radius: 3 });

        const lShoulder = poseResults.poseLandmarks[11];
        const lElbow = poseResults.poseLandmarks[13];
        const lWrist = poseResults.poseLandmarks[15];
        const rShoulder = poseResults.poseLandmarks[12];
        const rElbow = poseResults.poseLandmarks[14];
        const rWrist = poseResults.poseLandmarks[16];
        const nose = poseResults.poseLandmarks[0];

        if (handResults && handResults.multiHandLandmarks && !active) {
          for (const hand of handResults.multiHandLandmarks) {
            const wrist = hand[0];
            if (Math.abs(wrist.y - nose.y) < 0.1) {
              active = true;
              pushups = 0;
              showMessage = "Started";
              messageTimer = 60;
              break;
            }
          }
        }

        if (active) {
          const angleL = calculateAngle(lShoulder, lElbow, lWrist);
          const angleR = calculateAngle(rShoulder, rElbow, rWrist);

          if (angleL < 95 && angleR < 95 && !pushupState) {
            pushups++;
            document.getElementById("counter").innerText = `Push-ups: ${pushups}`;
            pushupState = true;
          } else if (angleL > 100 && angleR > 100) {
            pushupState = false;
          }
        }
      }

      if (handResults && handResults.multiHandLandmarks && handResults.multiHandLandmarks.length === 2 && cooldown === 0) {
        const h1 = handResults.multiHandLandmarks[0][0];
        const h2 = handResults.multiHandLandmarks[1][0];
        if (Math.abs(h1.x - h2.x) > 0.3) {
          pushups = 0;
          document.getElementById("counter").innerText = `Push-ups: 0`;
          active = false;
          showMessage = "Counter Reset";
          messageTimer = 60;
          cooldown = 30;
        }
      }

      if (cooldown > 0) cooldown--;

      if (showMessage) {
        ctx.font = "30px Arial";
        ctx.fillStyle = "red";
        ctx.fillText(showMessage, 20, 350);
        messageTimer--;
        if (messageTimer <= 0) showMessage = "";
      }

      if (!active) {
        ctx.font = "24px Arial";
        ctx.fillStyle = "yellow";
        ctx.fillText("✋ Put hand on head to start", 20, 100);
      }

      requestAnimationFrame(draw);
    }
  </script>
</body>
</html>
