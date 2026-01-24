# Pixel hex under cursor (Windows 10/11)

This repository provides a small Python CLI that prints the hex color code of the pixel currently under your mouse cursor using native Win32 APIs via `ctypes`.

## Requirements

* Windows 10/11.
* Python 3.10+.

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

From the repository root:

```powershell
python pixel_hex_under_cursor.py
```

Sample once and exit:

```powershell
python pixel_hex_under_cursor.py --once
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
