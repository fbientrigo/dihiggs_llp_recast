# Missing inputs for strong-bm1

Status: `NOT_REQUIRED_FOR_CANONICAL_RESULT`.

The upstream card `bm1.cmnd` names these inputs, none of which is distributed in the
frozen checkout:

```text
strong_0_2000_850_0p01.lhe.gz
strong_1_2000_850_0p01.lhe.gz
strong_2_2000_850_0p01.lhe.gz
```

They correspond to the 0-, 1-, and 2-additional-parton process cards. The upstream
reference log confirms that its original inputs were author-local files under
`pp2gogo_{0,1,2}/Events/run_01/unweighted_events.lhe.gz`.

MadGraph 3.5.3 is installed locally and its readiness probe passes. The exact parameter
or SLHA card used to generate run 01 is still not supplied. The only supplied upstream
source card is `GG_qqn1_2800_10_rpvLF_p01ns.slha`, which instead specifies 2800 GeV
and 10 GeV. The tracked 2000/850 GeV card is an independent reconstruction, not a
recovery of that private author input.

The canonical result freeze does not require these LHE files: it imports compact
run outputs, records the independent reconstruction card and seeds 201/202/203,
and regenerates only derived JSON and plots. A future new-generation campaign
remains a separate gate and must preserve its LHE inputs and event-level weights.
