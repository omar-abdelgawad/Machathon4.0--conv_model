# importing pygame module
import pygame
import pigpio
from pygame.locals import *
import cv2
import numpy as np
import time

PinFR = 3     #Front Right Motor
PinFL = 15    #Front Left Motor  
PinBR = 27    #Back Right Motor
PinBL = 10    #Back Left Motor

vc = 1700
sc = 300

pwm = pigpio.pi()

centroid_x = 0
centroid_y = 0

def invert(x):
    return 3000 - x

def forward(steering_angle):
    s_left_ = vc + steering_angle * sc
    s_right_ = vc - steering_angle * sc
    
    s_left = s_left_
    s_right = invert(s_right_)
    
    pwm.set_servo_pulsewidth(PinFR, s_right) #anti-clockwise
    pwm.set_servo_pulsewidth(PinFL, s_left) #clockwise
    pwm.set_servo_pulsewidth(PinBR, s_right) #anti-clockwise
    pwm.set_servo_pulsewidth(PinBL, s_left) #clockwise

def stop():
    pwm.set_servo_pulsewidth(PinFR, 0) #anti-clockwise
    pwm.set_servo_pulsewidth(PinFL, 0) #clockwise
    pwm.set_servo_pulsewidth(PinBR, 0) #anti-clockwise
    pwm.set_servo_pulsewidth(PinBL, 0) #clockwise

def analyze(original_image):
    global centroid_x , centroid_y
    blurred_image = cv2.GaussianBlur(original_image, (15, 15), cv2.BORDER_DEFAULT)
    hsv_image = cv2.cvtColor(blurred_image, cv2.COLOR_BGR2HSV)
    
    # Define lower and upper bounds for the red color in HSV
    lower_red1 = np.array([0, 75, 20])
    upper_red1 = np.array([10, 255, 255])

    lower_red2 = np.array([160, 75, 20])
    upper_red2 = np.array([180, 255, 255])

    # Create masks to detect the red color in both specified ranges
    lower_mask = cv2.inRange(hsv_image, lower_red1, upper_red1)
    upper_mask = cv2.inRange(hsv_image, lower_red2, upper_red2)

    # Combine the lower and upper masks to get a single mask
    combined_mask = lower_mask + upper_mask

    # Calculate the moments of the combined mask to find the centroid
    moments = cv2.moments(combined_mask)

    # Check if moments['m00'] is not zero before computing centroid
    if moments['m00'] != 0:
        centroid_x = int(moments['m10'] / moments['m00'])
        centroid_y = int(moments['m01'] / moments['m00'])

        print(f"Centroid Y-coordinate is {centroid_y}")
        print(f"Centroid X-coordinate is {centroid_x}")

        # Draw an arrow from the center to the centroid
        cv2.arrowedLine(original_image, (int(original_image.shape[1]/2), int(original_image.shape[0])), (centroid_x, centroid_y), (255, 0, 0), 2, tipLength=0.5)

    steering = (centroid_x - (hsv_image.shape[1]/2)) / (hsv_image.shape[1]/2)

    # Wait for a key press and close the window
    return original_image , steering

# Open the default camera (usually the built-in webcam)

steering = 0
cap = cv2.VideoCapture(0)
time_0 = time.time()

# Check if the camera is opened successfully
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Infinite loop to continuously capture frames from the camera
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    # Check if the frame is read successfully
    if not ret:
        print("Error: Couldn't read frame.")
        break

    # Display the frame
    frame , steering = analyze(frame)
    
    cv2.imshow('Camera', frame)
    
    if (time.time() - time_0) % 0.6 > 0.3:
        forward(steering)
    else:
        stop()
    # Break the loop if the user presses the 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        stop()
        break

# Release the camera and close the OpenCV window
cap.release()
cv2.destroyAllWindows()
