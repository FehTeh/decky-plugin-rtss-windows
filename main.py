import os
import sys
import decky
import asyncio

# Adiciona a pasta atual do plugin ao caminho de pesquisa do Python
plugin_path = os.path.dirname(os.path.realpath(__file__))
if plugin_path not in sys.path:
    sys.path.append(plugin_path)

try:
    from scripts.rtss import RTSSControl
    decky.logger.info("RTSSControl import with success!")
except Exception as e:
    decky.logger.error(f"Error importing RTSSControl: {e}")

class Plugin:
    def __init__(self):
        self.rtss = RTSSControl()

    async def set_osd_status(self, state: int):
        """Turns the OSD on or off based on the state parameter."""
        return self.rtss.send_command(f"OSD {state}")

    async def change_overlay_file(self, filename: str):
        """Changes the overlay layout (e.g., Minimal.ovl)"""
        return self.rtss.send_command(f"LoadFile {filename}")

    async def _main(self):
        decky.logger.info("RTSS Plugin loaded!")

    async def _unload(self):
        pass