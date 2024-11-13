import asyncio
from bleak import BleakClient
from const import (
    DATA_CHARACTERISTIC_UUID, 
    CMD_STOP_TIMER,
    CMD_TOGGLE_PRECISION
)


async def connect_to_scale(address):
    try:
        async with BleakClient(address) as client:
            while True:
                name = input("Enter hex command: ")
                if not name:
                    break
                command = int(name, 16)
                print(f"Sending command: {hex(command)}")
                await client.write_gatt_char(DATA_CHARACTERISTIC_UUID, bytearray([command]))
    except Exception as e:
        print(f"Error: {e}")
    
# open mac_addresses.txt and read first line, then run connect_to_scale
with open("mac_addresses.txt", "r") as f:
    address = f.readline().strip()

# Run the main connection loop
asyncio.run(connect_to_scale(address))
