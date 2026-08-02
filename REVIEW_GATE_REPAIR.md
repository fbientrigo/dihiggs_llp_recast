# strong-bm1 review-gate repair (2026-08-02)

- Initial HEAD: `e1d0d42f16d12bf571a57833aa9f5b60d2a5180c` (detached).
- Submodule diagnosis: `external/recastingCodes/.git` was absent, so its Git
  commands resolved to the parent worktree.  The remote initialization made an
  empty clone; the pinned object was fetched from the existing local checkout.
  The initialized submodule is clean at `d4047c744062094c9f88e507bb1ccf69e9fe88d6`,
  matching the parent gitlink.
- SLHA whitespace: `.gitattributes` disables whitespace checking only for the
  canonical source/generated SLHA paths.  Source SHA-256 remains
  `ee6e68881322ea4d89c2d60614437fcad12ef28c3bda0647f472e2a84020325a`;
  generated SHA-256 remains
  `1a92f7cdd65932b2b2d0527d59b1eb151a76763f800b769330e3c4f06f46b009`.
- Other diff-check findings were non-semantic whitespace in `bm1.cmnd`,
  `run_card.dat`, and generated SVG wrapping.  The first two now record that
  normalization in provenance; SVG output is trimmed deterministically.
  Physics tokens and all reported numerical claims are unchanged.
- Validation: focused pytest `43 passed`; full pytest `50 passed`; focused and
  repository Ruff both passed.  Regeneration was byte-identical on a second
  run and did not invoke event generation.  Portable and optional source
  checksum manifests both passed.  JSON and canonical CSV parsing passed.
- Visual review: cutflow separates authors/ours, omits absent ATLAS points,
  and has a valid ratio panel; ratio and cross-section plots have correct signs,
  units, and benchmark-specific labels.  No errors, pulls, or broad claims.
- Remaining limitation: this validates only the frozen upstream strong-bm1
  benchmark; no new event generation or model adaptation was performed.
