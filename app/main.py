import asyncio
from bleak import BleakClient

# Felicita scale characteristics
DEVICE_NAME = "FELICITA"
DATA_SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
DATA_CHARACTERISTIC_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

# Felicita command codes
CMD_RESET_TIMER = 0x43
CMD_TOGGLE_PRECISION = 0x44
CMD_START_TIMER = 0x52
CMD_STOP_TIMER = 0x53
CMD_TARE = 0x54
CMD_TOGGLE_UNIT = 0x55
MIN_BATTERY_LEVEL = 129
MAX_BATTERY_LEVEL = 158

last_battery_level_raw = 0

current_weight = 0
current_battery_level = 0

weight_stop_offset = 1.2 # how many grammes to stop before the target weight
expected_shot_weight = 40

def on_disconnected(client):
    print("Disconnected from the scale")

# runs every notification indefinitely
def parse_status_update(felicita_raw_status):
    if len(felicita_raw_status) != 18:
        print("Malformed data")
        return
    
    decimal_data = ' '.join(f'{byte}' for byte in felicita_raw_status)  # Convert each byte to decimal
    print(f"Decimal data: {decimal_data}")
    
    weight_bytes = felicita_raw_status[3:9]
    scale_unit = bytes(felicita_raw_status[9:11]).decode("utf-8")
    weight = "".join([str(b - 48) for b in weight_bytes])
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

    current_weight = int(weight) / 100
    current_battery_level = battery_percentage

    print(f"Weight: {current_weight}{scale_unit}, Battery Level: {battery_percentage:.2f}%")

async def notification_handler(sender, data):
    parse_status_update(bytearray(data))

async def connect_to_scale(address):
    try:
        async with BleakClient(address) as client:
            client.set_disconnected_callback(on_disconnected)
            await client.start_notify(DATA_CHARACTERISTIC_UUID, notification_handler)
            print("Notifications enabled")

            # one-time commands here:
            await client.write_gatt_char(DATA_CHARACTERISTIC_UUID, bytearray([CMD_STOP_TIMER]))
            await asyncio.sleep(0.1)
            await client.write_gatt_char(DATA_CHARACTERISTIC_UUID, bytearray([CMD_RESET_TIMER]))
            await asyncio.sleep(0.1)
            await client.write_gatt_char(DATA_CHARACTERISTIC_UUID, bytearray([CMD_TARE]))
            await asyncio.sleep(0.1)
            await client.write_gatt_char(DATA_CHARACTERISTIC_UUID, bytearray([CMD_START_TIMER]))
            print("Tare and start timer commands sent")

            global expected_shot_weight

            # Keep connection open
            while current_weight < (expected_shot_weight - weight_stop_offset):
                await asyncio.sleep(0.1)

            await client.write_gatt_char(DATA_CHARACTERISTIC_UUID, bytearray([CMD_STOP_TIMER]))
            print("Stop timer command sent")

            await client.stop_notify(DATA_CHARACTERISTIC_UUID)
    except Exception as e:
        print(f"Error: {e}")
    
# open mac_addresses.txt and read first line, then run connect_to_scale
with open("mac_addresses.txt", "r") as f:
    DEVICE_MAC_ADDRESS = f.readline().strip()

# Run the main connection loop
asyncio.run(connect_to_scale(DEVICE_MAC_ADDRESS))
