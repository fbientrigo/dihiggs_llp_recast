import os
import glob
import subprocess
import gzip
from pathlib import Path

def main():
    prod_dir = "/home/fabi/atlas_dihiggs/_worktrees/r13-reduced-direct-production-validation/results/r13_reduced_direct_validation/production/"
        
    print("Relabeling LHE files...")
    relabel_dir = "/home/fabi/atlas_dihiggs/_worktrees/r13-reduced-direct-recast-validation/results/r13_reduced_direct_validation/relabeled_lhes"
    os.makedirs(relabel_dir, exist_ok=True)
    
    lhe_map = {}
    for lhe_path in glob.glob(f"{prod_dir}/*/*/unweighted_events.lhe.gz"):
        parts = lhe_path.split("/")
        g_dir = parts[-3]
        run_dir = parts[-2]
        
        out_name = f"{g_dir}_{run_dir}_pdg35.lhe.gz"
        out_path = os.path.join(relabel_dir, out_name)
        
        with gzip.open(lhe_path, 'rt') as f_in, gzip.open(out_path, 'wt') as f_out:
            for line in f_in:
                if line.lstrip().startswith("9000006"):
                    line = line.replace("9000006", "35", 1)
                f_out.write(line)
        lhe_map[f"{g_dir}_{run_dir}"] = out_path

    print("Generating Pythia cards...")
    cards_dir = "/home/fabi/atlas_dihiggs/_worktrees/r13-reduced-direct-recast-validation/cards/r13_reduced_direct_validation"
    os.makedirs(cards_dir, exist_ok=True)
    
    g_vals = [("g40", 40.0), ("g63p591425", 63.59142520075966), ("g300", 300.0)]
    ctau_vals = [("ctau_0p3mm", 0.3), ("ctau_1mm", 1.0), ("ctau_4p326mm", 4.326221529733112), ("ctau_30mm", 30.0), ("ctau_300mm", 300.0), ("ctau_1000mm", 1000.0)]
    runs = [("run_01", 1), ("run_02", 2)]
    
    template = """! Pythia8 config for R13 recast
Main:numberOfEvents = 1000
Main:timesAllowErrors = 3
Init:showChangedSettings = on
Init:showChangedParticleData = off
Next:numberCount = 5000
Next:numberShowInfo = 0
Next:numberShowProcess = 0
Next:numberShowEvent = 0

Random:setSeed = on
Random:seed = {seed}

PartonLevel:MPI = off
PartonLevel:ISR = on
PartonLevel:FSR = on
HadronLevel:Hadronize = on
Tune:pp = 21

Higgs:useBSM = on
35:m0 = 50.0
35:mMin = 20.0
35:tauCalc = off
35:tau0 = {ctau_mm}
35:onMode = off
35:onIfMatch = 5 -5

Recast:llpPdgIds = {{35}}
Recast:llpTau0 = {ctau_mm}
LesHouches:setLifetime = 2

Beams:frameType = 4
LHEFInputs:nSubruns = 1
Main:subrun = 0
Beams:LHEF = {lhe_path}
"""
    
    for g_idx, (g_tag, g_val) in enumerate(g_vals):
        for ctau_idx, (ctau_tag, ctau_val) in enumerate(ctau_vals):
            for run_tag, run_idx_val in runs:
                pythia_seed = 230000 + g_idx * 1000 + ctau_idx * 10 + run_idx_val
                
                lhe_path = lhe_map.get(f"{g_tag}_{run_tag}")
                
                card_content = template.format(seed=pythia_seed, lhe_path=lhe_path, ctau_mm=ctau_val)
                card_name = f"{g_tag}_{ctau_tag}_{run_tag}.cmnd"
                with open(os.path.join(cards_dir, card_name), "w") as f:
                    f.write(card_content)
                    
    print("Ready for execution!")

if __name__ == "__main__":
    main()
