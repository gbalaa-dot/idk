#!/usr/bin/env python3
"""Print the hex color code of the pixel currently under the cursor."""

from __future__ import annotations

import argparse
import ctypes
from dataclasses import dataclass
import os
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
    """Extract RGB channels from an X11 pixel value."""
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


class PixelReader(Protocol):
    """Protocol describing the behavior required by the main loop."""

    def close(self) -> None:
        """Release any OS resources held by the reader."""

    def get_cursor_position(self) -> tuple[int, int]:
        """Return cursor coordinates relative to the desktop."""

    def get_pixel(self, x: int, y: int) -> RGB:
        """Read the pixel at the given coordinates."""


class X11PixelReader:
    """Read pixels and cursor position directly from the X11 server."""

    def __init__(self) -> None:
        if not os.environ.get("DISPLAY"):
            raise RuntimeError("DISPLAY is not set. This tool requires an X11 session.")

        self.x11 = ctypes.cdll.LoadLibrary("libX11.so.6")

        self.x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.x11.XOpenDisplay.restype = ctypes.c_void_p
        self.x11.XDefaultScreen.argtypes = [ctypes.c_void_p]
        self.x11.XDefaultScreen.restype = ctypes.c_int
        self.x11.XRootWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.x11.XRootWindow.restype = ctypes.c_ulong
        self.x11.XQueryPointer.argtypes = [
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_uint),
        ]
        self.x11.XQueryPointer.restype = ctypes.c_bool
        self.x11.XGetImage.argtypes = [
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_uint,
            ctypes.c_uint,
            ctypes.c_ulong,
            ctypes.c_int,
        ]
        self.x11.XGetImage.restype = ctypes.c_void_p
        self.x11.XGetPixel.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        self.x11.XGetPixel.restype = ctypes.c_ulong
        self.x11.XDestroyImage.argtypes = [ctypes.c_void_p]
        self.x11.XDestroyImage.restype = ctypes.c_int
        self.x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
        self.x11.XCloseDisplay.restype = ctypes.c_int
        self.x11.XFlush.argtypes = [ctypes.c_void_p]
        self.x11.XFlush.restype = ctypes.c_int

        self.display = self.x11.XOpenDisplay(None)
        if not self.display:
            raise RuntimeError("Unable to open X11 display. Are you running under X11?")

        self.screen = self.x11.XDefaultScreen(self.display)
        self.root_window = self.x11.XRootWindow(self.display, self.screen)

    def close(self) -> None:
        """Release the display connection."""
        if getattr(self, "display", None):
            self.x11.XCloseDisplay(self.display)
            self.display = None

    def get_cursor_position(self) -> tuple[int, int]:
        """Return the cursor coordinates relative to the root window."""
        root_return = ctypes.c_ulong()
        child_return = ctypes.c_ulong()
        root_x = ctypes.c_int()
        root_y = ctypes.c_int()
        win_x = ctypes.c_int()
        win_y = ctypes.c_int()
        mask_return = ctypes.c_uint()

        success = self.x11.XQueryPointer(
            self.display,
            self.root_window,
            ctypes.byref(root_return),
            ctypes.byref(child_return),
            ctypes.byref(root_x),
            ctypes.byref(root_y),
            ctypes.byref(win_x),
            ctypes.byref(win_y),
            ctypes.byref(mask_return),
        )
        if not success:
            raise RuntimeError("XQueryPointer failed.")
        return root_x.value, root_y.value

    def get_pixel(self, x: int, y: int) -> RGB:
        """Read the pixel at the given coordinates."""
        all_planes = ctypes.c_ulong(~0).value
        z_pixmap = 2

        image = self.x11.XGetImage(
            self.display,
            self.root_window,
            x,
            y,
            1,
            1,
            all_planes,
            z_pixmap,
        )
        if not image:
            raise RuntimeError("XGetImage failed.")

        try:
            pixel_value = int(self.x11.XGetPixel(image, 0, 0))
        finally:
            self.x11.XDestroyImage(image)
            self.x11.XFlush(self.display)

        return rgb_from_x11_pixel(pixel_value)


class POINT(ctypes.Structure):
    """Win32 POINT structure."""

    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class WindowsPixelReader:
    """Read pixels and cursor position using Win32 APIs."""

    CLR_INVALID = 0xFFFFFFFF

    def __init__(self) -> None:
        self.user32 = ctypes.windll.user32
        self.gdi32 = ctypes.windll.gdi32

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
    return X11PixelReader()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print the hex color code of the pixel under the mouse cursor "
            "(Windows and X11)."
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
    return parser.parse_args(argv)


def format_output(x: int, y: int, color: RGB) -> str:
    """Format a single output line."""
    return f"x={x:4d} y={y:4d} rgb=({color.r:3d},{color.g:3d},{color.b:3d}) hex={color.to_hex()}"


def run(interval: float, once: bool) -> int:
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


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    return run(args.interval, args.once)


if __name__ == "__main__":
    raise SystemExit(main())
