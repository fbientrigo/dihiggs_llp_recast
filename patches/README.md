# Patches

Project-owned changes to the public recast belong here as reviewable patches against the commit in `configs/upstream.lock.json`.

The first allowed physics patch, after upstream validation, is limited to:

1. configurable LLP PDG IDs;
2. explicit original/modified analysis modes;
3. regression preservation of the upstream benchmark.

Do not edit `external/recastingCodes` in place or treat a dirty submodule checkout as a reproducible source.
