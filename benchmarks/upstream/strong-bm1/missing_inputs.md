# Missing inputs for strong-bm1

Status: `BLOCKED`.

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

MadGraph (`mg5_aMC`) is not installed locally. More importantly, the exact parameter
or SLHA card used to generate run 01 is not supplied. The filenames and reference event
record identify a 2000 GeV gluino, 850 GeV neutralino, and lifetime label `0p01`. The
only supplied strong-production SLHA card is
`GG_qqn1_2800_10_rpvLF_p01ns.slha`, which instead specifies 2800 GeV and 10 GeV.
It must not be substituted silently.

M2 can start only after the exact bm1 SLHA/generation configuration is recovered or
reconstructed and documented, MadGraph is installed in a separate task, and all three
10,000-event LHE samples are produced with recorded seeds and checksums. No event
generation was attempted during M1.
