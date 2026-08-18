import gzip
import struct
from pathlib import Path


TEMPLATE = Path(__file__).parents[1] / "assets" / "world_templates" / "1.21.1" / "level.dat"


def payload_end(data: bytes, tag: int, position: int) -> int:
    sizes = {1: 1, 2: 2, 3: 4, 4: 8, 5: 4, 6: 8}
    if tag in sizes:
        return position + sizes[tag]
    if tag == 7:
        return position + 4 + struct.unpack(">i", data[position:position + 4])[0]
    if tag == 8:
        return position + 2 + struct.unpack(">H", data[position:position + 2])[0]
    if tag == 9:
        child = data[position]
        count = struct.unpack(">i", data[position + 1:position + 5])[0]
        position += 5
        for _ in range(count):
            position = payload_end(data, child, position)
        return position
    if tag == 10:
        while data[position] != 0:
            child = data[position]
            name_size = struct.unpack(">H", data[position + 1:position + 3])[0]
            position = payload_end(data, child, position + 3 + name_size)
        return position + 1
    if tag == 11:
        return position + 4 + 4 * struct.unpack(">i", data[position:position + 4])[0]
    if tag == 12:
        return position + 4 + 8 * struct.unpack(">i", data[position:position + 4])[0]
    raise ValueError(f"Type NBT inconnu: {tag}")


def main() -> None:
    data = gzip.decompress(TEMPLATE.read_bytes())
    marker = b"\x0a\x00\x06Player"
    position = data.find(marker)
    if position >= 0:
        end = payload_end(data, 10, position + len(marker))
        data = data[:position] + data[end:]
    TEMPLATE.write_bytes(gzip.compress(data))


if __name__ == "__main__":
    main()
