"""IPS writer and strict reader, with optional final-size extension."""
from fomt_text import FormatError


def create(source: bytes, target: bytes) -> bytes:
    if len(target) > 0x1000000:
        raise FormatError("IPS offsets limited to 24 bits; use BPS for larger builds")
    out = bytearray(b"PATCH")
    pos = 0
    while pos < len(target):
        if pos < len(source) and source[pos] == target[pos]:
            pos += 1
            continue
        start = pos
        # EOF is reserved as a record address; include its preceding byte instead.
        if start == 0x454F46:
            start -= 1
        stop = min(start + 65535, len(target))
        while pos < stop:
            pos += 1
            if pos < len(source) and source[pos:pos+8] == target[pos:pos+8]:
                break
        chunk = target[start:pos]
        # IPS RLE for uniform padding; retain literal records for everything else.
        if len(chunk) >= 4 and chunk.count(chunk[:1]) == len(chunk):
            out.extend(start.to_bytes(3, "big") + b"\0\0" + len(chunk).to_bytes(2, "big") + chunk[:1])
        else:
            out.extend(start.to_bytes(3, "big") + len(chunk).to_bytes(2, "big") + chunk)
    out.extend(b"EOF")
    # At exactly 16MiB, records extend the ROM to size; a 24-bit trailer
    # cannot express 0x1000000. All appended padding is represented in records.
    if len(target) < 0x1000000:
        out.extend(len(target).to_bytes(3, "big"))
    return bytes(out)


def apply(source: bytes, patch: bytes) -> bytes:
    if not patch.startswith(b"PATCH"):
        raise FormatError("not IPS")
    out = bytearray(source)
    p = 5
    while True:
        if p+3 > len(patch):
            raise FormatError("truncated IPS")
        if patch[p:p+3] == b"EOF":
            p += 3
            break
        addr = int.from_bytes(patch[p:p+3], "big")
        if p+5 > len(patch):
            raise FormatError("truncated IPS record")
        size = int.from_bytes(patch[p+3:p+5], "big")
        p += 5
        if size:
            if p+size > len(patch):
                raise FormatError("truncated IPS data")
            data = patch[p:p+size]
            p += size
        else:
            if p+3 > len(patch):
                raise FormatError("truncated IPS RLE")
            count = int.from_bytes(patch[p:p+2], "big")
            if count == 0:
                raise FormatError("zero IPS RLE size")
            data = patch[p+2:p+3]*count
            p += 3
        if addr+len(data) > len(out):
            out.extend(b"\0"*(addr+len(data)-len(out)))
        out[addr:addr+len(data)] = data
    if len(patch)-p == 3:
        size = int.from_bytes(patch[p:], "big")
        if size > len(out):
            out.extend(b"\0"*(size-len(out)))
        else:
            del out[size:]
    elif len(patch) != p:
        raise FormatError("unexpected IPS trailer")
    return bytes(out)
