# RTSS Overlay Control Decky Plugin

A Decky plugin for controlling RivaTuner Statistics Server (RTSS) overlay visibility on Windows using shared memory.

## Requirements

- Windows 10/11 with Decky Loader installed
- RivaTuner Statistics Server (RTSS) **installed and running**
- Node.js v18+ and pnpm for development

## Installation

1. Install Decky Loader for Windows
2. Install RivaTuner Statistics Server (RTSS)
3. **Start RTSS** before using the plugin
4. Clone this repository
5. Build and install the plugin following Decky development guidelines

## Features

- **Binary Overlay Control**: Simple ON/OFF toggle for RTSS overlay visibility
- **Performance Tab Integration**: Toggle appears in Decky's Performance tab
- **Real-time Control**: Uses RTSS shared memory for instant overlay switching
- **No Hotkey Configuration Required**: Direct memory manipulation, no keyboard simulation

## How It Works

The plugin communicates directly with RTSS through its shared memory interface (`RTSSSharedMemoryV2`). This provides reliable, real-time control of overlay visibility without requiring hotkey configuration or UAC elevation.

### Technical Details

- Reads RTSS shared memory header to locate application entries
- Modifies application flags to request profile updates
- Works with any RTSS-monitored application (games, benchmarks, etc.)
- No dependency on RTSS hotkey settings

### Important Notes

- RTSS must be running and monitoring applications for the plugin to work
- The plugin controls overlay visibility for RTSS-monitored processes
- Works during gameplay without interrupting the game
- No administrator privileges required (unlike command-line approaches)

## Development

### Setup
```bash
pnpm i
pnpm run build
```

### Building
```bash
pnpm run build
```

## Usage

Once installed in Decky Loader on Windows:

1. **Start RTSS** (RivaTuner Statistics Server)
2. **Launch a game** that RTSS monitors
3. **Open Decky's Performance tab** in game mode
4. **Use the "Performance Overlay Level" toggle** to control RTSS overlay:
   - **OFF**: Hide overlay completely
   - **ON**: Show RTSS overlay

The toggle provides instant control without interrupting gameplay. Changes take effect immediately through RTSS shared memory.

## Troubleshooting

**Plugin shows "Failed to set RTSS profile" errors:**
- Ensure RTSS is running (check system tray for RTSS icon)
- Start a game that RTSS monitors (most modern games are detected automatically)
- Check Decky logs for detailed error messages

**Slider doesn't appear in Performance tab:**
- Restart Decky Loader after installing the plugin
- Ensure you're in game mode (not desktop mode)

**Overlay doesn't change:**
- RTSS must be monitoring the active application
- Some games may require specific RTSS profile settings

Example:  
In our makefile used to demonstrate the CI process of building and distributing a plugin backend, note that the makefile explicitly creates the `out` folder (``backend/out``) and then compiles the binary into that folder. Here's the relevant snippet.

```make
hello:
	mkdir -p ./out
	gcc -o ./out/hello ./src/main.c
```

The CI does create the `out` folder itself but we recommend creating it yourself if possible during your build process to ensure the build process goes smoothly.

Note: When locally building your plugin it will be placed into a folder called 'out' this is different from the concept described above.

The out folder is not sent to the final plugin, but is then put into a ``bin`` folder which is found at the root of the plugin's directory.  
More information on the bin folder can be found below in the distribution section below.

### Distribution

We recommend following the instructions found in the [decky-plugin-database](https://github.com/SteamDeckHomebrew/decky-plugin-database) on how to get your plugin up on the plugin store. This is the best way to get your plugin in front of users.
You can also choose to do distribution via a zip file containing the needed files, if that zip file is uploaded to a URL it can then be downloaded and installed via decky-loader.

**NOTE: We do not currently have a method to install from a downloaded zip file in "game-mode" due to lack of a usable file-picking dialog.**

Layout of a plugin zip ready for distribution:
```
pluginname-v1.0.0.zip (version number is optional but recommended for users sake)
   |
   pluginname/ <directory>
   |  |  |
   |  |  bin/ <directory> (optional)
   |  |     |
   |  |     binary (optional)
   |  |
   |  dist/ <directory> [required]
   |      |
   |      index.js [required]
   | 
   package.json [required]
   plugin.json [required]
   main.py {required if you are using the python backend of decky-loader: serverAPI}
   README.md (optional but recommended)
   LICENSE(.md) [required, filename should be roughly similar, suffix not needed]
```

Note regarding licenses: Including a license is required for the plugin store if your chosen license requires the license to be included alongside usage of source-code/binaries!

Standard procedure for licenses is to have your chosen license at the top of the file, and to leave the original license for the plugin-template at the bottom. If this is not the case on submission to the plugin database, you will be asked to fix this discrepancy.

We cannot and will not distribute your plugin on the Plugin Store if it's license requires it's inclusion but you have not included a license to be re-distributed with your plugin in the root of your git repository.
