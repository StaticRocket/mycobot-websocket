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

def get_error_and_clear():
    """
    Wapper for get and clear command
    """
    error = MC.get_error_information()
    MC.clear_error_information()
    return error

async def on():
    """
    Ensure the device is powered on
    """
    async with CMD_LOCK:
        MC.power_on()
        return get_error_and_clear()


async def off():
    """
    Ensure the device is powered off
    """
    async with CMD_LOCK:
        MC.power_off()
        return get_error_and_clear()


async def home():
    """
    Try to home the device
    """
    async with CMD_LOCK:
        MC.sync_send_angles([0] * 7, 50)
        return get_error_and_clear()


async def cheap_move(cmd_args):
    """
    Parse the extra parameters for the cheap move command

    This is currently riding on the syntax for a linear move but there were some issues preventing
    it from actually being a proper linear move right now.
    """
    feed_rate = GLOBAL_FEED
    axies = ["X", "Y", "Z", "A", "B", "C"]
    async with CMD_LOCK:
        angles = MC.get_angles()
    for arg in cmd_args:
        if arg[0] == "F":
            feed_rate = int(arg[1:])
        elif arg[0] in axies:
            index = axies.index(arg[0])
            angles[index] = int(arg[1:])
        else:
            print("Unparsed argument:", arg)
    async with CMD_LOCK:
        MC.sync_send_angles(angles, feed_rate)
        return get_error_and_clear()


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
        ret = await cheap_move(cmd_arr[1:])
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
