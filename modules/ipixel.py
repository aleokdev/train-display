from PIL import Image
from bleak import BleakClient
from modules import ipixel_commands

class IPixelScreen:
    def __init__(self, mac_addr: str):
        self._client = BleakClient(mac_addr)
        
    async def update_screen(self, image: Image.Image):
        cmd_bytes = ipixel_commands.send_animation(image)
        await self._client.connect()
        await self._client.write_gatt_char("0000fa02-0000-1000-8000-00805f9b34fb", cmd_bytes)
