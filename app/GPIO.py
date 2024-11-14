from platform_check import is_raspberry_pi

if is_raspberry_pi():
    try:
        from RPi import GPIO as real_GPIO

        # If successful, map all functions to real_GPIO
        setmode = real_GPIO.setmode
        setup = real_GPIO.setup
        output = real_GPIO.output
        input = real_GPIO.input

        # Constants
        OUT = real_GPIO.OUT
        IN = real_GPIO.IN
        BCM = real_GPIO.BCM
        BOARD = real_GPIO.BOARD

    except ImportError:
        # Fallback to mock implementation if RPi.GPIO is not available
        print("RPi.GPIO not available; using mock implementation")
        real_GPIO = None
else:
    real_GPIO = None

# Mock implementations if not on Linux or RPi.GPIO import fails
if real_GPIO is None:
    OUT = "OUT"
    IN = "IN"
    BCM = "BCM"
    BOARD = "BOARD"
    LOW = False
    HIGH = True

    def setmode(mode):
        print(f"Mock set mode {mode}")

    def setup(pin, mode):
        print(f"Mock setup on pin {pin} with mode {mode}")

    def output(pin, state):
        print(f"Mock output to pin {pin} with state {state}")

    def input(pin):
        print(f"Mock input from pin {pin}")
        return False