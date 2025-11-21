from PIL import Image
from bleak import BleakClient
from modules import ipixel_commands
import io

class IPixelScreen:
    def __init__(self, mac_addr: str):
        self._client = BleakClient(mac_addr)

    async def _send_image(self, image):
        buf = io.BytesIO()
        # Preserve animation if present
        save_kwargs = {"format": "GIF"}
        image.save(buf, **save_kwargs)
        buf.seek(0)
        cmd_bytes = ipixel_commands.send_animation(buf)
        await self._client.write_gatt_char("0000fa02-0000-1000-8000-00805f9b34fb", cmd_bytes)

    async def connect(self):
        await self._client.connect()
        
    async def update_screen(self, images):
        if isinstance(images, list):
            for image in images:
                await self._send_image(image)
        else:
            await self._send_image(images)
