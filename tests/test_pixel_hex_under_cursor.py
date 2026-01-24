import unittest

from pixel_hex_under_cursor import RGB, clamp_channel, format_output, rgb_from_pixel


class PixelHexTests(unittest.TestCase):
    def test_rgb_to_hex(self) -> None:
        self.assertEqual(RGB(26, 43, 60).to_hex(), "#1a2b3c")

    def test_clamp_channel_bounds(self) -> None:
        self.assertEqual(clamp_channel(-10), 0)
        self.assertEqual(clamp_channel(512), 255)
        self.assertEqual(clamp_channel(128), 128)

    def test_rgb_from_pixel_extracts_channels(self) -> None:
        color = rgb_from_pixel(0x12_34_56)
        self.assertEqual(color, RGB(0x12, 0x34, 0x56))

    def test_format_output_contains_hex_and_coords(self) -> None:
        line = format_output(10, 20, RGB(1, 2, 3))
        self.assertIn("x=  10", line)
        self.assertIn("y=  20", line)
        self.assertIn("hex=#010203", line)


if __name__ == "__main__":
    unittest.main()
