import os
import subprocess
import glob
from pathlib import Path

def main():
    root = Path(__file__).resolve().parents[1]
    results_dir = root / "results/r13_reduced_direct_validation"
    logs_dir = results_dir / "recast_logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    recast_exec = Path("/home/fabi/atlas_dihiggs/_worktrees/r12-madgraph-per-g-recast-grid/results/upstream_build_patched/analysis/recast_2301_13866")
    
    # Run 1
    card_01 = root / "cards/r13_reduced_direct_validation/g63p591425_ctau_4p326mm_run_01.cmnd"
    log_01 = logs_dir / "g63p591425_ctau_4p326mm_run_01.log"
    print(f"Running {card_01}...")
    with open(log_01, "w") as f:
        subprocess.run([str(recast_exec), str(card_01)], stdout=f, stderr=subprocess.STDOUT)
        
    # Run 2
    card_02 = root / "cards/r13_reduced_direct_validation/g63p591425_ctau_4p326mm_run_02.cmnd"
    log_02 = logs_dir / "g63p591425_ctau_4p326mm_run_02.log"
    print(f"Running {card_02}...")
    with open(log_02, "w") as f:
        subprocess.run([str(recast_exec), str(card_02)], stdout=f, stderr=subprocess.STDOUT)
        
    print("Smoke test runs completed!")
    
if __name__ == "__main__":
    main()
