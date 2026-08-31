# Higher-mass LHE input-compatibility contract

An existing LHE may be reused for this response study only when its recorded
provenance establishes all of the following:

1. The intended topology is H2 pair production compatible with the study
   (`g g > H > h2 h2`, with the same analysis interpretation).
2. The H2 mass in the LHE is exactly the requested response mass.
3. H2 is stable at LHE level and can be handed to the validated forced-decay
   Pythia configuration.
4. The event count is sufficient for the response, or the lower statistics are
   explicitly recorded.
5. Generator version, process, run configuration, seeds/run IDs, and source
   provenance are known, with hashes where available.
6. No undocumented change alters the recast or analysis semantics.

Filename similarity is not evidence of compatibility. A mass mismatch, an
unrecorded production configuration, or an input that is only a lifetime scan
is a rejection for this mission.
