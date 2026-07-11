# AGENTS.md

## Goal

Reproduce arXiv:2606.01681 through a validated public ATLAS DV+jets recast before adapting the workflow to the local 2HDM/DiHiggs model.

## Required order

1. Bootstrap the exact upstream revision from `configs/upstream.lock.json`.
2. Compile the upstream recast without modifying its physics logic.
3. Reproduce at least one upstream validation benchmark.
4. Record tool versions, commands, cards, revisions and compact outputs.
5. Only then parameterize the LLP PDG ID and original/modified analysis mode.
6. Reproduce one paper benchmark before any local 2HDM reinterpretation.

## Boundaries

- Treat `external/recastingCodes` as read-only.
- Put project-owned adaptations in `patches/`, `src/`, `scripts/`, `cards/` or a clearly documented fork layer.
- Do not commit LHE, HepMC, ROOT, generated UFO, local toolchains or bulk HEPData downloads.
- Never report a reproduced result without a manifest and an explicit comparison against the reference.
- Do not derive exclusion contours from an unvalidated cutflow.
- Prefer minimal, reversible changes over framework rewrites.

## Validation language

Use these states only:

- `NOT_RUN`: no execution evidence.
- `BLOCKED`: prerequisite missing.
- `FAILED`: execution completed but acceptance criteria failed.
- `PROVISIONAL`: broadly consistent but not fully closed.
- `VALIDATED`: all declared acceptance criteria passed.

## Local environment

Primary development target: Linux or WSL, with the repository stored in the Linux filesystem. External tools may be installed under `.local/`; outputs belong under `results/` or `data/` and remain untracked unless they are compact validation artifacts.
