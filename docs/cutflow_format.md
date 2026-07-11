# Cutflow interchange format

Reference and observed cutflows use a minimal CSV contract:

```csv
cut,count
all_events,10000
trigger,7350
displaced_vertex,412
```

Cut names must be unique and identical between files. Counts may be integer or weighted floating-point yields but must be non-negative.

Compare two files with:

```bash
python scripts/compare_cutflows.py \
  --reference results/reference.csv \
  --observed results/observed.csv \
  --out results/comparison.json
```

The default engineering gate uses 20% relative tolerance for reference counts of at least 10 and an absolute tolerance of 3 for lower counts. Override these values explicitly when the reference publication or statistical treatment requires different thresholds.
