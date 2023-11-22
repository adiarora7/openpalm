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

def print_result(result: GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
    print('Gesture recognition result:', result)



def main():
    # Initialize the camera (0 is the default camera)
    cap = cv2.VideoCapture(1)

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

                # Convert frame to MediaPipe Image
                mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
                
                # Generate a timestamp based on frame count
                timestamp_ms = int(frame_counter * 1000 / 30 ) # assuming 30 fps
                frame_counter += 1

                # Perform gesture recognition
                recognizer.recognize_async(mp_frame, timestamp_ms)

                # Display the resulting frame
                cv2.imshow('Camera Feed', frame)

                # Break the loop when 'q' is pressed
                if cv2.waitKey(1) == ord('q'):
                    break
        finally:
            # When everything is done, release the capture
            cap.release()
            cv2.destroyAllWindows()



if __name__ == "__main__":
    main()