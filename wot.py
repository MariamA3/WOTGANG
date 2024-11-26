import time
from flask import Flask, jsonify, render_template
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import Servo
import serial
from test import get_sensor_data  # Importing the function from test.py

# Initialize Flask app
app = Flask(__name__)

# Setup for servo
pin_factory = PiGPIOFactory()
servo = Servo(18, pin_factory=pin_factory)

# Initialize variables for servo activation state
servo_activated = False

# For connecting to the micro:bit
microbit_port = '/dev/ttyACM0'
baud_rate = 115200
try:
    ser = serial.Serial(microbit_port, baud_rate, timeout=1)
    print(f"Serial connection established: {ser.is_open}")
except serial.SerialException as e:
    print(f"Serial error: {e}")
    ser = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/sensor-data", methods=["GET"])
def sensor_data():
    global servo_activated
    data = get_sensor_data()  # Fetch temperature and humidity data

    if data:
        temperature = data["temperature_c"]
        humidity = data["humidity"]

        # Check if humidity is lower than 50% and activate the servo and motor if not already activated
        if humidity < 50 and not servo_activated:
            # Activate servo
            print("Activating servo...")
            servo.mid()  # Move servo to 90°
            time.sleep(1)
            servo.max()  # Move servo to 180°

            # Send command to micro:bit for motor
            if ser:
                print("Sending TOGGLE command to micro:bit for motor.")
                ser.write("TOGGLE\n".encode("utf-8"))
                ser.flush()
                print("TOGGLE command sent!")

            # Set activation flag
            servo_activated = True

        # Reset the activation flag if humidity goes above 50%
        elif humidity >= 50:
            print("Deactivating servo...")
            servo.min()  # Move servo to 0°

            # No need to explicitly deactivate the motor in this example,
            # as micro:bit handles the motor logic upon receiving commands.

            servo_activated = False

        return jsonify({
            "temperature": temperature,
            "humidity": humidity,
            "servo_activated": servo_activated
        })
    else:
        return jsonify({
            "error": "Failed to read sensor data"
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
