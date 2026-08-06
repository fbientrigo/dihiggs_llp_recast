import os
import json
import hashlib
from pathlib import Path

def file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192): h.update(chunk)
    return h.hexdigest()

def main():
    root = Path(__file__).resolve().parents[1]
    results_dir = root / "results/r13_reduced_direct_validation"
    
    artifact_manifest = {"artifacts": {}}
    files = [
        "r13_efficiency_vs_g_ctau.csv", 
        "r13_effective_grid.csv", 
        "comparison_vs_r10.csv", 
        "comparison_vs_r12.csv",
        "result_summary.json",
        "verification_report.json",
        "FULL_EXECUTION_COMMANDS.md"
    ]
    
    for fname in files:
        fpath = results_dir / fname
        if fpath.exists():
            artifact_manifest["artifacts"][fname] = {"sha256": file_sha256(fpath)}
            
    with open(results_dir / "artifact_manifest.json", "w") as f:
        json.dump(artifact_manifest, f, indent=2)

if __name__ == "__main__":
    main()
