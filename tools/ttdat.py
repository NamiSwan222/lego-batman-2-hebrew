"""Read the TT Games .DAT archive of LEGO Batman 2 (index version -4).

Ported from our LEGO Batman (2008) pack's ttdat.js (index version -2); same layout so far:
  file start: u32 indexOffset, u32 indexSize (+ "PakDat v1.01" id string)
  index: s32 version, u32 fileCount, fileCount x {u32 offset/256, u32 packedSize, u32 size, u32 flags},
         u32 nameCount, nameCount x {s16 next, u16 prev, u32 nameOffset}, u32 poolSize, name pool, ...
  Name entries form a tree (see ttdat.js): next > i: folder; else a file with file index -next.
"""
import struct

ALIGN = 256


def read_index(path):
    with open(path, 'rb') as f:
        raw, size = struct.unpack('<II', f.read(8))
        off = ((raw ^ 0xffffffff) * 256 + 0x100) if raw & 0x80000000 else raw
        f.seek(off)
        idx = f.read(size)
    version, count = struct.unpack_from('<iI', idx, 0)
    files, p = [], 8
    for _ in range(count):
        o, packed, sz, flags = struct.unpack_from('<IIII', idx, p)
        files.append(dict(entry_pos=off + p, offset=o * ALIGN, packed=packed, size=sz, flags=flags))
        p += 16
    ncount = struct.unpack_from('<I', idx, p)[0]
    p += 4
    ents = [struct.unpack_from('<hHI', idx, p + 8 * i) for i in range(ncount)]
    p += 8 * ncount
    pool = p + 4

    def name_at(o):
        e = idx.index(b'\0', pool + o)
        return idx[pool + o:e].decode('latin-1')
    parent, full, paths = [0] * ncount, [''] * ncount, {}
    for i in range(1, ncount):
        nxt, prev, no = ents[i]
        parent[i] = i - 1 if prev == 0 else parent[prev]
        full[i] = (full[parent[i]] + '/' if full[parent[i]] else '') + name_at(no)
        if not nxt > i:
            paths[full[i].lower()] = -nxt
    return dict(offset=off, size=size, version=version, files=files, paths=paths)


if __name__ == '__main__':
    import sys
    ix = read_index(sys.argv[1])
    print('version', ix['version'], len(ix['files']), 'files', len(ix['paths']), 'paths')
    for name, i in sorted(ix['paths'].items()):
        if any(k in name for k in sys.argv[2:]):
            f = ix['files'][i]
            print(name, i, f)
