# Pixel hex under cursor (Windows 10/11)

This repository provides a small Python app that detects the pixel under your mouse cursor and shows:

* the hex color code,
* a general color name (red/green/blue/etc.), and
* a live color swatch.

It uses native Win32 APIs via `ctypes`.

## Requirements

* Windows 10/11.
* Python 3.10+ with Tkinter available (standard CPython installer includes it).

No third-party Python packages are required.

## How to get the file

### Option 1: download directly from a repo

If this project is hosted on GitHub, you can download just the script using PowerShell:

```powershell
Invoke-WebRequest \
  -Uri "https://raw.githubusercontent.com/<OWNER>/<REPO>/<BRANCH>/pixel_hex_under_cursor.py" \
  -OutFile "pixel_hex_under_cursor.py"
```

Or download the entire repository:

```bash
git clone https://github.com/<OWNER>/<REPO>.git
cd <REPO>
```

### Option 2: copy the file contents manually

Create a new file named `pixel_hex_under_cursor.py` and paste the contents from this repo.

## Usage

### GUI mode (default)

From the repository root:

```powershell
python pixel_hex_under_cursor.py
```

The GUI includes:

* a hex label whose text color matches the detected color,
* a general color label,
* a square swatch showing the current color, and
* **Start** / **Stop** buttons.

### CLI mode

Run in terminal-only mode:

```powershell
python pixel_hex_under_cursor.py --cli
```

Sample once and exit:

```powershell
python pixel_hex_under_cursor.py --once --cli
```

Adjust the polling interval (seconds):

```powershell
python pixel_hex_under_cursor.py --interval 0.1
```

## Windows behavior

The script calls native Windows APIs directly:

* `GetCursorPos` to read the cursor location.
* `GetDC` to access the desktop device context.
* `GetPixel` to read the pixel color.
* `ReleaseDC` to clean up the device context.

On non-Windows platforms, the script exits with a clear unsupported-platform error message.
