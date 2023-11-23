import cv2
import mediapipe as mp
import pyautogui 
import time

# Shorthand Naming
BaseOptions = mp.tasks.BaseOptions
GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
GestureRecognizerResult = mp.tasks.vision.GestureRecognizerResult
VisionRunningMode = mp.tasks.vision.RunningMode

# Configurable Parameters
CAMERA_INDEX = 1
SCROLL_AMOUNT = 12
GESTURE_COOLDOWN = 0.5
MODEL_PATH = '/Users/adiarora/Downloads/gesture_recognizer.task'

# Global Variables
current_gesture = ""
last_gesture = None
last_gesture_change_time = time.time()


def safe_execute(func):
    """Decorator for safe execution with exception handling."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error occurred: {e}")
    return wrapper


@safe_execute
def setup_camera():
    """Initializes and returns the camera object."""
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("Error: Camera could not be opened.")
        return None
    return cap


@safe_execute
def print_result(result: GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
    """Processes and prints gesture recognition results."""
    global current_gesture

    print("Gesture Recognizer Results:", result)

    if result.gestures:
        top_gesture = result.gestures[0][0]
        current_gesture = f"{top_gesture.category_name} ({top_gesture.score:.2f})"
    return result


@safe_execute
def map_gesture_to_action():
    """Maps recognized gestures to corresponding actions."""
    global last_gesture, last_gesture_change_time

    current_time = time.time()
    if current_gesture != last_gesture and (current_time - last_gesture_change_time) > GESTURE_COOLDOWN:
        if current_gesture.startswith("Pointing_Up"):
            pyautogui.scroll(SCROLL_AMOUNT)  # Scroll up
        elif current_gesture.startswith("Closed_Fist"):
            pyautogui.scroll(-SCROLL_AMOUNT)  # Scroll down        

        last_gesture = current_gesture
        last_gesture_change_time = current_time


@safe_execute
def draw_frame(frame, hand_results, mp_drawing, mp_hands):
    """Draws hand landmarks and gesture names on the frame."""
    if hand_results.multi_hand_landmarks:
        for hand_landmarks in hand_results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
    cv2.putText(frame, current_gesture, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 128, 0), 2, cv2.LINE_AA) 


@safe_execute
def process_frame(cap, recognizer, hands, mp_drawing, mp_hands):
    """Processes each frame for gesture recognition and action mapping."""
    ret, frame = cap.read()
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        return False

    frame = cv2.flip(frame, 1) 
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    hand_results = hands.process(image_rgb)
    draw_frame(frame, hand_results, mp_drawing, mp_hands)

    mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
    recognizer.recognize_async(mp_frame, int(time.time() * 1000))
    map_gesture_to_action()

    cv2.imshow('Camera Feed', frame) 
    return True


@safe_execute
def cleanup_resources(cap, hands):
    """Releases camera and MediaPipe resources."""
    cap.release()
    cv2.destroyAllWindows()
    hands.close()


def main():
    cap = setup_camera()
    if cap is None:
        return

    #Drawing utilities
    hands = mp.solutions.hands.Hands()
    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands

    # Create a gesture recognizer instance with the live stream mode
    options = GestureRecognizerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=VisionRunningMode.LIVE_STREAM,
        result_callback=print_result)

    with GestureRecognizer.create_from_options(options) as recognizer:
        while True:
            if not process_frame(cap, recognizer, hands, mp_drawing, mp_hands):
                break
            if cv2.waitKey(1) == ord('q'): #break loop when q is pressed
                break

    cleanup_resources(cap, hands)

if __name__ == "__main__":
    main()


