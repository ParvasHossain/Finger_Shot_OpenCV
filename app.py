import cv2
import math
import random
import pygame
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Initialize sound mixer
pygame.mixer.init()
try:
    gun_sound = pygame.mixer.Sound("gunshot.wav")
except Exception as e:
    print("Warning: gunshot.wav not found or could not be loaded.", e)
    gun_sound = None

# Set to 0 for default laptop webcam
CAMERA_URL = 0 

# Initialize MediaPipe Hand Landmarker (Tasks API)
base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5
)
detector = vision.HandLandmarker.create_from_options(options)

# Hand connections for skeleton drawing
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20) # Pinky
]

cap = cv2.VideoCapture(CAMERA_URL)

bullets = []
birds = []
explosions = []

flash_counter = 0
was_cocked = False
score = 0
bird_spawn_timer = 0

def dist_3d(p1, p2):
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)

def dist_2d(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Waiting for camera frame...")
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    detection_result = detector.detect(mp_image)

    status_text = "Searching Hand..."
    status_color = (150, 150, 150)

    # -------------------------------------------------------------
    # 1. SPAWN BIRDS / TARGETS
    # -------------------------------------------------------------
    bird_spawn_timer += 1
    if bird_spawn_timer > 40:  # Spawns a new bird every ~1.5 seconds
        bird_spawn_timer = 0
        birds.append({
            'x': float(random.randint(50, w - 50)),
            'y': -20.0,
            'vx': random.choice([-1.5, -0.5, 0.5, 1.5]),
            'vy': random.uniform(2.0, 4.0),
            'radius': random.randint(20, 30),
            'color': (random.randint(50, 255), random.randint(50, 255), 255)
        })

    # -------------------------------------------------------------
    # 2. HAND POSE & FINGER GUN DETECTION
    # -------------------------------------------------------------
    if detection_result.hand_landmarks:
        for hand_landmarks in detection_result.hand_landmarks:
            lm = hand_landmarks

            # Draw Hand Skeleton
            for conn in HAND_CONNECTIONS:
                pt1 = (int(lm[conn[0]].x * w), int(lm[conn[0]].y * h))
                pt2 = (int(lm[conn[1]].x * w), int(lm[conn[1]].y * h))
                cv2.line(frame, pt1, pt2, (180, 230, 30), 2)

            for l in lm:
                pt = (int(l.x * w), int(l.y * h))
                cv2.circle(frame, pt, 4, (255, 255, 255), -1)

            palm_scale = dist_3d(lm[0], lm[9])
            if palm_scale == 0:
                continue

            d_mid   = dist_3d(lm[12], lm[0]) / palm_scale
            d_ring  = dist_3d(lm[16], lm[0]) / palm_scale
            d_pinky = dist_3d(lm[20], lm[0]) / palm_scale
            d_index = dist_3d(lm[8], lm[0]) / palm_scale
            d_index_knuckle = dist_3d(lm[5], lm[0]) / palm_scale

            thumb_ratio = dist_3d(lm[4], lm[5]) / palm_scale

            is_curled = (d_mid < 1.05) and (d_ring < 1.0) and (d_pinky < 0.95)
            is_index_out = d_index > (d_index_knuckle * 1.35)
            is_gun = is_curled and is_index_out

            tip_px = (int(lm[8].x * w), int(lm[8].y * h))

            if is_gun:
                cv2.circle(frame, tip_px, 8, (0, 0, 255), -1)

                if thumb_ratio > 0.65:
                    was_cocked = True
                    status_text = "READY / COCKED"
                    status_color = (0, 255, 255)

                elif thumb_ratio < 0.45 and was_cocked:
                    was_cocked = False
                    flash_counter = 5
                    status_text = "BANG!"
                    status_color = (0, 0, 255)
                    if gun_sound:
                        gun_sound.play()

                    base_px = (int(lm[5].x * w), int(lm[5].y * h))
                    vx = tip_px[0] - base_px[0]
                    vy = tip_px[1] - base_px[1]
                    mag = math.hypot(vx, vy) or 1
                    speed = 45

                    bullets.append({
                        'x': float(tip_px[0]),
                        'y': float(tip_px[1]),
                        'vx': (vx / mag) * speed,
                        'vy': (vy / mag) * speed,
                        'life': 30
                    })
                else:
                    status_text = "AIMING"
                    status_color = (0, 255, 0)
            else:
                status_text = "HAND DETECTED"
                status_color = (255, 255, 0)

    # -------------------------------------------------------------
    # 3. UPDATE BIRDS
    # -------------------------------------------------------------
    for b in birds[:]:
        b['x'] += b['vx']
        b['y'] += b['vy']

        # Render Bird body & wing accent
        center = (int(b['x']), int(b['y']))
        cv2.circle(frame, center, b['radius'], b['color'], -1)
        cv2.circle(frame, center, b['radius'] // 2, (255, 255, 255), -1)

        # Remove if off-screen
        if b['y'] > h + 40 or b['x'] < -40 or b['x'] > w + 40:
            birds.remove(b)

    # -------------------------------------------------------------
    # 4. UPDATE BULLETS & HIT DETECTION
    # -------------------------------------------------------------
    for bullet in bullets[:]:
        bullet['x'] += bullet['vx']
        bullet['y'] += bullet['vy']
        bullet['life'] -= 1

        bullet_pt = (int(bullet['x']), int(bullet['y']))
        start_pt = bullet_pt
        end_pt = (int(bullet['x'] - bullet['vx'] * 0.7), int(bullet['y'] - bullet['vy'] * 0.7))
        cv2.line(frame, start_pt, end_pt, (0, 140, 255), 4)

        # Check collision with each bird
        bullet_hit = False
        for bird in birds[:]:
            if dist_2d(bullet_pt, (bird['x'], bird['y'])) < bird['radius'] + 10:
                score += 100
                explosions.append({'x': bird['x'], 'y': bird['y'], 'life': 8})
                birds.remove(bird)
                bullet_hit = True
                break

        if bullet_hit or bullet['life'] <= 0 or not (0 <= bullet['x'] <= w and 0 <= bullet['y'] <= h):
            if bullet in bullets:
                bullets.remove(bullet)

    # Render Explosions
    for exp in explosions[:]:
        cv2.circle(frame, (int(exp['x']), int(exp['y'])), 35 - exp['life'] * 3, (0, 165, 255), -1)
        exp['life'] -= 1
        if exp['life'] <= 0:
            explosions.remove(exp)

    # Render Muzzle Flash
    if flash_counter > 0 and detection_result.hand_landmarks:
        lm = detection_result.hand_landmarks[0]
        fx, fy = int(lm[8].x * w), int(lm[8].y * h)
        cv2.circle(frame, (fx, fy), 32, (0, 255, 255), -1)
        cv2.circle(frame, (fx, fy), 16, (255, 255, 255), -1)
        flash_counter -= 1

    # -------------------------------------------------------------
    # 5. OVERLAY HUD (STATUS & SCORE)
    # -------------------------------------------------------------
    cv2.putText(frame, f"STATUS: {status_text}", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, status_color, 2, cv2.LINE_AA)
    
    cv2.putText(frame, f"SCORE: {score}", (w - 220, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2, cv2.LINE_AA)

    cv2.imshow("Finger Gun Detector", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()