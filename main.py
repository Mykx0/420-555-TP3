import backend as backend
import asyncio
import time

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError

DEVICE_NAME = "Them Crooked Vultures"
SERVICE_UUID = "377aa64e-3265-4da3-a529-7d4f06c0a7f0"
LED_UUID = "f5c287f5-febb-47bd-be3b-c3a4955bc07b"

async def main():
    backend.start()
    print(f"Scanning for {DEVICE_NAME}...")

    device = await BleakScanner.find_device_by_filter(
        lambda device, advertisement: (
            advertisement.local_name == DEVICE_NAME
            and SERVICE_UUID in advertisement.service_uuids
        ),
        timeout=15.0,
    )

    if device is None:
        print("Device not found. Check that the ESP32 is advertising.")
        return

    print(f"Found {device.name} [{device.address}]")

    async with BleakClient(device) as client:
        print("Connected.")

        while True:
            data = await client.read_gatt_char(LED_UUID)
            if data is not None:
                await client.write_gatt_char(
                    LED_UUID,
                    bytes([(data[0] ^ 0x01) & 0x01]),
                    response=True,
                )
            await asyncio.sleep(1)
       
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")
    except (BleakError, OSError, asyncio.TimeoutError) as error:
        print(f"Bluetooth error: {error}")