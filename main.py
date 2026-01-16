import ctypes
import time
import mmap
import struct

# The decky plugin module is located at decky-loader/plugin
import decky
import asyncio

# RTSS Shared Memory Constants
RTSS_SHARED_MEMORY_NAME = "RTSSSharedMemoryV2"
RTSS_SIGNATURE = 0x52545353  # 'RTSS'
MAX_PATH = 260

# RTSS App Flags (from RTSSSharedMemory.h)
APPFLAG_PROFILE_UPDATE_REQUESTED = 0x10000000

class RTSSSharedMemory:
    def __init__(self):
        self.shared_memory = None
        self.header = None
        
    def is_rtss_running(self):
        """Check if RTSS is running by looking for its process"""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and 'rtss' in proc.info['name'].lower():
                    decky.logger.info(f"Found RTSS process: {proc.info['name']} (PID: {proc.info['pid']})")
                    return True
            decky.logger.warning("RTSS process not found")
            return False
        except ImportError:
            # psutil not available, try alternative method
            try:
                import subprocess
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq RTSS.exe'], 
                                      capture_output=True, text=True)
                if 'RTSS.exe' in result.stdout:
                    decky.logger.info("Found RTSS.exe via tasklist")
                    return True
                else:
                    decky.logger.warning("RTSS.exe not found via tasklist")
                    return False
            except Exception as e:
                decky.logger.warning(f"Could not check RTSS process via tasklist: {e}")
                # If we can't check, assume it's running and let the shared memory check fail
                return True
        except Exception as e:
            decky.logger.error(f"Error checking RTSS process: {e}")
            return False
        
    def open_shared_memory(self):
        """Open RTSS shared memory for reading/writing"""
        try:
            decky.logger.info(f"Attempting to open RTSS shared memory: {RTSS_SHARED_MEMORY_NAME}")
            
            # First check if RTSS is running
            if not self.is_rtss_running():
                decky.logger.error("RTSS is not running, cannot access shared memory")
                return False
            
            # Try to open the shared memory
            self.file_mapping = ctypes.windll.kernel32.OpenFileMappingA(
                0x0004 | 0x0002,  # FILE_MAP_READ | FILE_MAP_WRITE
                False,
                RTSS_SHARED_MEMORY_NAME.encode('ascii')
            )
            
            if not self.file_mapping:
                error_code = ctypes.windll.kernel32.GetLastError()
                decky.logger.error(f"Failed to open RTSS shared memory mapping. Error code: {error_code}")
                decky.logger.error("RTSS shared memory not found. Is RTSS running and monitoring applications?")
                return False
                
            decky.logger.info("RTSS shared memory mapping opened successfully")
                
            # Map view of file
            self.shared_memory = ctypes.windll.kernel32.MapViewOfFile(
                self.file_mapping,
                0x0004 | 0x0002,  # FILE_MAP_READ | FILE_MAP_WRITE
                0, 0, 0
            )
            
            if not self.shared_memory:
                error_code = ctypes.windll.kernel32.GetLastError()
                decky.logger.error(f"Failed to map RTSS shared memory view. Error code: {error_code}")
                ctypes.windll.kernel32.CloseHandle(self.file_mapping)
                return False
                
            decky.logger.info(f"RTSS shared memory mapped successfully at address: {hex(self.shared_memory)}")
            
            # Cast to proper pointer type for memory access
            self.shared_memory = ctypes.cast(self.shared_memory, ctypes.POINTER(ctypes.c_byte))
            return True
            
        except Exception as e:
            decky.logger.error(f"Failed to open RTSS shared memory: {e}")
            return False
    
    def close_shared_memory(self):
        """Close RTSS shared memory"""
        if self.shared_memory:
            # UnmapViewOfFile expects the original pointer value
            ctypes.windll.kernel32.UnmapViewOfFile(ctypes.cast(self.shared_memory, ctypes.c_void_p))
            self.shared_memory = None
        if self.file_mapping:
            ctypes.windll.kernel32.CloseHandle(self.file_mapping)
            self.file_mapping = None
    
    def read_header(self):
        """Read RTSS shared memory header"""
        if not self.shared_memory:
            decky.logger.error("Shared memory pointer is null")
            return None
            
        try:
            decky.logger.info(f"Reading RTSS header from pointer: {self.shared_memory}")
            decky.logger.info("Attempting to read first byte...")
            
            # Try to read just the first byte to test access
            first_byte = self.shared_memory[0]
            decky.logger.info(f"First byte read successfully: {hex(first_byte)}")
            
            # Read header (first 20 bytes for v2.x) directly from the pointer
            decky.logger.info("Reading header data byte by byte...")
            header_bytes = []
            for i in range(20):
                try:
                    byte_val = self.shared_memory[i]
                    header_bytes.append(byte_val)
                    if i < 5:  # Log first few bytes
                        decky.logger.info(f"Byte {i}: {hex(byte_val)}")
                except Exception as byte_e:
                    decky.logger.error(f"Failed to read byte {i}: {byte_e}")
                    return None
            
            header_data = bytes(header_bytes)
            decky.logger.info(f"Header data read: {header_data.hex()}")
            
            dwSignature, dwVersion, dwAppEntrySize, dwAppArrOffset, dwAppArrSize = struct.unpack('IIIII', header_data)
            
            decky.logger.info(f"RTSS header: sig={dwSignature:08X}, ver={dwVersion:08X}, entry_size={dwAppEntrySize}, arr_offset={dwAppArrOffset}, arr_size={dwAppArrSize}")
            
            if dwSignature != RTSS_SIGNATURE:
                decky.logger.error(f"Invalid RTSS signature: {dwSignature:08X} (expected {RTSS_SIGNATURE:08X})")
                return None
                
            return {
                'signature': dwSignature,
                'version': dwVersion,
                'app_entry_size': dwAppEntrySize,
                'app_arr_offset': dwAppArrOffset,
                'app_arr_size': dwAppArrSize
            }
            
        except Exception as e:
            decky.logger.error(f"Failed to read RTSS header: {e}")
            return None
    
    def read_app_entry(self, index):
        """Read application entry at specified index"""
        if not self.shared_memory or not self.header:
            return None
            
        try:
            offset = self.header['app_arr_offset'] + (index * self.header['app_entry_size'])
            
            # Read app entry (first 276 bytes for basic fields) directly from the pointer
            app_data = bytes(self.shared_memory[i + offset] for i in range(276))
            dwProcessID, szName, dwFlags, dwTime0, dwTime1, dwFrames = struct.unpack('I260sIIII', app_data)
            
            # Convert name from bytes to string
            szName = szName.decode('ascii', errors='ignore').rstrip('\x00')
            
            return {
                'process_id': dwProcessID,
                'name': szName,
                'flags': dwFlags,
                'time0': dwTime0,
                'time1': dwTime1,
                'frames': dwFrames
            }
            
        except Exception as e:
            decky.logger.error(f"Failed to read app entry {index}: {e}")
            return None
    
    def write_app_flags(self, index, flags):
        """Write flags to application entry"""
        if not self.shared_memory or not self.header:
            return False
            
        try:
            offset = self.header['app_arr_offset'] + (index * self.header['app_entry_size']) + 264  # dwFlags offset
            
            # Write dwFlags (4 bytes) directly to the pointer
            flags_bytes = struct.pack('I', flags)
            for i, byte in enumerate(flags_bytes):
                self.shared_memory[offset + i] = byte
            
            return True
            
        except Exception as e:
            decky.logger.error(f"Failed to write app flags for entry {index}: {e}")
            return False
    
    def find_app_entry(self, process_name=None, process_id=None):
        """Find application entry by name or PID"""
        if not self.header:
            return -1
            
        for i in range(self.header['app_arr_size']):
            app = self.read_app_entry(i)
            if not app or app['process_id'] == 0:
                continue
                
            decky.logger.debug(f"Found RTSS app entry {i}: PID={app['process_id']}, Name='{app['name']}'")
                
            if (process_name and process_name.lower() in app['name'].lower()) or \
               (process_id and app['process_id'] == process_id):
                return i
                
        return -1
    
    def set_profile_for_app(self, app_index, profile):
        """Set RTSS profile for specific application"""
        if profile < 0 or profile > 4:
            return False
            
        # RTSS uses profile IDs directly (0-4)
        flags = APPFLAG_PROFILE_UPDATE_REQUESTED | profile
        
        return self.write_app_flags(app_index, flags)

