# Pixel hex under cursor (X11)

This repository provides a small Python CLI that prints the hex color code of the pixel currently under your mouse cursor.

## Requirements

* Linux running an **X11** session (Wayland may require XWayland compatibility).
* Python 3.10+.

No third-party Python packages are required.

## How to get the file

### Option 1: download directly from a repo

If this project is hosted on GitHub, you can download just the script with `curl`:

```bash
curl -o pixel_hex_under_cursor.py \
  https://raw.githubusercontent.com/<OWNER>/<REPO>/<BRANCH>/pixel_hex_under_cursor.py
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

## Notes

The program uses `ctypes` to call the X11 API directly (`libX11.so.6`) to:

1. query the cursor position via `XQueryPointer`, and
2. read the pixel color via `XGetImage` + `XGetPixel`.
