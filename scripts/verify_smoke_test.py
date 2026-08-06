import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dvrecast.r8_cutflow import parse_recast_log
from dataclasses import asdict

root = Path(__file__).resolve().parents[1]
logs_dir = root / "results/r13_reduced_direct_validation/recast_logs"
log_01 = logs_dir / "g63p591425_ctau_4p326mm_run_01.log"

with open(log_01, "r") as f:
    res = parse_recast_log(f.read())
print(asdict(res))
