import asyncio
from bleak import BleakClient
from RPi import GPIO
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
    try:
        # one-time commands here:
        await client.write_gatt_char(DATA_CHARACTERISTIC_UUID, bytearray([CMD_WEIGHT_AND_TIMER_MODE]))
        await asyncio.sleep(0.1)
        await client.write_gatt_char(DATA_CHARACTERISTIC_UUID, bytearray([CMD_STOP_TIMER]))
        await asyncio.sleep(0.1)
        await client.write_gatt_char(DATA_CHARACTERISTIC_UUID, bytearray([CMD_RESET_TIMER]))
        await asyncio.sleep(0.1)
        await client.write_gatt_char(DATA_CHARACTERISTIC_UUID, bytearray([CMD_TARE]))
        await asyncio.sleep(0.1)
        await client.write_gatt_char(DATA_CHARACTERISTIC_UUID, bytearray([CMD_START_TIMER]))
        setRelay("True")
        print("Tare and start timer commands sent")

        global expected_shot_weight

        global is_shot_running
        # Keep connection open
        while current_weight < (expected_shot_weight - weight_stop_offset) and is_shot_running:
            await asyncio.sleep(0.1)
            simulateShotButton()
            print_scale_data()

        await client.write_gatt_char(DATA_CHARACTERISTIC_UUID, bytearray([CMD_STOP_TIMER]))

        print("Stop timer command sent")
        simulateShotButtonOff()
        setRelay("False")

    except Exception as e:
        print(f"Error: {e}")

def simulateShotButton():
    global is_shot_running
    global waiting_for_shot_button_off
    state = GPIO.input(2)
    is_shot_running = state == GPIO.HIGH

    if waiting_for_shot_button_off and state == GPIO.LOW:
        waiting_for_shot_button_off = False

def simulateShotButtonOff():
    global is_shot_running
    global waiting_for_shot_button_off
    is_shot_running = False
    waiting_for_shot_button_off = True


def setRelay(input):
    with open("relay.txt", "w") as f:
        f.write(input)

async def connect_to_scale(address):
    client = BleakClient(address, disconnect_callback)
    try:
        await client.connect()
        await client.start_notify(DATA_CHARACTERISTIC_UUID, notification_handler)
        print("Notifications enabled")
        
        # Small delay to ensure notifications start
        await asyncio.sleep(1)  # Wait a second for initial data
        
        return client
    except Exception as e:
        print(f"Error: {e}")
        await client.disconnect()
        return None

def print_scale_data():
    global last_printed_message
    message = f"Weight: {current_weight}{current_scale_unit}, Battery Level: {current_battery_level:.2f}%, Shot Running: {is_shot_running}"
    if message != last_printed_message:
        last_printed_message = message
        print(message)


async def monitor_scale(client):
    global is_shot_running, is_connected

    while is_connected:
        simulateShotButton()

        print_scale_data()

        if is_shot_running:
            await shotStopper(client)
        await asyncio.sleep(0.1)

async def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    with open("mac_addresses.txt", "r") as f:
        address = f.readline().strip()

    global is_connected
    while True:
        if not is_connected:
            client = await connect_to_scale(address)
            if client:
                is_connected = True
                await monitor_scale(client)

# Run the main function
asyncio.run(main())

