import asyncio
from bleak import BleakScanner

from const import SCALE_START_NAMES

async def find_acaia_devices():
    addresses = []
    await asyncio.sleep(1)
    scanner = BleakScanner()
    try:
        devices = await scanner.discover(timeout=5.0)
        for d in devices:
            if d.name and any(d.name.startswith(name) for name in SCALE_START_NAMES):
                print(d.name, d.address)
                addresses.append(d.address)
        return addresses
    except Exception as e:
        if e.error_name == "org.bluez.Error.InProgress":
            print("Another scan is already in progress, retrying...")
            await asyncio.sleep(1)  # Retry delay
            return await find_acaia_devices()
        else:
            print(f"Unexpected Bluetooth error: {e}")

felicitaAddresses = asyncio.run(find_acaia_devices())


    # write to mac_addresses.txt
with open("mac_addresses.txt", "w") as f:
    for address in felicitaAddresses:
        f.write(f"{address}\n")