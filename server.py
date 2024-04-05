"""
A websocket server to send commands to the myCobot 280-Pi
"""

import asyncio
from websockets.server import serve
import pymycobot
from pymycobot.genre import Angle

# Configurables
SERVER = "0.0.0.0"
PORT = 8765
MC = pymycobot.MyCobot("/dev/ttyS3", pymycobot.PI_BAUD)

# Globals
CMD_LOCK = asyncio.Lock()


def on():
    """
    Ensure the device is powered on
    """
    if MC.is_power_on():
        print("Already on")
    else:
        MC.power_on()


def off():
    """
    Ensure the device is powered off
    """
    if not MC.is_power_on():
        print("Already off")
    else:
        MC.power_off()


def parse_cmd(cmd):
    """
    Unravel command
    """
    cmd_arr = cmd.split()
    if len(cmd_arr) == 3:
        try:
            joint = int(cmd_arr[0])
            position = int(cmd_arr[1])
            speed = int(cmd_arr[2])
        except:
            print("Failed to parse command: ", cmd)
            return 1

        try:
            MC.send_angle(joint, position, speed)
            return 0
        except Exception as e:
            print("Exception: ", e)

    return 1


async def handler(websocket):
    """
    Listen and respond to incoming messages
    """
    async for message in websocket:
        async with CMD_LOCK:
            parse_cmd(message)


async def main():
    """
    Setup the device and start the websocket server
    """
    async with CMD_LOCK:
        on()
        print("Zeroing out")
        MC.send_angles([0, 0, 0, 0, 0, 0], 50)
    async with serve(handler, SERVER, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
