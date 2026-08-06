import json
import os
import glob
import hashlib
import subprocess
import re
import sys
from dataclasses import asdict

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from dvrecast.r8_cutflow import parse_recast_log
from dvrecast.r12_scan import derive_pythia_seed

def file_sha256(filepath):
    if not os.path.exists(filepath):
        return None
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def get_parser_commit():
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()
    except:
        return "UNKNOWN"

def build_evidence():
    worktree = "/home/fabi/atlas_dihiggs/_worktrees/r12-madgraph-per-g-recast-grid"
    logs_dir = os.path.join(worktree, "results/r12_madgraph_per_g_scan/recast_logs")
    evidence_dir = os.path.join(worktree, "results/r12_madgraph_per_g_scan/run_evidence")
    cards_dir = os.path.join(worktree, "cards/r12_madgraph_per_g_scan")
    
    os.makedirs(evidence_dir, exist_ok=True)
    
    parser_commit = get_parser_commit()
    
    logs = glob.glob(os.path.join(logs_dir, "*.log"))
    
    # Map G strings to float
    g_map = {
        "g40": 40.0,
        "g63p591425": 63.59142520075966,
        "g100": 100.0,
        "g150": 150.0,
        "g205p092725": 205.09272542237372,
        "g300": 300.0
    }
    g_idx_map = {
        "g40": 0, "g63p591425": 1, "g100": 2, "g150": 3, "g205p092725": 4, "g300": 5
    }
    
    # Map CTAU strings to float
    ctau_map = {
        "ctau_0p3mm": 0.3,
        "ctau_1mm": 1.0,
        "ctau_3mm": 3.0,
        "ctau_4p326mm": 4.326221529733112,
        "ctau_10mm": 10.0,
        "ctau_30mm": 30.0,
        "ctau_100mm": 100.0,
        "ctau_200mm": 200.0,
        "ctau_300mm": 300.0,
        "ctau_500mm": 500.0,
        "ctau_700mm": 700.0,
        "ctau_1000mm": 1000.0
    }
    ctau_idx_map = list(ctau_map.keys())
    
    runs = 0
    for log_path in logs:
        filename = os.path.basename(log_path)
        m = re.match(r"(g[0-9p]+)_(ctau_[0-9p]+mm)_(run_0[12]).log", filename)
        if not m:
            print(f"Skipping {filename}")
            continue
        g_tag, ctau_tag, run_tag = m.groups()
        g_val = g_map[g_tag]
        ctau_val = ctau_map[ctau_tag]
        
        run_idx = 0 if run_tag == "run_01" else 1
        g_idx = g_idx_map[g_tag]
        ctau_idx = ctau_idx_map.index(ctau_tag)
        
        pythia_seed = derive_pythia_seed(g_idx, ctau_idx, run_idx)
        
        with open(log_path, 'r') as f:
            log_text = f.read()
            
        try:
            parsed = parse_recast_log(log_text)
        except Exception as e:
            print(f"Failed to parse {filename}: {e}")
            parsed = None
        
        # authoritative lines
        auth_lines = []
        for line in log_text.splitlines():
            if any(k in line for k in ["Trackless Acc", "High-pT Acc", "All Events", "The inclusive cross section"]):
                auth_lines.append(line.strip())
        
        card_rel_path = f"cards/r12_madgraph_per_g_scan/{g_tag}/{ctau_tag}/{run_tag}.cmnd"
        card_full_path = os.path.join(worktree, card_rel_path)
        
        status = "PARSED" if parsed else "FAILED"
        
        if parsed:
            n_events = parsed.n_events
            trackless_acc_count = parsed.regions["Trackless"].acc
            trackless_acc_x_eff = parsed.regions["Trackless"].acc_x_eff
            highpt_acc_count = parsed.regions["High-pT"].acc
            highpt_acc_x_eff = parsed.regions["High-pT"].acc_x_eff
            
            data = {
                "g_hH2H2_GeV": g_val,
                "ctau_mm": ctau_val,
                "production_run": run_tag,
                "pythia_seed": pythia_seed,
                "n_events": n_events,
                "zero_llp_events": parsed.zero_llp_events,
                "trackless_acc_count": trackless_acc_count,
                "trackless_acc_x_eff": trackless_acc_x_eff,
                "trackless_raw_acceptance": trackless_acc_count / n_events if n_events else 0.0,
                "trackless_Aeff_weighted": trackless_acc_x_eff / n_events if n_events else 0.0,
                "highpt_acc_count": highpt_acc_count,
                "highpt_acc_x_eff": highpt_acc_x_eff,
                "trackless_stage_counts": parsed.regions["Trackless"].stage_counts,
                "trackless_stage_percentages": parsed.regions["Trackless"].stage_pct,
                "inclusive_cross_section_mb": parsed.inclusive_cross_section_mb,
                "authoritative_cutflow_lines": auth_lines,
                "full_log_sha256": file_sha256(log_path),
                "card_sha256": file_sha256(card_full_path),
                "card_path": card_rel_path,
                "parse_status": status,
                "parser_commit": parser_commit
            }
        else:
            data = {
                "g_hH2H2_GeV": g_val,
                "ctau_mm": ctau_val,
                "production_run": run_tag,
                "pythia_seed": pythia_seed,
                "parse_status": status,
                "full_log_sha256": file_sha256(log_path),
                "card_sha256": file_sha256(card_full_path),
                "card_path": card_rel_path,
                "parser_commit": parser_commit
            }
            
        out_name = f"{g_tag}_{ctau_tag}_{run_tag}.json"
        out_path = os.path.join(evidence_dir, out_name)
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)
            
        runs += 1

    print(f"Processed {runs} logs")

if __name__ == '__main__':
    build_evidence()
