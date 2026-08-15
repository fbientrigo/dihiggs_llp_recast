#!/usr/bin/env python3
"""Run isolated, resumable Trackless A x epsilon(mH,ctau) nodes.

This is deliberately a small bounded runner, not a scheduler.  It owns only
the mission directory passed on the command line, runs at most ``--workers``
independent nodes, and atomically updates one row per seed in grid_status.csv.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

RECAST = Path("/home/fabian/atlas_dihiggs/dihiggs_llp_recast/results/upstream_build_patched/analysis/recast_2301_13866")
GEOMETRY = Path("/home/fabian/atlas_dihiggs/dihiggs_llp_recast/results/r8_h2_model_derived_4b/bin/r8_geometry_driver")
REPO = Path("/home/fabian/atlas_dihiggs/dihiggs_llp_recast")
SRC = REPO / "src"
sys.path.insert(0, str(SRC))
from dvrecast.r8_cutflow import parse_recast_log  # noqa: E402
from dvrecast.r8_geometry import load_geometry_csv  # noqa: E402

SEEDS = (81001, 81002)
N_PER_SEED = 10000
STAGES = (
    "jet_selection_pct",
    "fiducial_pct",
    "r_vertex_gt_4mm_pct",
    "track_d0_gt_2mm_pct",
    "selected_decay_products_ge5_pct",
    "invariant_mass_gt_10gev_pct",
)
FIELDS = (
    "node_id", "mH_GeV", "ctau_mm", "seed", "N_requested", "N_processed",
    "status", "pid", "start_time", "end_time", "wall_seconds",
    "raw_selected", "weighted_numerator", "Aeff", "log_path", "card_path",
    "input_LHE", "input_sha256", "cutflow_path", "geometry_path",
    "peak_rss_kb", "error_path",
)

_status_lock = threading.Lock()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def ctau_tag(value: float) -> str:
    return f"{value:.16g}".replace(".", "p")


def node_id(mass: int, ctau: float) -> str:
    return f"mH{mass}_ctau{ctau_tag(ctau)}"


def input_for(mission: Path, mass: int, seed: int) -> Path:
    if mass == 150:
        return mission / "inputs" / f"relabelled_full_mH150_s{'101' if seed == 81001 else '107'}.lhe.gz"
    return REPO / "data/raw/mass_dependence_trackless" / f"relabelled_full_mH{mass}_s{'101' if seed == 81001 else '107'}.lhe.gz"


def parse_time_file(path: Path) -> tuple[float | None, int | None]:
    if not path.exists():
        return None, None
    text = path.read_text(errors="replace")
    m = re.search(r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): ([0-9:.]+)", text)
    wall = None
    if m:
        parts = m.group(1).split(":")
        if len(parts) == 3:
            wall = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        else:
            wall = int(parts[0]) * 60 + float(parts[1])
    rss = re.search(r"Maximum resident set size \(kbytes\): (\d+)", text)
    return wall, int(rss.group(1)) if rss else None


def load_status(path: Path) -> dict[tuple[str, int], dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="") as f:
        return {(r["node_id"], int(r["seed"])): r for r in csv.DictReader(f)}


def atomic_status(path: Path, rows: dict[tuple[str, int], dict[str, str]]) -> None:
    ordered = [rows[k] for k in sorted(rows, key=lambda x: (x[0], x[1]))]
    tmp = path.with_suffix(".csv.tmp")
    with tmp.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(ordered)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def update_row(status_path: Path, key: tuple[str, int], patch: dict[str, object]) -> None:
    with _status_lock:
        rows = load_status(status_path)
        row = rows[key]
        for k, v in patch.items():
            row[k] = "" if v is None else str(v)
        atomic_status(status_path, rows)


def make_card(path: Path, mass: int, ctau: float, seed: int, lhe: Path, lhe_hash: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = f"""! aeff_grid_mH_ctau mission node: mH={mass} GeV, ctau={ctau:.16g} mm
! canonical original/published Trackless mode; forced H2 -> bb; physical BR is downstream.
! LHE sha256: {lhe_hash}
Main:numberOfEvents = {N_PER_SEED}
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
35:m0 = {mass}.
35:mMin = 100.
35:tauCalc = off
35:tau0 = {ctau:.16g}
35:onMode = off
35:onIfMatch = 5 -5

