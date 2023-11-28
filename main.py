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
CAMERA_INDEX = 1 #0 for iphone and 1 for mac
SCROLL_AMOUNT = 12
GESTURE_COOLDOWN = 0.5
MODEL_PATH = '/Users/adiarora/Downloads/gesture_recognizer.task'

# Global Variables
current_gesture = ""
last_gesture = None
last_gesture_change_time = time.time()
frame_counter = 0
roi_x, roi_y, roi_width, roi_height = 600, 150, 1280, 832

# Sub-rectangle coordinates within the ROI
sub_roi_x, sub_roi_y = roi_x + 100, roi_y + 200  # Adjust as needed
sub_roi_width, sub_roi_height = 1080, 632  # Adjust as needed

# Screen dimensions
screen_width, screen_height = pyautogui.size()


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
        elif current_gesture.startswith("Victory"):
            pyautogui.scroll(-SCROLL_AMOUNT) # Scroll down
        elif current_gesture.startswith("Closed_Fist"):
            pyautogui.click() # Click
        elif current_gesture.startswith("Thumb_Up"):
            pyautogui.hotkey('command', 'option', 'right')  # Next tab in browser
        elif current_gesture.startswith("ILoveYou"):
            pyautogui.hotkey('command', 'option', 'left')  # Previous tab in browser

        last_gesture = current_gesture
        last_gesture_change_time = current_time

@safe_execute
def draw_frame(frame, hand_results, mp_drawing, mp_hands):
    """Draws hand landmarks and gesture names on the frame."""
    if hand_results.multi_hand_landmarks:
        for hand_landmarks in hand_results.multi_hand_landmarks:
            # Adjust the hand landmarks to the ROI coordinates
            for landmark in hand_landmarks.landmark:
                landmark.x = (landmark.x * roi_width / frame.shape[1]) + (roi_x / frame.shape[1])
                landmark.y = (landmark.y * roi_height / frame.shape[0]) + (roi_y / frame.shape[0])
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
    cv2.putText(frame, current_gesture, (roi_x, roi_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 128, 0), 8, cv2.LINE_AA) 

@safe_execute
def process_frame(cap, recognizer, hands, mp_drawing, mp_hands):
    """Processes each frame for gesture recognition and action mapping."""

    global frame_counter

    ret, frame = cap.read()
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        return False

    frame = cv2.flip(frame, 1)
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Draw the ROI on the frame
    cv2.rectangle(frame, (roi_x, roi_y), (roi_x + roi_width, roi_y + roi_height), (255, 0, 0), 2)
    # Draw the sub-rectangle (screen area)
    cv2.rectangle(frame, (sub_roi_x, sub_roi_y), (sub_roi_x + sub_roi_width, sub_roi_y + sub_roi_height), (0, 255, 0), 2)

    # Crop the frame to the ROI for hand detection
    roi_frame = image_rgb[roi_y:roi_y + roi_height, roi_x:roi_x + roi_width]
    hand_results = hands.process(roi_frame)

    if hand_results.multi_hand_landmarks:
        for hand_landmarks in hand_results.multi_hand_landmarks:
            # Assuming the base of the palm is the 0th landmark
            palm_base = hand_landmarks.landmark[0]
            palm_x = int(palm_base.x * roi_width) + roi_x
            palm_y = int(palm_base.y * roi_height) + roi_y

            # Check if the base of the palm is within the sub-rectangle
            if (sub_roi_x <= palm_x <= sub_roi_x + sub_roi_width and
                sub_roi_y <= palm_y <= sub_roi_y + sub_roi_height):
                # Map the position within the sub-rectangle to screen coordinates
                mapped_x = int((palm_x - sub_roi_x) / sub_roi_width * screen_width)
                mapped_y = int((palm_y - sub_roi_y) / sub_roi_height * screen_height)
                # Move the mouse cursor
                pyautogui.moveTo(mapped_x, mapped_y)


    # Draw the hand landmarks and gesture names
    draw_frame(frame, hand_results, mp_drawing, mp_hands)

    # Prepare the cropped frame for gesture recognition
    roi_frame_resized = cv2.resize(roi_frame, (frame.shape[1], frame.shape[0]))
    mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=roi_frame_resized)

    timestamp_ms = int(frame_counter * 1000 / 30)
    frame_counter += 1

    recognizer.recognize_async(mp_frame, timestamp_ms)
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

