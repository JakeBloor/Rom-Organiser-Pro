"""Builds PS3 PARAM.SFO files for tests."""

import struct


def make_sfo(entries):
    """A PARAM.SFO holding entries ({key: text}) in order."""
    keys = b""
    values = b""
    index = b""
    for key, text in entries.items():
        value = text.encode() + b"\0"
        index += struct.pack("<HHIII", len(keys), 0x0204, len(value), len(value), len(values))
        keys += key.encode() + b"\0"
        values += value
    key_table = 20 + len(index)
    data_table = key_table + len(keys)
    header = struct.pack("<4sIIII", b"\0PSF", 0x101, key_table, data_table, len(entries))
    return header + index + keys + values
