import cv2
import mediapipe as mp
import numpy as np
import math
import time
import random
import base64
import requests

# ==== Embedded Background (small pixel art scaled up) ====
retro_bg_base64 = """
iVBORw0KGgoAAAANSUhEUgAAAKAAAABgCAIAAABsb7+9AAAAAXNSR0IArs4c6QAAAAlwSFlzAAAO
xAAADsQBlSsOGwAAABl0RVh0Q3JlYXRpb24gVGltZQAwOC8wOS8yNX5NG+oAAACuSURBVHja7dIx
DoAwDAZQ//9fC7gpG5QBApRY7T3oQJtVZ4mwo8e3r29w5F3QdAlJ2RY4Dfc8ShEQcEYB2iGj0UPj
lpEtuSEyoIlxh8uoHOrKhGiJNErS+iV1bdpPZveJ1n2E5/J0Mzn5bCPL7Y6U13WJ43Ue/Wkfn05S
1nXtvhe0Y84I0Z5D3vZJ5DLeDNGeQ97PWeS43gDRnkPe91nkuN4A0Z5D3udZ5LjeANGeQ973WeS4
3gARlSjbGDrnKi0AAAAASUVORK5CYII=
"""
retro_bg_data = base64.b64decode(retro_bg_base64)
retro_bg_array = np.frombuffer(retro_bg_data, dtype=np.uint8)
retro_bg_img = cv2.imdecode(retro_bg_array, cv2.IMREAD_COLOR)

# Check if the background image was loaded successfully
if retro_bg_img is None:
    print("Warning: Failed to load background image, creating a fallback")
    # Create a simple fallback background without borders
    retro_bg_img = np.zeros((720, 1280, 3), dtype=np.uint8)
    # Add some game over style elements without frames
    cv2.putText(retro_bg_img, "GAME OVER", (500, 200), cv2.FONT_HERSHEY_DUPLEX, 2, (0, 255, 255), 3)
else:
    print("Background image loaded successfully")

# === Mediapipe setup (more accurate) ===
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# Track last few frames for stability
finger_up_history = []

