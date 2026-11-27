import asyncio

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError

import backend
import jsonLog

DEVICE_NAME = "Them Crooked Vultures"
SERVICE_UUID = "377aa64e-3265-4da3-a529-7d4f06c0a7f0"
LED_UUID = "f5c287f5-febb-47bd-be3b-c3a4955bc07b"
CRED_UUID = "6e1d7a52-3f0b-4c7e-9a41-5b8d2c0f1e93"
RESULT_UUID = "a3c4f8d1-72e5-4b19-8d6a-0c9e4f2b7a15"
EVENT_UUID = "c2b7e9a4-5d13-4f86-b0a2-7e1d9c3f4a68"

RETRY_MIN_S = 2    # first wait after a failure
RETRY_MAX_S = 30   # the wait doubles each failure, up to this

EVENT_LOG = {
    "opened":      ("info",    "safe opened"),
    "closed":      ("info",    "safe closed"),
    "closed_late": ("warning", "safe closed after being open too long"),
    "alarm":       ("warning", "safe open too long"),
}


def on_event(_, data: bytearray):
    name = bytes(data).decode(errors="ignore")
    level, message = EVENT_LOG.get(name, ("warning", f"unknown event: {name}"))
    getattr(jsonLog, level)("safe", message)
    print(f"Safe event: {name}")


async def safe_handle_login(client, text):
    pin, passcode = text.split(":", 1)

    ok = backend.check_login(pin, passcode, "keypad")

    try:
        await client.write_gatt_char(RESULT_UUID, bytes([1 if ok else 2]), response=True)
    except (BleakError, OSError) as error:
        jsonLog.error("keypad", f"could not send result to ESP32: {error}")
        return

    if ok:
        jsonLog.info("Safe login", f"The safe has been opened by {pin}")
    else:
        jsonLog.warning("Safe login", f"Someone tried opening the safe with {pin}")


async def run_session():
    """Scan, connect and serve until the connection drops.
    Returns True if a connection was made, False if the device wasn't found."""
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
        return False

    print(f"Found {device.name} [{device.address}]")

    tasks = set()

    def on_disconnect(_client):
        print("ESP32 disconnected.")

    async with BleakClient(device, disconnected_callback=on_disconnect, timeout=15.0) as client:
        print("Connected.")
        jsonLog.info("ble", "connected to ESP32")

        def on_cred(_, data: bytearray):
            text = bytes(data).decode(errors="ignore")
            if ":" not in text:
                return
            task = asyncio.create_task(safe_handle_login(client, text))
            tasks.add(task)  # keep a reference so it isn't garbage collected
            task.add_done_callback(tasks.discard)

        await client.start_notify(CRED_UUID, on_cred)
        await client.start_notify(EVENT_UUID, on_event)

        while client.is_connected:
            data = await client.read_gatt_char(LED_UUID)
            if data is not None:
                await client.write_gatt_char(
                    LED_UUID,
                    bytes([(data[0] ^ 0x01) & 0x01]),
                    response=True,
                )
            await asyncio.sleep(1)

    # Reached when the link drops without an exception
    for task in tasks:
        task.cancel()
    return True


async def main():
    backend.start()   # Flask runs in its own thread and stays up across reconnects
    delay = RETRY_MIN_S

    while True:
        try:
            connected = await run_session()
            if connected:
                delay = RETRY_MIN_S   # it worked, so start the backoff over
                jsonLog.warning("ble", "connection to ESP32 lost")
        except (BleakError, OSError, asyncio.TimeoutError) as error:
            print(f"Bluetooth error: {error}")
            jsonLog.error("ble", f"bluetooth error: {error}")

        print(f"Retrying in {delay}s...")
        await asyncio.sleep(delay)
        delay = min(delay * 2, RETRY_MAX_S)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")