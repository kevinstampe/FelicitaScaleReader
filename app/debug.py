import asyncio
from bleak import BleakClient

from const import (
    DATA_CHARACTERISTIC_UUID)


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

# Address of the scale

    
# open mac_addresses.txt and read first line, then run connect_to_scale
with open("mac_addresses.txt", "r") as f:
    address = f.readline().strip()

asyncio.run(connect_to_scale(address))

