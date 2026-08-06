import os
import glob
import subprocess
from pathlib import Path
from multiprocessing import Pool

def run_recast(card_path):
    root = Path(__file__).resolve().parents[1]
    recast_exec = Path("/home/fabi/atlas_dihiggs/_worktrees/r12-madgraph-per-g-recast-grid/results/upstream_build_patched/analysis/recast_2301_13866")
    logs_dir = root / "results/r13_reduced_direct_validation/recast_logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    log_path = logs_dir / (Path(card_path).stem + ".log")
    with open(log_path, "w") as f:
        subprocess.run([str(recast_exec), str(card_path)], stdout=f, stderr=subprocess.STDOUT)
    print(f"Finished {Path(card_path).name}")

def main():
    root = Path(__file__).resolve().parents[1]
    cards = glob.glob(str(root / "cards/r13_reduced_direct_validation/*.cmnd"))
    print(f"Found {len(cards)} cards. Starting pool with max_parallel=2...")
    with Pool(2) as p:
        p.map(run_recast, cards)
        
if __name__ == "__main__":
    main()
