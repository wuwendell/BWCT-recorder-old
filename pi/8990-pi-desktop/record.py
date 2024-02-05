from picamera2 import Picamera2
from picamera2.encoders import Quality
import datetime
import time
import RPi.GPIO as GPIO

# Debounce time
debounce_time = 50 # milliseconds

# Video recording length
record_length = 10 * (1000 * 60) # 10 minutes in milliseconds

# Set up GPIO pins
button_pin = 16
led_pin = 26

# Define the directory to save the files to
save_directory = "/media/pi/0123-4567/recordings/"

GPIO.setmode(GPIO.BCM)
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(led_pin, GPIO.OUT)

# Initialize the camera and set the resolution to 1280x720
picam2 = Picamera2()
camera_config = picam2.create_video_configuration(main={"size": (1280, 720)})
picam2.configure(camera_config)

# Start the camera
picam2.start()
print("Camera started, press button to begin recording")

# Function to generate the filename
def get_filename():
    return f"census_tool_{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.mp4"

# Function to get current time in milliseconds
def millis():
    return round(time.time() * 1000)

last_update = millis()
last_state = GPIO.input(button_pin)

# Main loop to handle recording and button press events
recording = False
handled = False
led_state = GPIO.LOW
led_time = millis()
record_time = millis()
while True:
    input_state = GPIO.input(button_pin)
    if input_state != last_state:
        if (millis() - last_update) >= debounce_time:
            last_state = input_state
            last_update = millis()
        else:
            continue
    if input_state == True:
        handled = False
    elif input_state == False and handled == False:
        handled = True
        if recording:
            print("Stopping recording")
            # Stop recording
            picam2.stop_recording()
            recording = False
            # Blink LED quickly
            for _ in range(5):
                GPIO.output(led_pin, GPIO.LOW)
                time.sleep(0.1)
                GPIO.output(led_pin, GPIO.HIGH)
                time.sleep(0.1)
            led_state = GPIO.LOW
            # Print saved file path
            print(f"Saved recording to {filename}")
        else:
            print("Starting recording")
            # Start recording
            filename = save_directory + get_filename()
            picam2.start_and_record_video(output=filename, config=camera_config, quality=Quality.HIGH)
            record_time = millis()
            # Print saved file path
            print(f"Recording to {filename}")
            recording = True
            # Blink LED quickly
            for _ in range(5):
                GPIO.output(led_pin, GPIO.HIGH)
                time.sleep(0.1)
                GPIO.output(led_pin, GPIO.LOW)
                time.sleep(0.1)
            led_state = GPIO.HIGH
        GPIO.output(led_pin, led_state)
    if recording:
        # Slow blink LED
        if (millis() - led_time) >= 1000:
            if led_state == GPIO.HIGH:
                led_state = GPIO.LOW
            else:
                led_state = GPIO.HIGH
            GPIO.output(led_pin, led_state)
            led_time = millis()
        if (millis() - record_time) >= record_length:
            print(f"Recorded for {(millis() - record_time)/(1000*60)} minutes, starting new segment")
            # Stop recording
            picam2.stop_recording()
            filename = save_directory + get_filename()
            # Start recording
            picam2.start_and_record_video(output=filename, config=camera_config, quality=Quality.HIGH)
            record_time = millis()
    else:
        # No recording, no button press
        time.sleep(0.1)

# Clean up GPIO settings when script exits
GPIO.cleanup()
