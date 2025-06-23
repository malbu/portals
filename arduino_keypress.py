"""
Sends keypress from arudino to a keyboard press 
Note, will need pyautogui installed 
"""

import serial
import pyautogui
import time

# Replace with your Arduino's port (the one we found earlier)
ARDUINO_PORT = '/dev/cu.usbmodem11301'
BAUD_RATE = 9600

try:
    # Connect to Arduino
    arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE)
    time.sleep(2)  # Wait for Arduino to initialize
    print("Connected to Arduino. Waiting for button presses...")
    
    while True:
        if arduino.in_waiting > 0:
            line = arduino.readline().decode('utf-8').strip()
            print(f"Received: {line}")
            
            if line == "BUTTON2_RELEASED":
                pyautogui.press('0')
                print("Sent '0' keypress to computer")
            if line == "BUTTON3_RELEASED":
                pyautogui.press('1')
                print("Sent '1' keypress to computer")
                
except KeyboardInterrupt:
    print("\nStopping...")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'arduino' in locals():
        arduino.close()
    print("Serial connection closed")