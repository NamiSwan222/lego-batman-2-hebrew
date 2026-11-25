"""Build the Hebrew pack data for LEGO Batman 2.

    python tools/build.py [--allow-missing] [--width 40] [--break real|literal]

Writes work/pack/:
  GAME.DAT.append     appended to a copy of GAME.DAT by the launcher (make-pack `append` patch with output)
  files/tirgumim/he/GAME.DAT.overlay   index entries pointing the replaced files at the appended copies
  files/XINPUT1_3.dll the launcher-only proxy (tools/proxy)
Replaced files: stuff/text/text.csv, english/american_credits.txt (job titles and headings), the cutscene CSVs (ENGLISH and AMERICAN columns in Hebrew, visual order,
wrapped at --width characters) and gui/font/font_nxg.ft2 (27 Hebrew letters added).
"""
import argparse, csv, io, json, os, shutil, subprocess, sys
import ttdat

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, 'work')
GAME = r'D:\SteamLibrary\steamapps\common\LEGO Batman 2'
LIB = os.path.join(ROOT, 'tools', 'lib')


def node(script, payload):
    r = subprocess.run(['node', os.path.join(LIB, script)], input=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                       capture_output=True, check=True)
    return json.loads(r.stdout.decode('utf-8'))


def rebuild_csv(data, he):
    """Replace ENGLISH/AMERICAN cells of rows we have Hebrew for; keep every other byte of layout."""
    text = data.decode('utf-8')
    rows = list(csv.reader(io.StringIO(text, newline='')))
    out = io.StringIO()
    w = csv.writer(out, quoting=csv.QUOTE_ALL, lineterminator='\r\n')
    for r in rows:
        if not r:
            out.write('\r\n')
            continue
        if len(r) >= 5 and r[0] != 'LABEL':
            h = he.get(f'{r[0]}|{r[1]}')
            if h is not None:
                r[3] = r[4] = h
        w.writerow(r)
    return out.getvalue().encode('utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--allow-missing', action='store_true')
    ap.add_argument('--width', type=int, default=40)
    ap.add_argument('--break', dest='brk', choices=['real', 'literal'], default='real')
    ap.add_argument('--he', default=os.path.join(ROOT, 'translation', 'he', 'strings.json'))
    a = ap.parse_args()
    if not a.allow_missing and subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'coverage.py')]).returncode:
        sys.exit('coverage is not 100%: not building')
    he = json.load(open(a.he, encoding='utf-8'))
    visual = node('rtl_cli.js', {'maxWidth': a.width, 'lineBreak': '\n' if a.brk == 'real' else '\\n', 'strings': he})
    by_file = {}
    for k, v in visual.items():
        f, rest = k.split('|', 1)
        by_file.setdefault(f, {})[rest] = v
    dat = os.path.join(GAME, 'GAME.DAT')
    ix = ttdat.read_index(dat)
    replace = {}
    for f, items in by_file.items():
        e = ix['files'][ix['paths'][f]]
        with open(dat, 'rb') as fh:
            fh.seek(e['offset'])
            replace[f] = rebuild_csv(fh.read(e['size']), items)
    # credits: Hebrew job titles and headings; names, companies and dedications stay as they are
    cred = json.load(open(os.path.join(ROOT, 'translation', 'he', 'credits.json'), encoding='utf-8'))
    cvis = node('rtl_cli.js', {'maxWidth': 0, 'lineBreak': '\n', 'strings': cred})
    import re
    bom_bytes = bytes.fromhex('efbbbf')
    for f in ('stuff/text/english_credits.txt', 'stuff/text/american_credits.txt'):
        e = ix['files'][ix['paths'][f]]
        with open(dat, 'rb') as fh:
            fh.seek(e['offset'])
            raw = fh.read(e['size'])
        bom = raw.startswith(bom_bytes)
        text = raw.decode('utf-8-sig')
        text = re.sub(r'^(\s*(?:heading|title|company)\s+")([^"]*)(")', lambda m: m.group(1) + cvis.get(m.group(2), m.group(2)) + m.group(3), text, flags=re.M)
        replace[f] = (bom_bytes if bom else b'') + text.encode('utf-8')
    # font
    e = ix['files'][ix['paths']['gui/font/font_nxg.ft2']]
    with open(dat, 'rb') as fh:
        fh.seek(e['offset'])
        font = fh.read(e['size'])
    tmp = os.path.join(WORK, 'font_in.ft2')
    open(tmp, 'wb').write(font)
    used = sorted({ord(c) for v in visual.values() for c in v})
    subprocess.run(['node', '-e', (
        "const fs=require('fs');const ft2=require(process.argv[1]+'/ft2');const {renderGlyphs}=require(process.argv[1]+'/glyphs');"
        "const used=new Set(JSON.parse(process.argv[4]));"
        "fs.writeFileSync(process.argv[3],ft2.addGlyphs(fs.readFileSync(process.argv[2]),renderGlyphs(),used));"),
        LIB, tmp, os.path.join(WORK, 'font_out.ft2'), json.dumps(used)], check=True)
    replace['gui/font/font_nxg.ft2'] = open(os.path.join(WORK, 'font_out.ft2'), 'rb').read()
    # append + overlay
    size = os.path.getsize(dat)
    end = -(-size // ttdat.ALIGN) * ttdat.ALIGN
    chunks, overlay = [b'\0' * (end - size)], []
    for name, data in sorted(replace.items()):
        e = ix['files'][ix['paths'][name]]
        pad = -(-len(data) // ttdat.ALIGN) * ttdat.ALIGN
        chunks.append(data + b'\0' * (pad - len(data)))
        entry = bytearray(16)
        import struct
        struct.pack_into('<IIII', entry, 0, end // ttdat.ALIGN, len(data), len(data), e['flags'] & ~0xff)
        overlay.append((e['entry_pos'], bytes(entry)))
        end += pad
    pack = os.path.join(WORK, 'pack')
    shutil.rmtree(pack, ignore_errors=True)
    os.makedirs(os.path.join(pack, 'files', 'tirgumim', 'he'))
    open(os.path.join(pack, 'GAME.DAT.append'), 'wb').write(b''.join(chunks))
    with open(os.path.join(pack, 'files', 'tirgumim', 'he', 'GAME.DAT.overlay'), 'w', newline='\n') as f:
        f.write('TIRGUMIM-OVERLAY 1\n' + ''.join(f'{p} {d.hex()}\n' for p, d in overlay))
    shutil.copy(os.path.join(WORK, 'files', 'XINPUT1_3.dll'), os.path.join(pack, 'files', 'XINPUT1_3.dll'))
    print(len(replace), 'files replaced;', len(b''.join(chunks)), 'bytes appended')


if __name__ == '__main__':
    main()
