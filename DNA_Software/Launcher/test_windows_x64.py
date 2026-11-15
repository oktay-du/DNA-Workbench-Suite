"""Check that the Windows x64 launcher and its Core pins stay AMD64."""

import json
from pathlib import Path
import struct
import sys
import unittest


AMD64 = 0x8664


def machine(binary):
    if binary[:2] != b"MZ" or len(binary) < 64:
        raise ValueError("Missing DOS executable header")
    offset = struct.unpack_from("<I", binary, 0x3C)[0]
    if offset + 6 > len(binary) or binary[offset : offset + 4] != b"PE\x00\x00":
        raise ValueError("Missing PE signature")
    return struct.unpack_from("<H", binary, offset + 4)[0]


class WindowsX64Tests(unittest.TestCase):
    def test_core_pins_are_x64(self):
        items = {
            row["id"]: row
            for row in json.loads(
                (Path(__file__).parent / "install-lock.json").read_text(encoding="utf-8")
            )["items"]
        }
        python = items["python-windows"]
        self.assertIn("x86_64-pc-windows-msvc", python["name"])
        self.assertIn("windows-x86_64", python["target"])
        self.assertNotIn("aarch64", python["url"].lower())
        self.assertIn(".x64.cab", items["webview2-runtime"]["name"])

    def test_machine_reads_coff_value_and_rejects_truncation(self):
        data = bytearray(70)
        data[:2] = b"MZ"
        struct.pack_into("<I", data, 0x3C, 64)
        data[64:68] = b"PE\x00\x00"
        struct.pack_into("<H", data, 68, AMD64)
        self.assertEqual(machine(data), AMD64)
        with self.assertRaises(ValueError):
            machine(data[:-1])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for argument in sys.argv[1:]:
            path = Path(argument)
            actual = machine(path.read_bytes())
            if actual != AMD64:
                raise SystemExit(
                    f"{path.name}: expected AMD64, found PE machine {actual:#06x}"
                )
            print(f"{path.name}: AMD64 PE")
    else:
        unittest.main()
