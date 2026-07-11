# Validation contract

## Evidence required for every claimed result

- repository commit and dirty status;
- upstream commit;
- OS, compiler, Pythia8 and FastJet versions;
- exact command and input-card checksums;
- event count and random seeds;
- compact machine-readable cutflow;
- reference source and comparison method.

## Gate A — build

Pass when the frozen upstream executable builds and starts without missing headers, unresolved symbols or runtime-library failures.

## Gate B — upstream cutflow

Use the supplied upstream validation benchmark. The provisional numerical target is:

- each well-populated cutflow step within 20% relative difference;
- no unexplained step beyond 50%;
- low-statistics bins reported with absolute counts and statistical uncertainty rather than percentage alone.

These are engineering gates, not a substitute for the reference publication's uncertainty prescription. Any systematic offset must be understood before scalar adaptation.

## Gate C — regression after adaptation

After parameterizing the LLP identity or analysis mode, the original configuration must reproduce the Gate B result. A scalar feature may not silently alter the baseline path.

## Gate D — paper benchmark

Acceptance/efficiency validation and production cross-section validation are separate. A constant K-factor or luminosity scaling must never compensate for a cutflow mismatch.

## Status record

Every validation summary must declare exactly one state: `NOT_RUN`, `BLOCKED`, `FAILED`, `PROVISIONAL` or `VALIDATED`.
