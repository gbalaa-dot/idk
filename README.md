# Pixel hex under cursor (Windows + X11)

This repository provides a small Python CLI that prints the hex color code of the pixel currently under your mouse cursor.

## Requirements

* **Windows 10/11** (uses Win32 APIs via `ctypes`), or
* **Linux running an X11 session** (Wayland may require XWayland compatibility).
* Python 3.10+.

No third-party Python packages are required.

## How to get the file

### Option 1: download directly from a repo

If this project is hosted on GitHub, you can download just the script.

On macOS/Linux:

```bash
curl -o pixel_hex_under_cursor.py \
  https://raw.githubusercontent.com/<OWNER>/<REPO>/<BRANCH>/pixel_hex_under_cursor.py
```

On Windows PowerShell:

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

```bash
python3 pixel_hex_under_cursor.py
```

Sample once and exit:

```bash
python3 pixel_hex_under_cursor.py --once
```

Adjust the polling interval (seconds):

```bash
python3 pixel_hex_under_cursor.py --interval 0.1
```

> On Windows, `python pixel_hex_under_cursor.py` also works if `python3` is not available.

## Notes

The program uses `ctypes` to call native OS APIs directly:

* **Windows**: `GetCursorPos` + `GetPixel`.
* **X11**: `XQueryPointer` + `XGetImage`/`XGetPixel`.
