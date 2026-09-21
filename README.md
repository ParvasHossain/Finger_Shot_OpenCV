# 🎯 OpenCV & MediaPipe Finger Gun Game

An interactive, AI-powered computer vision arcade game built using **Python**, **OpenCV**, and Google's latest **MediaPipe Tasks Vision API**. Aim with your index finger, cock your thumb, and shoot target birds appearing on your webcam feed!

---

## 🔥 Features
- 🖐️ **Dual-Hand Support:** Fire independently with both left and right hands simultaneously.
- 🎯 **Interactive Shooting Logic:** Cock your thumb up to load (`READY`), and snap it down to trigger a shot (`BANG!`).
- 🐦 **Spawning Targets:** Randomly generated falling/flying targets to shoot down.
- 💥 **Visual & Audio Effects:** Muzzle flashes at fingertip, moving laser bullets, explosion particle animations, and gunshot audio output.
- 📊 **Real-time HUD:** Displays current gun status and live score tracking.
- 🐍 **Python 3.14 Compatible:** Updated with MediaPipe's modern `Tasks Vision API` (`hand_landmarker.task`).

---

## 🛠️ Project Structure
```text
finger_gunshot_opencv/
│
├── app.py                  # Main game logic and loop
├── hand_landmarker.task    # MediaPipe Hand Landmarker model file
├── gunshot.wav             # Gunshot sound effect
└── README.md               # Project documentation