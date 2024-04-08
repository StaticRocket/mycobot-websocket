"""
A websocket server to send commands to the myCobot 280-Pi
"""

import asyncio
from websockets.server import serve
import pymycobot
from pymycobot.genre import Angle
from pymycobot.genre import Coord

# Configurables
SERVER = "0.0.0.0"
PORT = 8765
MC = pymycobot.MyCobot("/dev/ttyS3", pymycobot.PI_BAUD)

# Globals
CMD_LOCK = asyncio.Lock()
GLOBAL_FEED = 50


async def on():
    """
    Ensure the device is powered on
    """
    async with CMD_LOCK:
        MC.power_on()
        return MC.get_error_information()


async def off():
    """
    Ensure the device is powered off
    """
    async with CMD_LOCK:
        MC.power_off()
        return MC.get_error_information()


async def home():
    """
    Try to home the device
    """
    async with CMD_LOCK:
        MC.send_angles([0] * 7, 50)
        return MC.get_error_information()


async def linear_move(cmd_args):
    """
    Parse the extra parameters for the linear move command
    """
    feed_rate = GLOBAL_FEED
    axies = ["X", "Y", "Z", "A", "B", "C", "D"]
    updated = [0, 0, 0, 0, 0, 0, 0]
    async with CMD_LOCK:
        coords = MC.get_coords()
    for arg in cmd_args:
        if arg[0] == "F":
            feed_rate = int(arg[1:])
        elif arg[0] in axies:
            index = axies.index(arg[0])
            coords[index] = int(arg[1:])
        else:
            print("Unparsed argument:", arg)
    async with CMD_LOCK:
        MC.send_coord(coords, feed_rate)
        return MC.get_error_information()
    return 1


async def parse_cmd(cmd):
    """
    Unravel command
    """
    if not cmd:
        return 1

    ret = 0
    cmd_arr = cmd.upper().split()
    if cmd_arr[0] == ";":
        pass
    elif cmd_arr[0] == "G1":
        ret = await linear_move(cmd_arr[1:])
    elif cmd_arr[0] == "G30":
        ret = await home()
    elif cmd_arr[0] == "M80":
        ret = await on()
    elif cmd_arr[0] == "M81":
        ret = await off()
    else:
        print("Not implemented:", cmd)
        ret = 1

    return ret


async def handler(websocket):
    """
    Listen and respond to incoming messages
    """
    async for message in websocket:
        await websocket.send(str(await parse_cmd(message)))


async def main():
    """
    Start the websocket server
    """
    async with serve(handler, SERVER, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
