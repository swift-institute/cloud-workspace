#!/usr/bin/env python3
"""Reads clang/Swift serialized diagnostics (.dia, LLVM bitstream). Each source file the build compiles has its own
.dia, rewritten whenever that file is compiled again, so the union of a scratch path's .dia files is the current set
of diagnostics even after incremental builds that print nothing for unchanged files.

    read(path) -> [(severity, file, line, column, message, flag)]
"""
import struct

SEVERITY = {0: "ignored", 1: "note", 2: "warning", 3: "error", 4: "fatal", 5: "remark"}


class Bits:
    def __init__(self, data):
        self.data, self.pos = data, 0

    def read(self, width):
        value, done = 0, 0
        while done < width:
            byte = self.data[self.pos >> 3]
            offset = self.pos & 7
            take = min(8 - offset, width - done)
            value |= ((byte >> offset) & ((1 << take) - 1)) << done
            done += take
            self.pos += take
        return value

    def vbr(self, width):
        value, shift, high = 0, 0, 1 << (width - 1)
        while True:
            piece = self.read(width)
            value |= (piece & (high - 1)) << shift
            shift += width - 1
            if not piece & high:
                return value

    def align32(self):
        self.pos = (self.pos + 31) & ~31

    def at_end(self):
        return self.pos >= len(self.data) * 8


def _read_abbrev(bits):
    ops, n, i = [], bits.vbr(5), 0
    while i < n:
        literal = bits.read(1)
        if literal:
            ops.append(("lit", bits.vbr(8)))
        else:
            enc = bits.read(3)
            if enc in (1, 2):
                ops.append(("fixed" if enc == 1 else "vbr", bits.vbr(5)))
            else:
                ops.append({3: ("array", None), 4: ("char6", None), 5: ("blob", None)}[enc])
        i += 1
    return ops


def _scalar(bits, op):
    kind, w = op
    if kind == "lit":
        return w
    if kind == "fixed":
        return bits.read(w)
    if kind == "vbr":
        return bits.vbr(w)
    if kind == "char6":
        return bits.read(6)
    raise ValueError(kind)


def _read_record(bits, abbrev):
    values, blob, i = [], None, 0
    while i < len(abbrev):
        op = abbrev[i]
        if op[0] == "array":
            n = bits.vbr(6)
            element = abbrev[i + 1]
            values.extend(_scalar(bits, element) for _ in range(n))
            i += 2
            continue
        if op[0] == "blob":
            n = bits.vbr(6)
            bits.align32()
            start = bits.pos >> 3
            blob = bits.data[start:start + n]
            bits.pos += n * 8
            bits.align32()
        else:
            values.append(_scalar(bits, op))
        i += 1
    return values, blob


def records(data):
    """Yields (block_id, code, values, blob) for every record, depth first."""
    bits = Bits(data)
    if bits.read(32) != struct.unpack("<I", b"DIAG")[0]:
        raise ValueError("not a .dia file")
    blockinfo = {}
    stack = [(2, [], None)]  # (abbrev width, abbrevs, block id)
    current_bid = None
    while not bits.at_end():
        width, abbrevs, bid = stack[-1]
        if bits.pos + width > len(data) * 8:
            break
        code = bits.read(width)
        if code == 0:  # END_BLOCK
            bits.align32()
            stack.pop()
            if not stack:
                break
            continue
        if code == 1:  # ENTER_SUBBLOCK
            new_bid = bits.vbr(8)
            new_width = bits.vbr(4)
            bits.align32()
            bits.read(32)  # length in words
            stack.append((new_width, list(blockinfo.get(new_bid, [])), new_bid))
            continue
        if code == 2:  # DEFINE_ABBREV
            ab = _read_abbrev(bits)
            if bid == 0:
                blockinfo.setdefault(current_bid, []).append(ab)
            else:
                abbrevs.append(ab)
            continue
        if code == 3:  # UNABBREV_RECORD
            rcode = bits.vbr(6)
            n = bits.vbr(6)
            values = [bits.vbr(6) for _ in range(n)]
            if bid == 0 and rcode == 1:  # SETBID
                current_bid = values[0]
                continue
            yield bid, rcode, values, None
            continue
        ab = abbrevs[code - 4]
        values, blob = _read_record(bits, ab)
        rcode, values = values[0], values[1:]
        if bid == 0 and rcode == 1:
            current_bid = values[0]
            continue
        yield bid, rcode, values, blob


def read(path, fixits=False):
    """With fixits=True each entry gains a seventh element: [(file, start offset, end offset, replacement)]."""
    data = open(path, "rb").read()
    if len(data) < 4:
        return []
    files, flags, out = {}, {}, []
    for bid, code, values, blob in records(data):
        if code == 7 and blob is not None and out:  # FIXIT: range (file, line, col, offset) x2, text
            out[-1][6].append((values[0], values[3], values[7], blob.decode("utf8", "replace")))
            continue
        if code == 6 and blob is not None:  # FILENAME: id, size, mtime, name
            files[values[0]] = blob.decode("utf8", "replace")
        elif code == 4 and blob is not None:  # DIAG_FLAG: id, name
            flags[values[0]] = blob.decode("utf8", "replace")
        elif code == 2 and blob is not None:  # DIAG: severity, file, line, col, offset, category, flag, message
            sev, fid, line, col = values[0], values[1], values[2], values[3]
            flag = values[6] if len(values) > 6 else 0
            out.append((SEVERITY.get(sev, str(sev)), fid, line, col, blob.decode("utf8", "replace"), flag, []))
    if fixits:
        return [(s, files.get(f, ""), l, c, m, flags.get(fl, ""), [(files.get(x[0], ""), x[1], x[2], x[3]) for x in fx])
                for s, f, l, c, m, fl, fx in out]
    return [(s, files.get(f, ""), l, c, m, flags.get(fl, "")) for s, f, l, c, m, fl, fx in out]


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        for d in read(p):
            print(p, d)