Recast:llpPdgIds = {{35}}
Recast:llpTau0 = {ctau:.16g}
LesHouches:setLifetime = 2

Beams:frameType = 4
LHEFInputs:nSubruns = 1
Main:subrun = 0
Beams:LHEF = {lhe.resolve()}
"""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def valid_reuse(existing: dict[str, str], result_json: Path, log: Path, geom: Path,
                card: Path, mass: int, ctau: float, seed: int, input_hash: str) -> bool:
    """Reuse only a COMPLETE result whose identity and denominator still match."""
    if existing.get("status") != "COMPLETE" or not (result_json.exists() and log.exists() and geom.exists()):
        return False
    try:
        if int(existing.get("seed", "-1")) != seed or int(existing.get("mH_GeV", "-1")) != mass:
            return False
        if abs(float(existing.get("ctau_mm", "nan")) - ctau) > 1e-12:
            return False
        if int(existing.get("N_processed", "-1")) != N_PER_SEED or existing.get("input_sha256") != input_hash:
            return False
        payload = json.loads(result_json.read_text())
        if (payload.get("seed") != seed or payload.get("mH_GeV") != mass or
                abs(float(payload.get("ctau_mm", "nan")) - ctau) > 1e-12 or
                payload.get("N_processed") != N_PER_SEED or payload.get("input_sha256") != input_hash):
            return False
        card_path = Path(existing.get("card_path") or card)
        if not card_path.exists():
            return False
        card_text = card_path.read_text()
        required = (f"Main:numberOfEvents = {N_PER_SEED}", f"Random:seed = {seed}",
                    f"35:m0 = {mass}.", f"35:tau0 = {ctau:.16g}",
                    f"Recast:llpTau0 = {ctau:.16g}", "Recast:llpPdgIds = {35}")
        if any(token not in card_text for token in required):
            return False
        if "modified" in card_text.lower():
            return False
        parsed = parse_recast_log(log.read_text(errors="replace"))
        return parsed.n_events == N_PER_SEED
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        return False


def cutflow_csv(path: Path, result) -> None:
    tl = result.regions["Trackless"]
    hp = result.regions["High-pT"]
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["stage", "high_pt_count", "trackless_count", "high_pt_pct", "trackless_pct"])
        w.writerow(["events_processed", result.n_events, result.n_events, "", ""])
        w.writerow(["zero_configured_llp_events", result.zero_llp_events, result.zero_llp_events, "", ""])
        for stage in STAGES:
            w.writerow([stage, hp.stage_counts[stage], tl.stage_counts[stage], hp.stage_pct[stage], tl.stage_pct[stage]])
        w.writerow(["acc", hp.acc, tl.acc, hp.acc / result.n_events, tl.acc / result.n_events])
        w.writerow(["acc_x_eff", hp.acc_x_eff, tl.acc_x_eff, hp.acc_x_eff / result.n_events, tl.acc_x_eff / result.n_events])


def run_one(mission: Path, mass: int, ctau: float, seed: int, status_path: Path) -> dict[str, object]:
    nid = node_id(mass, ctau)
    seed_dir = mission / "nodes" / nid / f"seed_{seed}"
    seed_dir.mkdir(parents=True, exist_ok=True)
    card = mission / "cards" / nid / f"seed_{seed}.cmnd"
    log = seed_dir / "recast.log"
    geom_log = seed_dir / "geometry_driver.log"
    geom = seed_dir / "geometry.csv"
    cutflow = seed_dir / "cutflow.csv"
    result_json = seed_dir / "result.json"
    error_path = seed_dir / "error.txt"
    input_lhe = input_for(mission, mass, seed)
    input_hash = sha256(input_lhe)
    key = (nid, seed)

    existing = load_status(status_path).get(key, {})
    if valid_reuse(existing, result_json, log, geom, card, mass, ctau, seed, input_hash):
        return {"node_id": nid, "seed": seed, "status": "REUSED", "wall_seconds": float(existing.get("wall_seconds") or 0.0)}

    start = time.time()
    update_row(status_path, key, {"status": "RUNNING", "pid": os.getpid(), "start_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start)), "error_path": ""})
    try:
        if not input_lhe.exists():
            raise FileNotFoundError(input_lhe)
        make_card(card, mass, ctau, seed, input_lhe, input_hash)
        recast_time = seed_dir / "recast_time.txt"
        with log.open("w") as out:
            p = subprocess.Popen(["/usr/bin/time", "-v", "-o", str(recast_time), str(RECAST), str(card)], stdout=out, stderr=subprocess.STDOUT, cwd=RECAST.parent)
            update_row(status_path, key, {"pid": p.pid})
            rc = p.wait()
        if rc != 0:
            raise RuntimeError(f"recast exit code {rc}")
        result = parse_recast_log(log.read_text(errors="replace"))
        if result.n_events != N_PER_SEED:
            raise RuntimeError(f"denominator mismatch: parsed {result.n_events}, expected {N_PER_SEED}")

        geom_time = seed_dir / "geometry_time.txt"
        with geom_log.open("w") as out:
            p = subprocess.Popen(["/usr/bin/time", "-v", "-o", str(geom_time), str(GEOMETRY), str(card), str(N_PER_SEED), str(geom)], stdout=out, stderr=subprocess.STDOUT, cwd=GEOMETRY.parent)
            update_row(status_path, key, {"pid": p.pid})
            rc = p.wait()
        if rc != 0:
            raise RuntimeError(f"geometry exit code {rc}")
        geometry = load_geometry_csv(geom)
        if len(geometry.leading_jet_pt_per_event) != N_PER_SEED:
            raise RuntimeError(f"geometry denominator mismatch: {len(geometry.leading_jet_pt_per_event)}")

        tl = result.regions["Trackless"]
        hp = result.regions["High-pT"]
        cutflow_csv(cutflow, result)
        recast_wall, recast_rss = parse_time_file(recast_time)
        geometry_wall, geometry_rss = parse_time_file(geom_time)
        total_wall = time.time() - start
        payload = {
            "node_id": nid, "mH_GeV": mass, "ctau_mm": ctau, "seed": seed,
            "N_requested": N_PER_SEED, "N_processed": result.n_events,
            "raw_selected": tl.acc, "raw_selection_fraction": tl.acc / result.n_events,
            "weighted_numerator": tl.acc_x_eff, "Aeff": tl.acc_x_eff / result.n_events,
            "raw_highpt_selected": hp.acc, "weighted_highpt_numerator": hp.acc_x_eff,
            "HighPt_Aeff": hp.acc_x_eff / result.n_events,
            "recast_wall_seconds": recast_wall, "geometry_wall_seconds": geometry_wall,
            "wall_seconds": total_wall, "recast_peak_rss_kb": recast_rss, "geometry_peak_rss_kb": geometry_rss,
            "input_LHE": str(input_lhe.resolve()), "input_sha256": input_hash,
            "card_path": str(card.resolve()), "log_path": str(log.resolve()),
            "cutflow_path": str(cutflow.resolve()), "geometry_path": str(geom.resolve()),
            "mean_leading_jet_pt_GeV": sum(geometry.leading_jet_pt_per_event) / len(geometry.leading_jet_pt_per_event),
            "mean_n_jets_pt20": sum(geometry.n_jets_per_event) / len(geometry.n_jets_per_event),
            "cutflow": {stage: {"highpt_count": result.regions["High-pT"].stage_counts[stage], "trackless_count": result.regions["Trackless"].stage_counts[stage]} for stage in STAGES},
        }
        result_json.write_text(json.dumps(payload, indent=2))
        update_row(status_path, key, {"status": "COMPLETE", "pid": "", "end_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "wall_seconds": f"{total_wall:.3f}", "N_processed": result.n_events, "raw_selected": tl.acc, "weighted_numerator": tl.acc_x_eff, "Aeff": f"{tl.acc_x_eff / result.n_events:.12g}", "log_path": log.resolve(), "card_path": card.resolve(), "input_LHE": input_lhe.resolve(), "input_sha256": input_hash, "cutflow_path": cutflow.resolve(), "geometry_path": geom.resolve(), "peak_rss_kb": max(x for x in (recast_rss, geometry_rss) if x is not None)})
        return {"node_id": nid, "seed": seed, "status": "COMPLETE", "wall_seconds": total_wall, "result": payload}
    except Exception as exc:
        error_path.write_text(f"{type(exc).__name__}: {exc}\n")
        update_row(status_path, key, {"status": "FAILED", "pid": "", "end_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "wall_seconds": f"{time.time() - start:.3f}", "error_path": error_path.resolve()})
        return {"node_id": nid, "seed": seed, "status": "FAILED", "error": str(exc)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mission-root", type=Path, required=True)
    ap.add_argument("--nodes-json", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--batch-name", required=True)
    args = ap.parse_args()
    mission = args.mission_root.resolve()
    status_path = mission / "grid_status.csv"
    nodes = json.loads(args.nodes_json.read_text())
    unique_nodes = {}
    for n in nodes:
        key = (int(n["mH_GeV"]), float(n["ctau_mm"]))
        if key in unique_nodes:
            raise SystemExit(f"duplicate requested node: mH={key[0]} ctau={key[1]:.16g}")
        unique_nodes[key] = {"mH_GeV": key[0], "ctau_mm": key[1]}
    nodes = list(unique_nodes.values())
    if args.workers < 1 or args.workers > 4:
        raise SystemExit("workers must be between 1 and 4")
    rows = load_status(status_path)
    for n in nodes:
        mass = int(n["mH_GeV"]); ctau = float(n["ctau_mm"]); nid = node_id(mass, ctau)
        for seed in SEEDS:
            key = (nid, seed)
            if key not in rows:
                rows[key] = {f: "" for f in FIELDS}
                rows[key].update({"node_id": nid, "mH_GeV": mass, "ctau_mm": f"{ctau:.16g}", "seed": str(seed), "N_requested": str(N_PER_SEED), "N_processed": "0", "status": "PENDING", "pid": "", "start_time": "", "end_time": "", "wall_seconds": "", "raw_selected": "", "weighted_numerator": "", "Aeff": "", "log_path": "", "card_path": "", "input_LHE": "", "input_sha256": "", "cutflow_path": "", "geometry_path": "", "peak_rss_kb": "", "error_path": ""})
    atomic_status(status_path, rows)
    batch_start = time.time()
    futures = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for n in nodes:
            for seed in SEEDS:
                futures.append(pool.submit(run_one, mission, int(n["mH_GeV"]), float(n["ctau_mm"]), seed, status_path))
        results = [f.result() for f in as_completed(futures)]
    batch_wall = time.time() - batch_start
    out = {"batch_name": args.batch_name, "started_epoch": batch_start, "ended_epoch": time.time(), "batch_wall_seconds": batch_wall, "workers": args.workers, "nodes_requested": len(nodes), "seed_jobs_requested": len(nodes) * len(SEEDS), "results": sorted(results, key=lambda x: (x["node_id"], x["seed"]))}
    (mission / f"{args.batch_name}_batch.json").write_text(json.dumps(out, indent=2))
    failed = [x for x in results if x["status"] == "FAILED"]
    print(json.dumps({"batch_name": args.batch_name, "batch_wall_seconds": batch_wall, "nodes": len(nodes), "complete_seed_jobs": sum(x["status"] in ("COMPLETE", "REUSED") for x in results), "failed_seed_jobs": len(failed)}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
