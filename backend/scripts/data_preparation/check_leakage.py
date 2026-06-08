import json
from collections import Counter
from pathlib import Path

tags = Counter()
texts = set()
dupes = 0
total = 0

base_dir = Path(__file__).resolve().parent.parent.parent
dataset_path = base_dir / 'dataset' / 'processed' / 'unified_dataset_iob.jsonl'

with open(dataset_path) as f:
    for line in f:
        total += 1
        d = json.loads(line)
        tags.update(d.get('iob_tags', []))
        t = ' '.join(d.get('tokens', []))
        if t in texts:
            dupes += 1
        texts.add(t)

print(f"Total records: {total}")
print(f"Duplicates: {dupes}")
print(f"Unique texts: {len(texts)}")
print("Tag distribution:")
for k, v in tags.most_common():
    print(f"  {k}: {v}")
