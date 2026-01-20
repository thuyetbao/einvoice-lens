#!/bin/python3

# External
import google_crc32c


def calculate_checksum_crc32c_on(path):
    crc = google_crc32c.Checksum()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            crc.update(chunk)
    return crc.digest().hex()
