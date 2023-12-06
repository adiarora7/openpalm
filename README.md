# 👋 Open Palm
Open Palm translates hand gestures into computer commands allowing for a touchless user interface.

![Demo of using your hands to move and click]()*Mouse movement & click*

## How it works
![Logic]()

1. Webcam (or iPhone camera through continuity camera!) is used for input.
2. Each frame is then processed and checked for 
    - hand presence
    - handedness (left or right)
    - position (for mouse movement)
    - gesture recognition
3. The recognized gestures are then mapped to certain computer commands.(click, scroll, etc.)

Libraries used: OpenCV, MediaPipe and PyAutoGui  

