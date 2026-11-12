"""Check the compiled launcher, native loader and portable Python pins."""

import json
from pathlib import Path
import struct
import sys
import unittest


ARM64 = 0xAA64


def machine(binary):
    if binary[:2] != b"MZ" or len(binary) < 64:
        raise ValueError("Missing DOS executable header")
    offset = struct.unpack_from("<I", binary, 0x3C)[0]
    if offset + 6 > len(binary) or binary[offset : offset + 4] != b"PE\x00\x00":
        raise ValueError("Missing PE signature")
    return struct.unpack_from("<H", binary, offset + 4)[0]


class WindowsArm64Tests(unittest.TestCase):
    def test_arm64_core_pins_use_separate_downloads(self):
        folder = Path(__file__).parent
        arm = json.loads(
            (folder / "windows-arm64-packages.json").read_text(encoding="utf-8")
        )
        x64 = {
            row["id"]: row
            for row in json.loads(
                (folder / "install-lock.json").read_text(encoding="utf-8")
            )["items"]
        }
        for key, item in arm.items():
            self.assertNotEqual(item["expected_sha256"], x64[key]["expected_sha256"])
            self.assertRegex(item["expected_sha256"], r"^[a-f0-9]{64}$")
            self.assertNotEqual(item["relative_path"], x64[key]["relative_path"])
        self.assertIn("/Python-arm64/", arm["python-windows"]["target"])
        self.assertTrue(arm["ubuntu-wsl"]["url"].endswith("-arm64.wsl"))

    def test_machine_reads_coff_value_and_rejects_truncation(self):
        data = bytearray(70)
        data[:2] = b"MZ"
        struct.pack_into("<I", data, 0x3C, 64)
        data[64:68] = b"PE\x00\x00"
        struct.pack_into("<H", data, 68, ARM64)
        self.assertEqual(machine(data), ARM64)
        with self.assertRaises(ValueError):
            machine(data[:-1])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for argument in sys.argv[1:]:
            path = Path(argument)
            actual = machine(path.read_bytes())
            if actual != ARM64:
                raise SystemExit(
                    f"{path.name}: expected ARM64, found PE machine {actual:#06x}"
                )
            print(f"{path.name}: ARM64 PE")
    else:
        unittest.main()
