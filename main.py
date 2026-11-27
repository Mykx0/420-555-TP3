import asyncio
import jsonBD
import jsonLog

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError

import backend

DEVICE_NAME = "Them Crooked Vultures"
SERVICE_UUID = "377aa64e-3265-4da3-a529-7d4f06c0a7f0"
LED_UUID = "f5c287f5-febb-47bd-be3b-c3a4955bc07b"
CRED_UUID = "6e1d7a52-3f0b-4c7e-9a41-5b8d2c0f1e93"
RESULT_UUID = "a3c4f8d1-72e5-4b19-8d6a-0c9e4f2b7a15"

async def safe_handle_login(client, text):
    pin, passcode = text.split(":", 1)

    ok = backend.check_login(pin, passcode, "keypad")

    try:
        await client.write_gatt_char(RESULT_UUID, bytes([1 if ok else 2]), response=True)
    except BleakError as error:
        jsonLog.error("keypad", f"could not send result to ESP32: {error}")
        return
    
    jsonLog.info("Safe login", f"The safe has been opened by {pin}") if ok else jsonLog.warning("Safe login", f"Someone tried opening the safe with {pin}")


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
        tasks = set()

        def on_cred(_, data: bytearray):
            text = bytes(data).decode(errors="ignore")
            if ":" not in text:
                return
            task = asyncio.create_task(safe_handle_login(client, text))
            tasks.add(task)  # keep a reference so it isn't garbage collected
            task.add_done_callback(tasks.discard)

        await client.start_notify(CRED_UUID, on_cred)

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