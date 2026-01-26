#!/usr/bin/env python3
"""Print the hex color code of the pixel currently under the cursor."""

from __future__ import annotations

import argparse
import colorsys
import ctypes
from dataclasses import dataclass
import sys
import time
from typing import Protocol

IS_WINDOWS = sys.platform.startswith("win")


@dataclass(frozen=True)
class RGB:
    """Simple RGB color container."""

    r: int
    g: int
    b: int

    def to_hex(self) -> str:
        """Return the color formatted as a hex code (e.g. #1a2b3c)."""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"


def clamp_channel(value: int) -> int:
    """Clamp an integer channel value into the 0..255 range."""
    return max(0, min(255, value))


def rgb_from_x11_pixel(pixel_value: int) -> RGB:
    """Extract RGB channels from a 0xRRGGBB-style pixel value."""
    r = clamp_channel((pixel_value >> 16) & 0xFF)
    g = clamp_channel((pixel_value >> 8) & 0xFF)
    b = clamp_channel(pixel_value & 0xFF)
    return RGB(r, g, b)


def rgb_from_windows_colorref(colorref: int) -> RGB:
    """Extract RGB channels from a Windows COLORREF (0x00bbggrr)."""
    r = clamp_channel(colorref & 0xFF)
    g = clamp_channel((colorref >> 8) & 0xFF)
    b = clamp_channel((colorref >> 16) & 0xFF)
    return RGB(r, g, b)


def classify_color(color: RGB) -> str:
    """Return a human-friendly color name based on HSV ranges."""
    r, g, b = (channel / 255.0 for channel in (color.r, color.g, color.b))
    hue, saturation, value = colorsys.rgb_to_hsv(r, g, b)
    hue_deg = hue * 360.0

    if value < 0.12:
        return "black"
    if saturation < 0.12:
        if value > 0.9:
            return "white"
        return "gray"

    if hue_deg < 15 or hue_deg >= 345:
        return "red"
    if hue_deg < 45:
        return "orange"
    if hue_deg < 70:
        return "yellow"
    if hue_deg < 160:
        return "green"
    if hue_deg < 200:
        return "cyan"
    if hue_deg < 255:
        return "blue"
    if hue_deg < 290:
        return "purple"
    if hue_deg < 345:
        return "magenta"
    return "red"


class PixelReader(Protocol):
    """Protocol describing the behavior required by the main loop."""

    def close(self) -> None:
        """Release any OS resources held by the reader."""

    def get_cursor_position(self) -> tuple[int, int]:
        """Return cursor coordinates relative to the desktop."""

    def get_pixel(self, x: int, y: int) -> RGB:
        """Read the pixel at the given coordinates."""


class POINT(ctypes.Structure):
    """Win32 POINT structure."""

    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class WindowsPixelReader:
    """Read pixels and cursor position using Win32 APIs."""

    CLR_INVALID = 0xFFFFFFFF

    def __init__(self) -> None:
        if not IS_WINDOWS:
            raise RuntimeError("WindowsPixelReader is only available on Windows.")

        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

        self.user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
        self.user32.GetCursorPos.restype = ctypes.c_bool
        self.user32.GetDC.argtypes = [ctypes.c_void_p]
        self.user32.GetDC.restype = ctypes.c_void_p
        self.user32.ReleaseDC.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        self.user32.ReleaseDC.restype = ctypes.c_int

        self.gdi32.GetPixel.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        self.gdi32.GetPixel.restype = ctypes.c_uint

        self.hdc = self.user32.GetDC(None)
        if not self.hdc:
            raise RuntimeError("Unable to acquire the desktop device context.")

    def close(self) -> None:
        """Release the device context."""
        if getattr(self, "hdc", None):
            self.user32.ReleaseDC(None, self.hdc)
            self.hdc = None

    def get_cursor_position(self) -> tuple[int, int]:
        """Return the cursor coordinates relative to the desktop."""
        point = POINT()
        if not self.user32.GetCursorPos(ctypes.byref(point)):
            raise RuntimeError("GetCursorPos failed.")
        return int(point.x), int(point.y)

    def get_pixel(self, x: int, y: int) -> RGB:
        """Read the pixel at the given coordinates."""
        colorref = int(self.gdi32.GetPixel(self.hdc, x, y))
        if colorref == self.CLR_INVALID:
            raise RuntimeError("GetPixel failed.")
        return rgb_from_windows_colorref(colorref)


