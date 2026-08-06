import os
import glob
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dvrecast.r8_cutflow import parse_recast_log
from dataclasses import asdict

def main():
    root = Path(__file__).resolve().parents[1]
    logs_dir = root / "results/r13_reduced_direct_validation/recast_logs"
    evidence_dir = root / "results/r13_reduced_direct_validation/run_evidence"
    os.makedirs(evidence_dir, exist_ok=True)
    
    for log_path in glob.glob(str(logs_dir / "*.log")):
        p = Path(log_path)
        name_parts = p.stem.split("_")
        
        g_tag = name_parts[0]
        g_val = 40.0
        if g_tag == "g63p591425": g_val = 63.59142520075966
        elif g_tag == "g300": g_val = 300.0
        
        ctau_tag = name_parts[1] + "_" + name_parts[2]
        ctau_val = 1.0
        if "0p3" in ctau_tag: ctau_val = 0.3
        elif "4p326" in ctau_tag: ctau_val = 4.326221529733112
        elif "300mm" in ctau_tag: ctau_val = 300.0
        elif "30mm" in ctau_tag: ctau_val = 30.0
        elif "1000mm" in ctau_tag: ctau_val = 1000.0
        
        run_tag = name_parts[3] + "_" + name_parts[4]
        
        try:
            with open(log_path, "r") as f:
                res = parse_recast_log(f.read())
            
            evidence = {
                "g_hH2H2_GeV": g_val,
                "ctau_mm": ctau_val,
                "production_run": run_tag,
                "parse_status": "PARSED",
                "n_events": res.n_events,
                "trackless_acc_count": res.regions["Trackless"].acc,
                "trackless_acc_x_eff": res.regions["Trackless"].acc_x_eff,
                "trackless_raw_acceptance": res.regions["Trackless"].acc / res.n_events if res.n_events > 0 else 0.0,
                "trackless_Aeff_weighted": res.regions["Trackless"].acc_x_eff / res.n_events if res.n_events > 0 else 0.0,
            }
        except Exception as e:
            evidence = {
                "g_hH2H2_GeV": g_val,
                "ctau_mm": ctau_val,
                "production_run": run_tag,
                "parse_status": "FAILED",
                "error": str(e)
            }
            
        with open(evidence_dir / (p.stem + ".json"), "w") as f:
            json.dump(evidence, f, indent=2)

    print("Evidence built.")

if __name__ == "__main__":
    main()
