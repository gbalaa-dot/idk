import unittest

from pixel_hex_under_cursor import (
    RGB,
    clamp_channel,
    classify_color,
    format_output,
    rgb_from_windows_colorref,
    rgb_from_x11_pixel,
)


class PixelHexTests(unittest.TestCase):
    def test_rgb_to_hex(self) -> None:
        self.assertEqual(RGB(26, 43, 60).to_hex(), "#1a2b3c")

    def test_clamp_channel_bounds(self) -> None:
        self.assertEqual(clamp_channel(-10), 0)
        self.assertEqual(clamp_channel(512), 255)
        self.assertEqual(clamp_channel(128), 128)

    def test_rgb_from_x11_pixel_extracts_channels(self) -> None:
        color = rgb_from_x11_pixel(0x12_34_56)
        self.assertEqual(color, RGB(0x12, 0x34, 0x56))

    def test_rgb_from_windows_colorref_extracts_channels(self) -> None:
        # COLORREF is 0x00bbggrr, so this should decode to r=0x11, g=0x22, b=0x33.
        color = rgb_from_windows_colorref(0x00_33_22_11)
        self.assertEqual(color, RGB(0x11, 0x22, 0x33))

    def test_classify_color_basic_ranges(self) -> None:
        self.assertEqual(classify_color(RGB(255, 0, 0)), "red")
        self.assertEqual(classify_color(RGB(0, 255, 0)), "green")
        self.assertEqual(classify_color(RGB(0, 0, 255)), "blue")
        self.assertEqual(classify_color(RGB(255, 255, 255)), "white")
        self.assertEqual(classify_color(RGB(10, 10, 10)), "black")

    def test_format_output_contains_hex_coords_and_color_name(self) -> None:
        line = format_output(10, 20, RGB(255, 0, 0))
        self.assertIn("x=  10", line)
        self.assertIn("y=  20", line)
        self.assertIn("hex=#ff0000", line)
        self.assertIn("color=red", line)


if __name__ == "__main__":
    unittest.main()
