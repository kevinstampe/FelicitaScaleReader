import asyncio
from bleak import BleakClient
from RpiGPIO import GPIO
from const import (
    DATA_CHARACTERISTIC_UUID, 
    CMD_START_TIMER, 
    CMD_STOP_TIMER,
    CMD_RESET_TIMER,
    CMD_TARE,
    CMD_WEIGHT_AND_TIMER_MODE,
    MIN_BATTERY_LEVEL,
    MAX_BATTERY_LEVEL
)

waiting_for_shot_button_off = False

is_connected = False
is_shot_running = False

last_battery_level_raw = 0
last_printed_message = ""

current_weight = 0
current_battery_level = 0

weight_stop_offset = 1.2 # how many grammes to stop before the target weight
expected_shot_weight = 40
current_scale_unit = "g"

def disconnect_callback(client):
    print("Disconnected from the scale")
    global is_connected
    is_connected = False

# runs every notification indefinitely
def parse_status_update(felicita_raw_status):
    if len(felicita_raw_status) != 18:
        print("Malformed data")
        return

    weight_bytes = felicita_raw_status[3:9]
    weight = "".join([str(b - 48) for b in weight_bytes])
    scale_unit = bytes(felicita_raw_status[9:11]).decode("utf-8")
    battery_level = felicita_raw_status[15]


    global last_battery_level_raw

    if abs(last_battery_level_raw - battery_level) < 2:
        battery_level = last_battery_level_raw
    else:
        last_battery_level_raw = battery_level

    battery_percentage = ((battery_level - MIN_BATTERY_LEVEL) / (MAX_BATTERY_LEVEL - MIN_BATTERY_LEVEL)) * 100
    if battery_percentage > 100:
        battery_percentage = 100
    elif battery_percentage < 0:
        battery_percentage = 0

    global current_weight
    global current_battery_level
    global current_scale_unit

    isNegativeNumber = felicita_raw_status[2] == 45 and weight != "000000"
    current_weight = -int(weight) / 100 if isNegativeNumber else int(weight) / 100
    current_battery_level = battery_percentage
    current_scale_unit = scale_unit

async def notification_handler(sender, data):
    parse_status_update(bytearray(data))

async def shotStopper(client):
    global is_shot_running
    try:
        # Send initial commands
        await client.write_gatt_char(DATA_CHARACTERISTIC_UUID, bytearray([CMD_WEIGHT_AND_TIMER_MODE]))
        await asyncio.sleep(0.1)
        await client.write_gatt_char(DATA_CHARACTERISTIC_UUID, bytearray([CMD_STOP_TIMER]))
        await asyncio.sleep(0.1)
        await client.write_gatt_char(DATA_CHARACTERISTIC_UUID, bytearray([CMD_RESET_TIMER]))
        await asyncio.sleep(0.1)
        await client.write_gatt_char(DATA_CHARACTERISTIC_UUID, bytearray([CMD_TARE]))
        await asyncio.sleep(0.1)
        await client.write_gatt_char(DATA_CHARACTERISTIC_UUID, bytearray([CMD_START_TIMER]))
        setRelay(True)
        print("Tare and start timer commands sent")

        # Loop to monitor weight and button state
        while current_weight < (expected_shot_weight - weight_stop_offset):
            await asyncio.sleep(0.1)
            readShotButton()  # Check button state
            print_scale_data()

            # Stop immediately if button is turned off
            if not is_shot_running:
                print("Shot stopped due to button being turned off")
                await client.write_gatt_char(DATA_CHARACTERISTIC_UUID, bytearray([CMD_STOP_TIMER]))
                setRelay(False)
                return  # Exit the function

        # Stop shot when target weight is reached
        await client.write_gatt_char(DATA_CHARACTERISTIC_UUID, bytearray([CMD_STOP_TIMER]))
        print("Stop timer command sent due to reaching target weight")
        setShotButtonOff()
        setRelay(False)

    except Exception as e:
        print(f"Error: {e}")

def readShotButton():
    global is_shot_running
    global waiting_for_shot_button_off
    state = GPIO.input(2)

    if waiting_for_shot_button_off:
        # Wait for the button to be released (HIGH)
        if state == GPIO.HIGH:
            waiting_for_shot_button_off = False  # Reset flag when button is released
            is_shot_running = False  # Reset shot state after button is toggled off
    else:
        # Set shot running if button is pressed (LOW) and no pending reset
        if state == GPIO.LOW and not is_shot_running:
            is_shot_running = True
        elif state == GPIO.HIGH and is_shot_running:
            # Mark waiting_for_shot_button_off when shot is stopped
            waiting_for_shot_button_off = True

def setShotButtonOff():
    global is_shot_running
    global waiting_for_shot_button_off
    is_shot_running = False
    waiting_for_shot_button_off = True

def setRelay(input):
    GPIO.output(3, input)
    GPIO.output(4, input)

async def connect_to_scale(address):
    client = BleakClient(address, disconnect_callback, timeout=1.0)
    try:
        await client.connect()
        await client.start_notify(DATA_CHARACTERISTIC_UUID, notification_handler)
        print("Notifications enabled")
        
        await asyncio.sleep(0.1) 
        
        return client
    except Exception as e:
        print(f"Error: {e}")
        await client.disconnect()
        return None

def print_scale_data():
    global last_printed_message
    message = f"Weight: {current_weight}{current_scale_unit}, Battery Level: {current_battery_level:.2f}%, Shot Running: {is_shot_running}, is waiting for shotbutton off: {waiting_for_shot_button_off}"
    if message != last_printed_message:
        last_printed_message = message
        print(message)



async def monitor_scale(client):
    global is_shot_running, is_connected

    while is_connected:
        readShotButton()
        print_scale_data()

        # Start shot stopper if shot has just started
        if is_shot_running:
            await shotStopper(client)
        await asyncio.sleep(0.1)

async def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(2, GPIO.IN)
    GPIO.setup(3, GPIO.OUT)
    GPIO.setup(4, GPIO.OUT)

    with open("mac_addresses.txt", "r") as f:
        address = f.readline().strip()

    global is_connected
    client = None  # Initialize client outside the loop to persist between retries

    while True:
        if not is_connected:
            # Attempt to connect to the scale
            try:
                client = await connect_to_scale(address)
                if client:
                    is_connected = True
                    print("Connected to scale")
                    await monitor_scale(client)  # Begin monitoring the scale
            except asyncio.TimeoutError:
                print("Connection attempt timed out; switching to relay control via button")
            except Exception as e:
                print(f"Error connecting to scale: {e}")

        # Relay control based on button if not connected
        while not is_connected:
            button_state = GPIO.input(2)
            
            # Activate relay if button is pressed (LOW)
            if button_state == GPIO.LOW:
                setRelay(True)
            else:
                # Turn off relay instantly if button is released
                setRelay(False)
                print("Button released, retrying connection to scale")
                break  # Exit to retry connection
            
            await asyncio.sleep(0.1)  # Small delay
            is_connected = False

        await asyncio.sleep(0.1)  # Delay to reduce loop intensity

# Run the main function
asyncio.run(main())