class Plugin:
    def __init__(self):
        self.rtss = RTSSSharedMemory()
        self.current_app_index = -1



    def _set_rtss_profile(self, profile: int):
        """Set RTSS profile using shared memory"""
        try:
            # Check if RTSS is running first
            if not self.rtss.is_rtss_running():
                decky.logger.error("RTSS is not running. Please start RivaTuner Statistics Server first.")
                return False
            
            # Open shared memory
            if not self.rtss.open_shared_memory():
                decky.logger.error("Failed to open RTSS shared memory. Make sure RTSS is running and monitoring applications.")
                return False
            
            # Read header
            self.rtss.header = self.rtss.read_header()
            if not self.rtss.header:
                self.rtss.close_shared_memory()
                return False
            
            decky.logger.info(f"RTSS shared memory opened successfully. Version: {self.rtss.header['version']:08X}")
            
            # Find current foreground application or any active RTSS-monitored app
            # For now, we'll find the first valid app entry
            app_index = self.rtss.find_app_entry()
            
            if app_index == -1:
                decky.logger.warning("No active RTSS-monitored applications found. Start a game that RTSS monitors.")
                self.rtss.close_shared_memory()
                return False
            
            app_info = self.rtss.read_app_entry(app_index)
            decky.logger.info(f"Setting profile for app: {app_info['name']} (PID: {app_info['process_id']})")
            
            # Set profile for the application (0 = hide, 1 = show overlay)
            success = self.rtss.set_profile_for_app(app_index, profile)
            
            self.rtss.close_shared_memory()
            
            if success:
                decky.logger.info(f"RTSS profile {profile} set for app at index {app_index}")
            else:
                decky.logger.error(f"Failed to set RTSS profile {profile}")
            
            return success
            
        except Exception as e:
            decky.logger.error(f"Error setting RTSS profile: {e}")
            try:
                self.rtss.close_shared_memory()
            except:
                pass
            return False

    async def set_rtss_profile(self, profile: int) -> bool:
        decky.logger.info(f"Setting RTSS profile to {profile}")
        if profile < 0 or profile > 1:
            decky.logger.error(f"Invalid profile {profile}")
            return False
        
        success = self._set_rtss_profile(profile)
        if success:
            decky.logger.info(f"RTSS profile {profile} set successfully")
        else:
            decky.logger.error(f"Failed to set RTSS profile {profile}")
        return success



    # Asyncio-compatible long-running code, executed in a task when the plugin is loaded
    async def _main(self):
        self.loop = asyncio.get_event_loop()
        decky.logger.info("RTSS Plugin loaded!")

    # Function called first during the unload process
    async def _unload(self):
        decky.logger.info("RTSS Plugin unloading!")
        pass

    # Function called after `_unload` during uninstall
    async def _uninstall(self):
        decky.logger.info("RTSS Plugin uninstalling!")
        pass

    # Migrations
    async def _migration(self):
        decky.logger.info("Migrating RTSS Plugin")
        # Add migrations if needed
