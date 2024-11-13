import asyncio
from bleak import BleakClient

async def list_characteristics(mac):
    async with BleakClient(mac) as client:
        services = await client.get_services()
        for service in services:
            print(f"Service: {service}")
            for char in service.characteristics:
                print(f"  Characteristic: {char} - {char.uuid}")


# open mac_addresses.txt and read all lines, then run list_characteristics for each line

with open("mac_addresses.txt", "r") as f:
    for line in f:
        asyncio.run(list_characteristics(line.strip()))
