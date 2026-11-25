"""Merge translated batches (work/done/batch-NN.json, {id: Hebrew}) into translation/he/strings.json."""
import io, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(ROOT, 'translation', 'he', 'strings.json')
cur = json.load(io.open(out, encoding='utf-8')) if os.path.exists(out) else {}
for p in sys.argv[1:]:
    cur.update({k: v for k, v in json.load(io.open(p, encoding='utf-8')).items() if v})
    print('merged', p)
os.makedirs(os.path.dirname(out), exist_ok=True)
with io.open(out, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(dict(sorted(cur.items())), f, ensure_ascii=False, indent=1)
print(len(cur), 'strings')
