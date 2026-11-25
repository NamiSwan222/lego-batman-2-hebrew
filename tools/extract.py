"""Extract LEGO Batman 2's English text into work/en/*.json.

    python tools/extract.py [--game "<install>"]

- text.csv and the 117 cutscene CSVs: rows {id: "<file>|<LABEL>|<PLATFORM>", type, en} where the game reads
  the ENGLISH column (column 4; AMERICAN is column 5 and is translated the same).
- credits: english/american_credits.txt and levels/credits/credits.txt, one row per line.
Every file is also kept raw in work/en/raw/ for the build (the CSV layout is rebuilt from it).
"""
import argparse, csv, io, json, os
import ttdat

DEFAULT_GAME = r'D:\SteamLibrary\steamapps\common\LEGO Batman 2'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EN = os.path.join(ROOT, 'work', 'en')
DATS = ['GAME.DAT', 'GAME0.DAT', 'GAME1.DAT', 'GAME2.DAT']


def files(game):
    """{archive path: (dat file, entry)} for the text files we translate."""
    out = {}
    for dat in DATS:
        ix = ttdat.read_index(os.path.join(game, dat))
        for name, i in ix['paths'].items():
            if (name == 'stuff/text/text.csv' or (name.startswith('cut/') and name.endswith('.csv'))
                    or name.endswith('credits.txt') and 'audio' not in name):
                out[name] = (dat, ix['files'][i])
    return out


def read(game, dat, e):
    assert e['packed'] == e['size'] and e['flags'] & 0xff == 0, 'compressed file'
    with open(os.path.join(game, dat), 'rb') as f:
        f.seek(e['offset'])
        return f.read(e['size'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', default=DEFAULT_GAME)
    a = ap.parse_args()
    os.makedirs(os.path.join(EN, 'raw'), exist_ok=True)
    csv_rows, credit_rows = [], []
    for name, (dat, e) in sorted(files(a.game).items()):
        data = read(a.game, dat, e)
        open(os.path.join(EN, 'raw', name.replace('/', '__')), 'wb').write(data)
        text = data.decode('utf-8-sig', 'replace')
        if name.endswith('.csv'):
            for r in csv.reader(io.StringIO(text, newline='')):
                if len(r) >= 4 and r[0] and r[0] != 'LABEL' and r[3].strip():
                    csv_rows.append({'id': f'{name}|{r[0]}|{r[1]}', 'type': r[2], 'en': r[3]})
        else:
            for n, line in enumerate(text.splitlines()):
                if line.strip():
                    credit_rows.append({'id': f'{name}|{n}', 'type': 'Credit', 'en': line})
    json.dump(csv_rows, open(os.path.join(EN, 'strings.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    json.dump(credit_rows, open(os.path.join(EN, 'credits.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(len(csv_rows), 'csv strings,', len(credit_rows), 'credit lines')


if __name__ == '__main__':
    main()
