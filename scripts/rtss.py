import ctypes
from ctypes import windll, c_void_p, c_size_t, wintypes
import decky

RTSS_SHARED_MEMORY_NAME = "RTSSSharedMemoryV2"
FILE_MAP_ALL_ACCESS = 0x000F001F
RTSS_COMMAND_ROUTING_OFFSET = 0x200

class RTSSControl:
    def __init__(self):
        # Configurar as funções do Windows
        self.OpenFileMapping = windll.kernel32.OpenFileMappingA
        self.OpenFileMapping.restype = wintypes.HANDLE
        self.OpenFileMapping.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCSTR]

        self.MapViewOfFile = windll.kernel32.MapViewOfFile
        self.MapViewOfFile.restype = c_void_p
        self.MapViewOfFile.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, c_size_t]

    def send_command(self, command_str):
        hMapFile = None
        pBuf = None
        try:
            hMapFile = self.OpenFileMapping(FILE_MAP_ALL_ACCESS, False, RTSS_SHARED_MEMORY_NAME.encode('ascii'))
            if not hMapFile:
                return False

            pBuf = self.MapViewOfFile(hMapFile, FILE_MAP_ALL_ACCESS, 0, 0, 0)
            if not pBuf:
                windll.kernel32.CloseHandle(hMapFile)
                return False

            destination = pBuf + RTSS_COMMAND_ROUTING_OFFSET
            ctypes.memset(destination, 0, 256)
            
            # Comando com o trigger global
            formatted_command = f"< APP >[Global]\n{command_str}\0".encode('ascii')

            decky.logger.info("Sent command: " + formatted_command.decode('ascii').strip())

            ctypes.memmove(destination, formatted_command, len(formatted_command))

            # Trigger Serial Number (Offset 28)
            serial_ptr = ctypes.cast(pBuf + 28, ctypes.POINTER(wintypes.DWORD))
            serial_ptr.contents.value += 1
            
            return True
        finally:
            if pBuf:
                windll.kernel32.UnmapViewOfFile(c_void_p(pBuf))
            if hMapFile:
                windll.kernel32.CloseHandle(hMapFile)