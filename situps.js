<!DOCTYPE html>
<html>
<head>
  <title>Sit-Up Counter</title>
  <style>
    canvas { position: absolute; top: 0; left: 0; }
    #counter { position: absolute; top: 10px; left: 20px; font-size: 24px; color: lime; font-family: sans-serif; }
  </style>
</head>
<body>
  <video id="video" playsinline style="display:none;"></video>
  <canvas id="canvas"></canvas>
  <div id="counter">Sit-ups: 0</div>

  <script type="module">
    import { Pose } from 'https://cdn.jsdelivr.net/npm/@mediapipe/pose/pose.js';
    import { Camera } from 'https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js';
    import { drawConnectors, drawLandmarks } from 'https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js';

    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');

    let counter = 0;
    let situpsCount = 0;
    let situps = false;

    function calculate_angle(a, b, c) {
      const ba = [a.x - b.x, a.y - b.y];
      const bc = [c.x - b.x, c.y - b.y];
      const dot = ba[0] * bc[0] + ba[1] * bc[1];
      const magBA = Math.hypot(...ba);
      const magBC = Math.hypot(...bc);
      const cosine = dot / (magBA * magBC);
      const angle = Math.acos(Math.min(Math.max(cosine, -1), 1));
      return angle * 180 / Math.PI;
    }

    const pose = new Pose({
      locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`
    });

    pose.setOptions({
      modelComplexity: 1,
      minDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5
    });

    pose.onResults(results => {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      if (results.poseLandmarks) {
        drawConnectors(ctx, results.poseLandmarks, Pose.POSE_CONNECTIONS, { color: '#00FF00', lineWidth: 2 });
        drawLandmarks(ctx, results.poseLandmarks, { color: '#FF0000', radius: 3 });

        const shoulderL = results.poseLandmarks[11];
        const waistL = results.poseLandmarks[23];
        const kneeL = results.poseLandmarks[25];
        const shoulderR = results.poseLandmarks[12];
        const waistR = results.poseLandmarks[24];
        const kneeR = results.poseLandmarks[26];

        ctx.font = "24px Arial";
        ctx.fillStyle = "lime";
        ctx.fillText(`Sit-ups: ${situpsCount}`, 20, 250);

        if (counter % 3 === 0) {
          const angleL = calculate_angle(shoulderL, waistL, kneeL);
          const angleR = calculate_angle(shoulderR, waistR, kneeR);

          if (angleL < 95 && angleR < 95 && !situps) {
            situpsCount++;
            situps = true;
            document.getElementById("counter").innerText = `Sit-ups: ${situpsCount}`;
          } else if (angleL > 100 && angleR > 100) {
            situps = false;
          }
        }

        counter++;
      }
    });

    const camera = new Camera(video, {
      onFrame: async () => {
        await pose.send({ image: video });
      },
      width: 1280,
      height: 720
    });

    camera.start();
  </script>
</body>
</html>
