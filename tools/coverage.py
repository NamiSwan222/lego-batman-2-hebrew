"""Coverage check for LEGO Batman 2: every English string needs Hebrew with the same game codes.

    python tools/coverage.py

Codes: [[BUTTON]] tags, %s/%d/%i/%.1f%% numbers, ~N colour codes and ~~, and line breaks (count).
Strings without letters count as done. Credits: see tools/credits.py (names and licences stay Latin).
"""
import collections, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE = re.compile(r'\[\[[^\]]*\]\]|\[[A-Z_]+\]|%[0-9.]*[a-z]|%%|~[^~]|~~')
HEB = re.compile(r'[֐-׿]')


def main():
    en = json.load(open(os.path.join(ROOT, 'work', 'en', 'strings.json'), encoding='utf-8'))
    p = os.path.join(ROOT, 'translation', 'he', 'strings.json')
    he = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
    kp = os.path.join(ROOT, 'translation', 'keep.json')
    keep = set(json.load(open(kp)).get('ids', [])) if os.path.exists(kp) else set()
    done, missing, broken = 0, [], []
    for r in en:
        src = r['en']
        if not re.search(r'[A-Za-z]{2}', CODE.sub('', src)) or r['id'] in keep:
            done += 1
            continue
        h = he.get(r['id'])
        if not h:
            missing.append(r['id'])
        elif collections.Counter(CODE.findall(src)) != collections.Counter(CODE.findall(h)) or src.count('\n') != h.count('\n'):
            broken.append((r['id'], src, h))
        elif not HEB.search(h):
            broken.append((r['id'], src, h))
        else:
            done += 1
    for i, s, h in broken:
        print('BROKEN', i, repr(s), '->', repr(h))
    print(f'coverage: {done}/{len(en)} = {100 * done / len(en):.2f}%  missing {len(missing)}  broken {len(broken)}')
    sys.exit(0 if not missing and not broken else 1)


if __name__ == '__main__':
    main()