# === Game constants ===
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 900
cv2.namedWindow("Finger Controlled Reverse Snake", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Finger Controlled Reverse Snake", WINDOW_WIDTH, WINDOW_HEIGHT)

BASE_GRID_SIZE = min(WINDOW_WIDTH, WINDOW_HEIGHT) // 40
GRID_SIZE = BASE_GRID_SIZE
WINDOW_COLS = WINDOW_WIDTH // GRID_SIZE
WINDOW_ROWS = WINDOW_HEIGHT // GRID_SIZE
FONT_SCALE = min(WINDOW_WIDTH, WINDOW_HEIGHT) / 1000
UI_PADDING = int(min(WINDOW_WIDTH, WINDOW_HEIGHT) * 0.05)

obstacles = []
moving_obstacles = False
target_blink = False
OBSTACLE_SIZE = GRID_SIZE

level = 1
target_blink_state = True
target_blink_timer = 0

def random_target():
    return {"x": random.randint(0, WINDOW_COLS - 1), "y": random.randint(0, WINDOW_ROWS - 1)}

def generate_obstacles(num):
    obs = []
    for _ in range(num):
        obs.append({"x": random.randint(0, WINDOW_COLS - 1), "y": random.randint(0, WINDOW_ROWS - 1)})
    return obs

def update_level_settings():
    global snake_speed, obstacles, moving_obstacles, target_blink, target_size, level
    
    print(f"Level change detected!")
    print(f"Current score: {score}")
    print(f"New level: {level}")
    print(f"Snake speed: {snake_speed}")
    
    if level == 1:
        snake_speed = 0.3
        obstacles = []
        moving_obstacles = False
        target_blink = False
        target_size = GRID_SIZE
    elif level == 2:
        snake_speed = 0.25
        obstacles = generate_obstacles(3)
        moving_obstacles = False
        target_blink = False
        target_size = GRID_SIZE + 4
    elif level == 3:
        snake_speed = 0.20
        obstacles = generate_obstacles(5)
        moving_obstacles = True
        target_blink = False
        target_size = GRID_SIZE + 8
    elif level == 4:
        snake_speed = 0.15
        obstacles = generate_obstacles(8)
        moving_obstacles = False
        target_blink = True
        target_size = GRID_SIZE + 12
    elif level == 5:
        snake_speed = 0.12
        obstacles = generate_obstacles(10)
        moving_obstacles = True
        target_blink = True
        target_size = GRID_SIZE + 16



def pixel_to_grid(px, py, frame_width, frame_height):
    gx = min(max(int(px / frame_width * WINDOW_COLS), 0), WINDOW_COLS - 1)
    gy = min(max(int(py / frame_height * WINDOW_ROWS), 0), WINDOW_ROWS - 1)
    return {"x": gx, "y": gy}

def fingers_up(hand_landmarks):
    finger_states = []
    tips = [4, 8, 12, 16, 20]
    for tip in tips:
        finger_states.append(
            hand_landmarks.landmark[tip].y <
            hand_landmarks.landmark[tip - 2].y
        )
    return finger_states

def move_snake():
    global snake, growth_pending
    head = snake[0].copy()
    dx = target["x"] - head["x"]
    dy = target["y"] - head["y"]

    dist = math.sqrt(dx * dx + dy * dy)
    if dist > MIN_GAP:
        if dx > 0: head["x"] += 1
        elif dx < 0: head["x"] -= 1
        if dy > 0: head["y"] += 1
        elif dy < 0: head["y"] -= 1
    else:
        return False

    if head in snake:
        return False
    if head in obstacles:
        return False

    snake.insert(0, head)

    if growth_pending > 0:
        growth_pending -= 1
    else:
        if len(snake) > snake_length:
            snake.pop()

    return True

def draw_game_on_camera(frame):
    # Draw snake segments as red circles
    for s in snake:
        center = (
            int(s["x"] * GRID_SIZE + GRID_SIZE//2), 
            int(s["y"] * GRID_SIZE + GRID_SIZE//2)
        )
        radius = int(GRID_SIZE/2) - 2
        cv2.circle(frame, center, radius, (0, 0, 255), -1)

    # Draw obstacles as blue circles
    for obs in obstacles:
        center = (
            int(obs["x"] * GRID_SIZE + GRID_SIZE//2),
            int(obs["y"] * GRID_SIZE + GRID_SIZE//2)
        )
        radius = int(OBSTACLE_SIZE/2) - 2
        cv2.circle(frame, center, radius, (255, 0, 0), -1)

    # Score display
    cv2.putText(frame, f"Score: {score}  Level: {level}", (50, 350),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 5)



def check_finger_obstacle_collision(finger_pos):
    for obs in obstacles:
        if obs["x"] == finger_pos["x"] and obs["y"] == finger_pos["y"]:
            return True
    return False

def reset_game_state():
    global snake, snake_length, growth_pending, score, target, snake_speed
    global last_move_time, last_growth_time, game_started, countdown_done
    global countdown_start_time, game_over, game_over_time, level
    global obstacles, moving_obstacles, target_blink, target_size, face_captured, roast_index
    
    snake = [{"x": 5, "y": 5}]
    snake_length = 3
    growth_pending = 0
    score = 0
    level = 1
    target = {"x": 15, "y": 10}
    snake_speed = 0.3
    last_move_time = time.time()
    last_growth_time = time.time()
    game_started = False
    countdown_done = False
    countdown_start_time = None
    game_over = False
    game_over_time = None
    face_captured = False
    roast_index = 0  # Reset roast index for new game
    update_level_settings()

reset_game_state()

MIN_GAP = 3
min_speed = 0.07
speed_decrement = 0.005
growth_interval = 2

def get_camera_index():
    for i in range(5):
        test_cap = cv2.VideoCapture(i)
        if test_cap.isOpened():
            test_cap.release()
            return i
    return -1

def capture_face_fullres():
    cap = cv2.VideoCapture(0)
    cap.set(3, 1920)
    cap.set(4, 1080)
    ret, frame = cap.read()
    cap.release()
    return frame if ret else None

def apply_funny_filter(img):
    h, w = img.shape[:2]
    # Create a simple color distortion effect without duplicating the image
    distorted = img.copy()
    
    # Add some color distortion by adjusting brightness and contrast
    distorted = cv2.convertScaleAbs(distorted, alpha=1.2, beta=30)
    
    # Add a subtle blur effect
    distorted = cv2.GaussianBlur(distorted, (5, 5), 0)
    
    return distorted

def get_roast(score):
    # List of 20 different roasts that cycle through
    roasts = [
        "Wow, {score} points? My grandma could do better with her eyes closed!",
        "Is {score} your high score or your IQ? Asking for a friend...",
        "With {score} points, you're not just bad at this game, you're bad at life!",
        "Did you let a toddler play? Because {score} points is toddler-level performance!",
        "Congratulations! You've achieved the impossible: making {score} points look pathetic!",
        "Breaking news: Local player discovers new low with {score} points!",
        "Your snake moves like you're trying to text and drive at the same time!",
        "At {score} points, you're not playing the game, the game is playing you!",
        "I've seen better snake control from someone having a seizure!",
        "With {score} points, you're basically a walking tutorial!",
        "Your gaming skills are like a broken calculator - always giving the wrong answer!",
        "At this rate, you'll reach 100 points by the time you're 100 years old!",
        "Your snake has better dance moves than you do!",
        "I've seen more coordination in a drunk penguin on ice!",
        "Your score of {score} is like a participation trophy - everyone gets one!",
        "You're not just bad at this game, you're making bad look good!",
        "Your snake moves like it's trying to solve a Rubik's cube blindfolded!",
        "At {score} points, you're basically a walking advertisement for what NOT to do!",
        "Your gaming skills are like a broken clock - wrong twice a day!",
        "Congratulations on achieving the impossible: making {score} points look impressive... to a goldfish!"
    ]
    
    # Use a global variable to track which roast to use
    global roast_index
    if 'roast_index' not in globals():
        roast_index = 0
    
    # Get the current roast and cycle to the next one
    current_roast = roasts[roast_index % len(roasts)]
    roast_index += 1
    
    # Format the roast with the actual score
    formatted_roast = current_roast.format(score=score)
    

        # If OpenAI fails, just return the pre-written roast
    return formatted_roast

def show_gameover_screen(score, face_img, roast_text):
    print("🎨 Creating game over screen...")
    
    bg = cv2.resize(retro_bg_img, (1280, 720))
    # Make the face image much bigger - increased from 320x240 to 480x360
    face_big = cv2.resize(face_img, (480, 360))
    # Position the bigger face image more prominently on the left side
    bg[50:410, 50:530] = face_big
    # Move score text to the right side to accommodate bigger face image
    cv2.putText(bg, f"SCORE: {score}", (580, 150), cv2.FONT_HERSHEY_DUPLEX, 2, (0, 255, 255), 3)
    # Position roast text below score, also on the right side
    cv2.putText(bg, roast_text, (580, 250), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 2)
    print("🖼 Displaying game over window...")
    cv2.imshow("GAME OVER", bg)
    
    # 🎵 Play dramatic game over sound 🎵
    try:
        import winsound
        winsound.Beep(800, 1000)  # Lower pitch, longer duration for dramatic effect
        print("🔊 Audio played successfully!")
    except ImportError:
        print("⚠ winsound not available on this system")
    
    print("⏳ Waiting for 3 seconds...")
    cv2.waitKey(3000)  # Wait 3 seconds
    print("🔒 Closing game over window...")
    cv2.destroyWindow("GAME OVER")  # Close the game over window

camera_index = get_camera_index()
if camera_index == -1:
    print("❌ No camera found! Please connect a webcam.")
    exit()

cap = cv2.VideoCapture(camera_index)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WINDOW_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WINDOW_HEIGHT)

if not cap.isOpened():
    print("❌ Failed to open camera.")
    exit()

running = True
corner_length = 50
corner_color = (255, 255, 255)
corner_thickness = 5

while running:
    ret, webcam_frame = cap.read()
    if not ret:
        print("⚠ Frame not captured.")
        break

    webcam_frame = cv2.resize(webcam_frame, (WINDOW_WIDTH, WINDOW_HEIGHT))
    webcam_frame = cv2.flip(webcam_frame, 1)
    rgb = cv2.cvtColor(webcam_frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if not game_started:
        cv2.putText(webcam_frame, "Press 'S' to Start", (50, 300),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 5)
        cv2.putText(webcam_frame, "Press 'Q' to Quit", (50, 400),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 3)
        cv2.imshow("Finger Controlled Reverse Snake", webcam_frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            game_started = True
            countdown_start_time = time.time()
        elif key == ord('q') or key == 27:
            break
        continue

    # Modify the countdown section to center the numbers
    if not countdown_done:
        elapsed = int(time.time() - countdown_start_time)
        countdown_value = 3 - elapsed
        if countdown_value > 0:
            text = str(countdown_value)
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 6.0, 8)[0]
            text_x = (WINDOW_WIDTH - text_size[0]) // 2
            text_y = (WINDOW_HEIGHT + text_size[1]) // 2
            cv2.putText(webcam_frame, text, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 6.0, (255, 255, 255), 8)
        else:
            countdown_done = True
            last_move_time = time.time()
            last_growth_time = time.time()
        cv2.imshow("Finger Controlled Reverse Snake", webcam_frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        continue

    if game_over:
        # Only print game over message once
        if not face_captured:
            print(f"🎮 GAME OVER! Score: {score}, Level: {level}")
            print("📸 Capturing face and getting roast...")
            face_captured = True
            
            # Capture face and get roast
            face_img = capture_face_fullres()
            if face_img is not None:
                print("😄 Applying funny filter...")
                funny_face = apply_funny_filter(face_img)
                print("🔥 Getting roast from AI...")
                roast = get_roast(score)
                print(f"💬 Roast: {roast}")
                print("🖼 Showing game over screen...")
                show_gameover_screen(score, funny_face, roast)
            else:
                print("❌ Failed to capture face")
        
        # Always show the game over screen on the main window
        cv2.putText(webcam_frame, "GAME OVER", (50, 250),
                    cv2.FONT_HERSHEY_SIMPLEX, 2.5, (0, 0, 0), 8)
        cv2.putText(webcam_frame, f"Final Score: {score}  Level: {level}", (50, 350),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 5)
        cv2.putText(webcam_frame, "Press 'R' to Restart", (50, 450),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 5)
        cv2.putText(webcam_frame, "Press 'Q' to Quit", (50, 550),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 5)
        cv2.imshow("Finger Controlled Reverse Snake", webcam_frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('r'):
            reset_game_state()
            game_started = True
            countdown_start_time = time.time()
        elif key == ord('q') or key == 27:
            break
        continue

    finger_detected = False
    # Modify the finger detection section in the main loop to draw hollow circle
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(webcam_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            thumb_up, index_up, middle_up, ring_up, pinky_up = fingers_up(hand_landmarks)
            index_finger_tip = hand_landmarks.landmark[8]
            px, py = int(index_finger_tip.x * WINDOW_WIDTH), int(index_finger_tip.y * WINDOW_HEIGHT)

            if not index_up:
                cv2.putText(webcam_frame, "✋ Show index finger properly", (50, 250),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 4)
            else:
                finger_detected = True
                finger_grid_pos = pixel_to_grid(px, py, WINDOW_WIDTH, WINDOW_HEIGHT)
                if check_finger_obstacle_collision(finger_grid_pos):
                    game_over = True
                    game_over_time = time.time()
                else:
                    target = finger_grid_pos
                    # Draw hollow green circle at finger position
                    cv2.circle(webcam_frame, (px, py), int(GRID_SIZE/2), (0, 255, 0), 2)

    if time.time() - last_move_time > snake_speed:
        if not move_snake():
            game_over = True
            game_over_time = time.time()
        last_move_time = time.time()

    head = snake[0]
    if head["x"] == target["x"] and head["y"] == target["y"]:
        growth_pending += 1
        score += 1
        if score >= 25:
            level = 5
        elif score >= 20:
            level = 4
        elif score >= 15:
            level = 3
        elif score >= 10:
            level = 2
        update_level_settings()
        while True:
            new_target = random_target()
            if all(segment["x"] != new_target["x"] or segment["y"] != new_target["y"] for segment in snake):
                target = new_target
                break
        snake_speed = max(min_speed, snake_speed - speed_decrement)

    if time.time() - last_growth_time > growth_interval:
        growth_pending += 1
        score += 1
        last_growth_time = time.time()
        if score >= 25:
            level = 5
            update_level_settings()
        elif score >= 20:
            level = 4
            update_level_settings()
        elif score >= 15:
            level = 3
            update_level_settings()
        elif score >= 10:
            level = 2
            update_level_settings()

    draw_game_on_camera(webcam_frame)
    cv2.putText(webcam_frame, "Press 'Q' to Quit", (50, 400),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 3)

    cv2.imshow("Finger Controlled Reverse Snake", webcam_frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:
        break
    elif key == ord('r'):
        reset_game_state()
        game_started = True
        countdown_start_time = time.time()

cap.release()
cv2.destroyAllWindows()