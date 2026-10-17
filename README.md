# Zenon

Zenon is a small Windows Python helper for the fishing minigame in a custom Roblox game. It watches a selected part of the screen, helps keep the bobber in the orange range, and can click when the cast-ready turquoise cue appears.

> Use this with your own Roblox experience and follow Roblox's rules. Keep the game visible and attended while Zenon is running.

## What it does

- Tracks the bobber and orange target range in a screen area you select.
- Adjusts the left mouse button to help keep the bobber in range.
- Looks for the turquoise cast-ready cue, including in dark scenes.
- Waits for the cue to disappear and return before clicking again, with a four-second minimum between clicks.
- Lets you set start and stop keys and shows an always-on-top active indicator.

The detector is tuned for the current game UI. Screen resolution, UI scaling, or game updates may affect detection. Holding the left mouse button is expected to lower the bobber; releasing it lets the bobber rise.

## Run it on Windows

### 1. Install Python

Install Python 3.10 or newer from [python.org](https://www.python.org/downloads/windows/). During setup, enable **Add Python to PATH**. The Python Launcher (`py`) should also be installed.

### 2. Download Zenon

On this GitHub page, click the green **Code** button, then **Download ZIP**. Extract the ZIP somewhere easy to find, such as your Documents folder.

### 3. Install the required packages

Open the extracted project folder in File Explorer (the folder containing `fishing_helper.py` and `README.md`). Click the address bar, type `powershell`, and press Enter. In the PowerShell window, run:

```powershell
py -m pip install -r requirements.txt
```

Wait for it to finish. This only needs to be done once.

### 4. Start Zenon

In that same PowerShell window, run:

```powershell
py fishing_helper.py
```

### 5. Set up the fishing area

In Roblox, show the fishing bars. In Zenon, choose an area that includes both bars and the full area where the turquoise cast-ready oval can appear. Keep Roblox focused while fishing. Press **F8** (or your configured start key) to start and **Esc** (or your configured stop key) to stop. Closing Zenon releases the left mouse button if it is being held.

## Build a standalone app (optional)

If you want an `.exe` instead of running the Python file, double-click `build_exe.bat` on Windows with Python 3.10+ and the Python Launcher installed. The result is written to `release\Zenon.exe`. The Python source is the main download for this project; the standalone build is optional.

## For contributors

Install dependencies with `py -m pip install -r requirements.txt`, then run `py fishing_helper.py`. Pull requests and bug reports are welcome.
