# -*- coding: utf-8 -*-
# from https://github.com/lucagoc/iPixel-CLI

from logging import getLogger
from modules.bit_tools import *
from PIL import Image
import io
import os

logger = getLogger(__name__)

# Utility functions
def to_bool(value):
    """Convert a value to a boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.lower() in {"true", "1", "yes"}:
        return True
    if isinstance(value, str) and value.lower() in {"false", "0", "no"}:
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def to_int(value, name="parameter"):
    """Convert a value to an integer."""
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Invalid integer value for {name}: {value}")


def int_to_hex(n):
    """Convert an integer to a 2-character hexadecimal string."""
    return f"{n:02x}"


def validate_range(value, min_val, max_val, name):
    """Validate that a value is within a specific range."""
    if not min_val <= value <= max_val:
        raise ValueError(f"{name} must be between {min_val} and {max_val}")

def clear():
    """Clear the EEPROM."""
    return bytes.fromhex("04000380")


def set_brightness(value):
    """Set the brightness of the device."""
    value = to_int(value, "brightness")
    validate_range(value, 0, 100, "Brightness")
    return bytes.fromhex("05000480") + bytes.fromhex(int_to_hex(value))

def led_off():
    """Turn the LED off."""
    return bytes.fromhex("0500070100")


def led_on():
    """Turn the LED on."""
    return bytes.fromhex("0500070101")

def send_animation(image: Image.Image):
    """Send a GIF animation to the device."""
    if isinstance(image, Image.Image):
        buf = io.BytesIO()
        # Preserve animation if present
        save_kwargs = {"format": "GIF"}
        image.save(buf, **save_kwargs)
        buf.seek(0)
        hex_data = buf.read().hex()

    checksum = CRC32_checksum(hex_data)
    size = get_frame_size(hex_data, 8)
    return bytes.fromhex(f"{get_frame_size('FFFF030000' + size + checksum + '0201' + hex_data, 4)}030000{size}{checksum}0201{hex_data}")


def delete_screen(n):
    """Delete a screen from the EEPROM."""
    return bytes.fromhex("070002010100") + bytes.fromhex(int_to_hex(to_int(n, "screen index")))
