import network_io

"""Download public-domain land outlines only; no personal information sent."""
from pathlib import Path
import zipfile, io, struct, json, hashlib

url = "https://naturalearth.s3.amazonaws.com/110m_physical/ne_110m_land.zip"
data = network_io.open_https(url, timeout=90).read()
z = zipfile.ZipFile(io.BytesIO(data))
shp = z.read(next(n for n in z.namelist() if n.endswith(".shp")))
offset = 100
rings = []
while offset < len(shp):
    _, length = struct.unpack_from(">ii", shp, offset)
    record = shp[offset + 8 : offset + 8 + length * 2]
    offset += 8 + length * 2
    if struct.unpack_from("<i", record)[0] != 5:
        continue
    parts, count = struct.unpack_from("<ii", record, 36)
    indices = list(struct.unpack_from("<" + "i" * parts, record, 44)) + [count]
    start = 44 + 4 * parts
    points = [
        list(struct.unpack_from("<dd", record, start + i * 16)) for i in range(count)
    ]
    rings += [
        [[round(x, 3), round(y, 3)] for x, y in points[indices[i] : indices[i + 1]]]
        for i in range(parts)
    ]
out = Path(__file__).with_name("world-land.json")
out.write_text(
    json.dumps(
        {
            "rings": rings,
            "source": url,
            "license": "Natural Earth public domain",
            "archive_sha256": hashlib.sha256(data).hexdigest(),
        },
        separators=(",", ":"),
    ),
    encoding="utf-8",
)
print("Offline-Weltkarte:", len(rings), "Polygone,", out.stat().st_size, "Bytes")
