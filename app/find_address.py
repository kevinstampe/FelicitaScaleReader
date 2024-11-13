import asyncio
from bleak import BleakScanner

from const import SCALE_START_NAMES


async def find_acaia_devices(timeout=10, scanner: BleakScanner | None = None) -> list:
    if scanner is None:
        async with BleakScanner() as scanner:
            return await scan(scanner, timeout)
    else:
        return await scan(scanner, timeout)
    

async def scan(scanner: BleakScanner, timeout) -> list:
    addresses = []

    devices = await scanner.discover(timeout=timeout)
    for d in devices:
        if d.name and any(d.name.startswith(name) for name in SCALE_START_NAMES):
            print(d.name, d.address)
            addresses.append(d.address)

    # write to mac_addresses.txt
    with open("mac_addresses.txt", "w") as f:
        for address in addresses:
            f.write(f"{address}\n")

    return addresses

asyncio.run(find_acaia_devices())