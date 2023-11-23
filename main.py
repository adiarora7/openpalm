import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

BaseOptions = mp.tasks.BaseOptions
GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
GestureRecognizerResult = mp.tasks.vision.GestureRecognizerResult
VisionRunningMode = mp.tasks.vision.RunningMode


current_gesture = ""

def print_result(result: GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
    print("Gesture Recognizer Results:", result)

    global current_gesture

    if result.gestures:
        top_gesture = result.gestures[0][0]
        current_gesture = f"{top_gesture.category_name} ({top_gesture.score:.2f})"
    return result


def main():
    global current_gesture

    # Initialize the camera (0 is iPhone camera)
    cap = cv2.VideoCapture(1)

    # Drawing utilities
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands()
    mp_drawing = mp.solutions.drawing_utils

    # Check if the camera opened successfully
    if not cap.isOpened():
        print("Error: Camera could not be opened.")
        return
    
     # Create a gesture recognizer instance with the live stream mode
    options = GestureRecognizerOptions(
        base_options=BaseOptions(model_asset_path='/Users/adiarora/Downloads/gesture_recognizer.task'),
        running_mode=VisionRunningMode.LIVE_STREAM,
        result_callback=print_result)

    frame_counter = 0
    with GestureRecognizer.create_from_options(options) as recognizer:

        try:
            while True:
                # Capture frame-by-frame
                ret, frame = cap.read()

                # If frame is read correctly, ret is True
                if not ret:
                    print("Can't receive frame (stream end?). Exiting ...")
                    break

                # Mirrored display
                frame = cv2.flip(frame, 1)

                # Convert frame for hand tracking
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                hand_results = hands.process(image_rgb)

                # Draw hand landmarks
                if hand_results.multi_hand_landmarks:
                    for hand_landmarks in hand_results.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Convert frame to MediaPipe Image
                mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
                
                # Generate a timestamp based on frame count
                timestamp_ms = int(frame_counter * 1000 / 30 ) # assuming 30 fps
                frame_counter += 1

                # Perform gesture recognition
                recognizer.recognize_async(mp_frame, timestamp_ms)
                
                # Draw the gesture name on the frame
                cv2.putText(frame, current_gesture, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 128, 0), 2, cv2.LINE_AA)

                # Display the resulting frame
                cv2.imshow('Camera Feed', frame)

                # Break the loop when 'q' is pressed
                if cv2.waitKey(1) == ord('q'):
                    break

        finally:
            # When everything is done, release the capture and hands
            cap.release()
            cv2.destroyAllWindows()
            hands.close()



if __name__ == "__main__":
    main()
