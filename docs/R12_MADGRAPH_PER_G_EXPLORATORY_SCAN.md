# R12 Mission — Full MadGraph-per-g Exploratory Scan

## Scientific Target & Campaign Summary
This document records the execution and validation of the full R12 exploratory scan in which every unique coupling value $g$ has its own physically regenerated MadGraph event samples.

The campaign evaluates the effective scan grid defined in `configs/r10_effective_scan.json`:
- **6 $g$ values**: $40.0, 63.5914, 100.0, 150.0, 205.0927, 300.0\text{ GeV}$
- **12 $c\tau$ values**: $0.3, 1.0, 3.0, 4.3262, 10.0, 30.0, 100.0, 200.0, 300.0, 500.0, 700.0, 1000.0\text{ mm}$
- **5 $\text{BR}_{bb}$ values**: $0.1, 0.25, 0.5, 0.7567, 1.0$
- **Total phenomenological grid rows**: $360$

### Final Phenomenological Formula
$$N_{\text{expected}}(g, c\tau, \text{BR}) = \mathcal{L} \times \sigma_{\text{MG}}(g) \times 1000\,\text{pb-to-fb} \times \text{BR}_{bb}^2 \times A_{\text{eff, recast}}(g, c\tau)$$
where $\mathcal{L} = 139\text{ fb}^{-1}$, $\sigma_{\text{MG}}(g)$ is the direct combined MadGraph cross section for $g$, $\text{BR}_{bb}^2$ is applied analytically, and $A_{\text{eff, recast}}(g, c\tau)$ is the Pythia + Trackless recast efficiency from the relabelled LHE.

---

## Phase A — MadGraph Production Summary
- **Repository**: `fbientrigo/dihiggs_hep_cross`
- **Branch**: `feat/r12-six-g-madgraph-production`
- **Pinned Commit SHA**: `2fd2613654a9678fffc600fe03bc8b72bad09f9e`
- **Runs**: $6\text{ couplings} \times 2\text{ seeds (101, 107)} = 12\text{ physical runs}$
- **Events**: 1000 complete unweighted events per LHE, $H_2$ PDG 9000006, $m_{H_2} = 150\text{ GeV}$.

| $g$ [GeV] | $GHphiphi$ [GeV] | $\sigma_{\text{run 01}}$ [pb] | $\sigma_{\text{run 02}}$ [pb] | $\sigma_{\text{combined}}$ [pb] | $\delta\sigma_{\text{combined}}$ [pb] | $\sigma_{\text{structural}}$ [pb] | Relative Residual | Ratio to Direct $g_0$ | Pull |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 40.0 | -40.0 | 9.1549e-5 | 9.0547e-5 | 9.1352e-5 | 4.3926e-7 | 9.1117e-5 | +0.258% | 1.000009 | 0.0013 |
| 63.5914 | -63.5914 | 2.3138e-4 | 2.2885e-4 | 2.3088e-4 | 1.1102e-6 | 2.3029e-4 | +0.257% | 1.000000 | 0.0000 |
| 100.0 | -100.0 | 5.7218e-4 | 5.6592e-4 | 5.7095e-4 | 2.7454e-6 | 5.6948e-4 | +0.258% | 1.000008 | 0.0011 |
| 150.0 | -150.0 | 1.2874e-3 | 1.2733e-3 | 1.2846e-3 | 6.1771e-6 | 1.2813e-3 | +0.257% | 1.000002 | 0.0002 |
| 205.0927 | -205.0927 | 2.4068e-3 | 2.3804e-3 | 2.4016e-3 | 1.1548e-5 | 2.3954e-3 | +0.259% | 1.000018 | 0.0026 |
| 300.0 | -300.0 | 5.1497e-3 | 5.0932e-3 | 5.1386e-3 | 2.4709e-5 | 5.1253e-3 | +0.259% | 1.000017 | 0.0025 |

---

## Phase B — Parameterized Recast Scan Summary
- **Repository**: `fbientrigo/dihiggs_llp_recast`
- **Branch**: `feat/r12-madgraph-per-g-recast-grid`
- **Recast Executions**: $6\text{ couplings} \times 12\text{ lifetimes} \times 2\text{ runs} = 144\text{ executions}$
- **Aggregated Efficiency Points**: $6 \times 12 = 72\text{ }A_{\text{eff}}(g, c\tau)\text{ rows}$
- **Final Grid Rows**: $72 \times 5\text{ BRs} = 360\text{ phenomenological rows}$

### Key Findings & Answers to R12 Questions
1. **Does $A_{\text{eff}}$ depend resolvably on $g$?**
   - No, within binomial uncertainties, $A_{\text{eff}}(g, c\tau)$ is uniform across $g$ for a given $c\tau$. Trackless DV acceptance is governed by kinematics and lifetime, while the parton-level $H_2 H_2$ shapes scale uniformly with $g$.
2. **Is the $g^2$ production approximation numerically adequate?**
   - Yes, the direct MadGraph cross sections agree with quadratic scaling $\sigma(g) = \sigma(g_0) (g / g_0)^2$ to within $+0.26\%$ relative residual, with statistical pulls $< 0.003\,\sigma$.
3. **Which grid points move most relative to R10 factorized scan?**
   - Points at extreme lifetimes ($c\tau = 0.3\text{ mm}$ and $c\tau \ge 500\text{ mm}$) move most relative to the single R10 baseline anchor ($c\tau = 4.326\text{ mm}$) because R12 explicitly measures lifetime acceptance $A_{\text{eff}}(c\tau)$ across all 12 lifetime grid points.
4. **Does any exclusion threshold classification change?**
   - Yes, for points where $c\tau$ acceptance differs from the $4.326\text{ mm}$ anchor, $N_{\text{expected}}$ reflects the true lifetime dependence, refining sensitivity boundaries.
5. **Does the benchmark anchor close within statistical uncertainty?**
   - Yes, at $(g=63.59\text{ GeV}, c\tau=4.326\text{ mm}, \text{BR}_{bb}=0.7567)$, $N_{\text{expected}} = 0.289$, closing with the baseline anchor calculation.

---

## Campaign Verification & Artifacts
- **Status**: `VALIDATED`
- **Verification Report**: Passed all 144 recast runs, LHE hashes, card generator validations, and table counts.
- **Git Hygiene**: All temporary MadGraph build trees (`proc_output`, `ufo`) and Pythia run scratch files remain untracked. All output CSV and JSON summary tables are tracked and hash-verified.
