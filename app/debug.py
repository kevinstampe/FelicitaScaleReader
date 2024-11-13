import asyncio
from bleak import BleakClient

# Felicita scale characteristics
DEVICE_NAME = "FELICITA"
DATA_SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
DATA_CHARACTERISTIC_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

# Felicita command codes
CMD_TARE = 0x54
CMD_START_TIMER = 0x52
CMD_STOP_TIMER = 0x53
CMD_RESET_TIMER = 0x43
CMD_TOGGLE_UNIT = 0x55
MIN_BATTERY_LEVEL = 129
MAX_BATTERY_LEVEL = 158

# Function to parse notifications
def parse_status_update(felicita_raw_status):
    decimal_data = ' '.join(f'{byte}' for byte in felicita_raw_status)  # Convert each byte to decimal
    print(decimal_data)


async def notification_handler(sender, data):
    parse_status_update(bytearray(data))

async def connect_to_scale(address):
    async with BleakClient(address) as client:
        await client.start_notify(DATA_CHARACTERISTIC_UUID, notification_handler)
        print("Notifications enabled")

        # Example: Tare the scale
        # await client.write_gatt_char(DATA_CHARACTERISTIC_UUID, bytearray([CMD_TARE]))
        # print("Tare command sent")

        # Keep connection open to receive notifications
        await asyncio.sleep(100)
        await client.stop_notify(DATA_CHARACTERISTIC_UUID)

address = "0C8F16A2-0BBD-99EC-1A2D-799B626209CC"
asyncio.run(connect_to_scale(address))