def create_reader() -> PixelReader:
    """Create the appropriate reader for the current platform."""
    if IS_WINDOWS:
        return WindowsPixelReader()
    raise RuntimeError(
        f"Unsupported platform '{sys.platform}'. This script runs on Windows 10/11 only."
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print the hex color code of the pixel under the mouse cursor "
            "(Windows 10/11)."
        )
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.2,
        help="Seconds to wait between samples (default: 0.2).",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Sample once and exit.",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in CLI mode (prints to stdout) instead of launching the GUI.",
    )
    return parser.parse_args(argv)


def format_output(x: int, y: int, color: RGB) -> str:
    """Format a single output line."""
    color_name = classify_color(color)
    return (
        f"x={x:4d} y={y:4d} rgb=({color.r:3d},{color.g:3d},{color.b:3d}) "
        f"hex={color.to_hex()} color={color_name}"
    )


def run_cli(interval: float, once: bool) -> int:
    """Run the CLI polling loop."""
    reader = create_reader()
    try:
        while True:
            x, y = reader.get_cursor_position()
            color = reader.get_pixel(x, y)
            print(format_output(x, y, color), flush=True)
            if once:
                return 0
            time.sleep(max(0.01, interval))
    finally:
        reader.close()


def run_gui(interval: float) -> int:
    """Launch a small Tkinter GUI for live sampling."""
    import tkinter as tk
    from tkinter import ttk

    reader = create_reader()
    interval_ms = max(10, int(interval * 1000))

    root = tk.Tk()
    root.title("Pixel Hex Under Cursor")
    root.resizable(False, False)

    padding = {"padx": 12, "pady": 8}

    hex_label = ttk.Label(root, text="#000000", font=("Segoe UI", 20, "bold"))
    hex_label.grid(row=0, column=0, columnspan=2, **padding)

    color_name_label = ttk.Label(root, text="color: unknown", font=("Segoe UI", 12))
    color_name_label.grid(row=1, column=0, columnspan=2, **padding)

    swatch = tk.Canvas(root, width=120, height=120, highlightthickness=1)
    swatch.grid(row=2, column=0, columnspan=2, padx=12, pady=10)
    swatch_rect = swatch.create_rectangle(0, 0, 120, 120, fill="#000000", outline="")

    status_var = tk.StringVar(value="stopped")
    status_label = ttk.Label(root, textvariable=status_var)
    status_label.grid(row=3, column=0, columnspan=2, **padding)

    is_running = False
    after_id: str | None = None

    def apply_color(color: RGB) -> None:
        color_hex = color.to_hex()
        color_name = classify_color(color)
        hex_label.configure(text=color_hex, foreground=color_hex)
        color_name_label.configure(text=f"color: {color_name}")
        swatch.itemconfigure(swatch_rect, fill=color_hex)

    def sample_once() -> None:
        nonlocal after_id
        x, y = reader.get_cursor_position()
        color = reader.get_pixel(x, y)
        apply_color(color)
        status_var.set(f"running at x={x} y={y}")
        if is_running:
            after_id = root.after(interval_ms, sample_once)
        else:
            after_id = None

    def start() -> None:
        nonlocal is_running
        if is_running:
            return
        is_running = True
        status_var.set("running")
        sample_once()

    def stop() -> None:
        nonlocal is_running, after_id
        is_running = False
        status_var.set("stopped")
        if after_id is not None:
            root.after_cancel(after_id)
            after_id = None

    def on_close() -> None:
        stop()
        reader.close()
        root.destroy()

    start_button = ttk.Button(root, text="Start", command=start)
    start_button.grid(row=4, column=0, padx=12, pady=(4, 12), sticky="ew")

    stop_button = ttk.Button(root, text="Stop", command=stop)
    stop_button.grid(row=4, column=1, padx=12, pady=(4, 12), sticky="ew")

    root.protocol("WM_DELETE_WINDOW", on_close)

    start()
    root.mainloop()

    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.cli or args.once:
        return run_cli(args.interval, args.once)
    return run_gui(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
