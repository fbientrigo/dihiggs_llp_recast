"""Tests for the R8 full-reproduction self-consistency fixes:

1. the reference-manifest snapshot used by scripts/run_r8_reproduction.sh
   lives outside results/r8_h2_model_derived_4b/ (RESULTS_DIR) and is
   cleaned up on every exit path;
2. scripts/lhe_identity.py's separation of historical/canonical/
   deterministic LHE identity, including that gzip-header-only differences
   are not treated as physics-content drift while real decompressed-
   content differences are.

None of these tests run MadGraph, Pythia, the C++ recast, or the geometry
driver.
"""

from __future__ import annotations

import gzip
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPRODUCTION_SCRIPT = ROOT / "scripts" / "run_r8_reproduction.sh"
RESULTS_DIR = ROOT / "results" / "r8_h2_model_derived_4b"
INPUT_MANIFEST = RESULTS_DIR / "input_manifest.json"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


lhe_identity = _load_module("lhe_identity", ROOT / "scripts" / "lhe_identity.py")
verify_r8_artifacts = _load_module("verify_r8_artifacts", ROOT / "scripts" / "verify_r8_artifacts.py")


_MINI_LHE = """<LesHouchesEvents version="3.0">
<init>
</init>
<event>
 4      1 +2.2986000e-04 6.82333700e+02 7.81860800e-03 9.74793000e-02
       21 -1    0    0  502  501 +0.0000000000e+00 +0.0000000000e+00 +2.9507588988e+02 2.9507588988e+02 0.0000000000e+00 0.0000e+00 -1.0000e+00
       21 -1    0    0  501  502 -0.0000000000e+00 -0.0000000000e+00 -3.9445719893e+02 3.9445719893e+02 0.0000000000e+00 0.0000e+00 -1.0000e+00
  9000006  1    1    2    0    0 -3.0637933119e+02 -4.3929035059e+00 -4.6975897764e+01 3.4437527082e+02 1.5000000000e+02 0.0000e+00 0.0000e+00
  9000006  1    1    2    0    0 +3.0637933119e+02 +4.3929035059e+00 -5.2405411284e+01 3.4515781798e+02 1.5000000000e+02 0.0000e+00 0.0000e+00
</event>
</LesHouchesEvents>
"""


def _write_gz(path, text):
    with gzip.open(path, "wt") as fh:
        fh.write(text)
    return path


# ---------------------------------------------------------------------------
# Fix 1: reference manifest outside the artifact tree
# ---------------------------------------------------------------------------


def _script_text():
    return REPRODUCTION_SCRIPT.read_text()


def test_reference_manifest_lives_outside_results_dir():
    text = _script_text()
    assert 'SCRATCH_DIR="$(mktemp -d "${TMPDIR:-/tmp}/r8-reproduction.XXXXXX")"' in text
    assert 'REFERENCE_MANIFEST="${SCRATCH_DIR}/artifact_manifest.reference.json"' in text
    # The old, buggy placement must not reappear.
    assert 'REFERENCE_MANIFEST="${RESULTS_DIR}/artifact_manifest.reference.json"' not in text


def test_temporary_reference_cleanup_trap_present():
    text = _script_text()
    assert "trap cleanup EXIT INT TERM" in text
    assert 'rm -rf "${SCRATCH_DIR}"' in text
    # cleanup must be registered before any step that could fail, i.e.
    # before the first "step " call that follows scratch-dir creation.
    scratch_idx = text.index("SCRATCH_DIR=")
    trap_idx = text.index("trap cleanup EXIT INT TERM")
    assert scratch_idx < trap_idx


def test_reference_manifest_never_self_included_in_fresh_manifest():
    """Regenerate the real artifact_manifest.json from the already-committed
    result tree (fast: pure hashing, no Pythia/recast) and confirm the
    reference-manifest filename never appears as a tracked artifact, and no
    stray file with that name exists anywhere under RESULTS_DIR."""
    result = subprocess.run(
        [sys.executable, "scripts/build_r8_artifact_manifest.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    manifest = json.loads((RESULTS_DIR / "artifact_manifest.json").read_text())
    assert not any(
        "artifact_manifest.reference.json" in path for path in manifest["files"]
    ), "the reference-manifest snapshot must never be recorded as a tracked R8 artifact"

    stray = list(RESULTS_DIR.rglob("artifact_manifest.reference.json"))
    assert stray == [], f"reference-manifest snapshot leaked into RESULTS_DIR: {stray}"


# ---------------------------------------------------------------------------
# Fix 2: canonical identity for relabelled gzip inputs
# ---------------------------------------------------------------------------


def test_deterministic_gzip_sha_stable_across_repeated_runs(tmp_path):
    src = _write_gz(tmp_path / "in.lhe.gz", _MINI_LHE)
    identity_1 = lhe_identity.compute_identity(str(src), 9000006, 35, 1, 2)
    time.sleep(1.1)  # gzip's default header would embed a different mtime
    identity_2 = lhe_identity.compute_identity(str(src), 9000006, 35, 1, 2)
    key = "deterministic_relabelled_gzip_sha256"
    assert identity_1[key] == identity_2[key]


def test_canonical_decompressed_hash_stable_across_repeated_runs(tmp_path):
    src = _write_gz(tmp_path / "in.lhe.gz", _MINI_LHE)
    identity_1 = lhe_identity.compute_identity(str(src), 9000006, 35, 1, 2)
    identity_2 = lhe_identity.compute_identity(str(src), 9000006, 35, 1, 2)
    key = "canonical_uncompressed_sha256"
    assert identity_1[key] == identity_2[key]


def test_historical_gzip_provenance_preserved_in_input_manifest():
    manifest = json.loads(INPUT_MANIFEST.read_text())
    for run, historical_hash in (
        ("run_01", "547db2ddec2dfab31bd9383fa2be4bcfcc9773216ed88aec0b8ef4afb2e3b967"),
        ("run_02", "3f0f2c37c2c72739b9bd10e6f4130f7fd71c8eb29b95c233a54180a9973386f4"),
    ):
        identity = manifest["lhe_inputs"][run]["lhe_identity"]
        assert identity["historical_relabelled_gzip_sha256_at_pr6_run_time"] == historical_hash
        # The historical hash must be distinguishable from the current
        # deterministic hash, not silently overwritten in place.
        assert identity["deterministic_relabelled_gzip_sha256"] != historical_hash
        assert identity["gzip_contract"] == {"mtime": 0, "filename": ""}


def test_input_manifest_lhe_identity_has_required_fields():
    manifest = json.loads(INPUT_MANIFEST.read_text())
    required_fields = {
        "source_lhe_sha256",
        "historical_relabelled_gzip_sha256_at_pr6_run_time",
        "canonical_uncompressed_sha256",
        "deterministic_relabelled_gzip_sha256",
        "relabel_script_sha256",
        "gzip_contract",
    }
    for run in ("run_01", "run_02"):
        identity = manifest["lhe_inputs"][run]["lhe_identity"]
        assert required_fields <= set(identity)


def test_modified_decompressed_event_content_is_rejected(tmp_path, monkeypatch):
    """A relabelled LHE whose decompressed physics content differs from the
    recorded canonical_uncompressed_sha256 must fail check_lhe_content_identity
    closed -- not be silently accepted because the file merely exists."""
    src = _write_gz(tmp_path / "in.lhe.gz", _MINI_LHE)
    identity = lhe_identity.compute_identity(str(src), 9000006, 35, 1, 2)

    fake_data_dir = tmp_path / "data_dir"
    fake_data_dir.mkdir()
    fake_results_dir = tmp_path / "results_dir"
    fake_results_dir.mkdir()

    # A relabelled file whose decompressed content differs from what the
    # manifest below claims (built from a different source event).
    tampered_lhe = _MINI_LHE.replace("1.5000000000e+02", "1.5000000001e+02")
    _write_gz(fake_data_dir / "relabelled_run_01.lhe.gz", tampered_lhe)
    _write_gz(fake_data_dir / "relabelled_run_02.lhe.gz", tampered_lhe)

    manifest = {
        "lhe_inputs": {
            "run_01": {"lhe_identity": identity},
            "run_02": {"lhe_identity": identity},
        }
    }
    (fake_results_dir / "input_manifest.json").write_text(json.dumps(manifest))

    monkeypatch.setattr(verify_r8_artifacts, "RESULTS_DIR", str(fake_results_dir))
    monkeypatch.setattr(verify_r8_artifacts, "DATA_DIR", str(fake_data_dir))
    assert verify_r8_artifacts.check_lhe_content_identity() is False


def test_gzip_header_only_difference_is_accepted_as_same_physics_content(tmp_path, monkeypatch):
    """Two relabelled files with identical decompressed content but
    different gzip header metadata (mtime, embedded filename) must be
    accepted -- a compressed-byte difference alone is not physics drift."""
    src = _write_gz(tmp_path / "in.lhe.gz", _MINI_LHE)
    identity = lhe_identity.compute_identity(str(src), 9000006, 35, 1, 2)

    fake_data_dir = tmp_path / "data_dir"
    fake_data_dir.mkdir()
    fake_results_dir = tmp_path / "results_dir"
    fake_results_dir.mkdir()

    # Recompute decompressed bytes via relabel(), then re-wrap them with
    # non-canonical gzip header metadata (different mtime + embedded name).
    tmp_out = tmp_path / "relabelled.lhe.gz"
    sys.path.insert(0, str(ROOT / "scripts"))
    from relabel_lhe_pdg import relabel as _relabel  # noqa: E402

    _relabel(str(src), str(tmp_out), 9000006, 35, 1, 2)
    with gzip.open(tmp_out, "rb") as fh:
        decompressed = fh.read()

    for run in ("run_01", "run_02"):
        dest = fake_data_dir / f"relabelled_{run}.lhe.gz"
        with open(dest, "wb") as raw:
            gz = gzip.GzipFile(filename="not-canonical.lhe", mode="wb", fileobj=raw, mtime=999999)
            with gz:
                gz.write(decompressed)

    manifest = {
        "lhe_inputs": {
            "run_01": {"lhe_identity": identity},
            "run_02": {"lhe_identity": identity},
        }
    }
    (fake_results_dir / "input_manifest.json").write_text(json.dumps(manifest))

    monkeypatch.setattr(verify_r8_artifacts, "RESULTS_DIR", str(fake_results_dir))
    monkeypatch.setattr(verify_r8_artifacts, "DATA_DIR", str(fake_data_dir))
    assert verify_r8_artifacts.check_lhe_content_identity() is True


# ---------------------------------------------------------------------------
# Fresh input_checksums reproducibility (uses the real cached canonical LHE
# if a prior session has staged it under data/raw/; skips otherwise, since
# raw LHE is intentionally not committed -- see AGENTS.md).
# ---------------------------------------------------------------------------

_DATA_DIR = ROOT / "data" / "raw" / "r8_h2_model_derived_4b"


@pytest.mark.parametrize("run", ["run_01", "run_02"])
def test_fresh_input_checksums_reproducible(run):
    canonical = _DATA_DIR / f"canonical_{run}.lhe.gz"
    if not canonical.exists():
        pytest.skip(f"canonical LHE not cached locally at {canonical}; raw LHE is not committed")

    manifest = json.loads(INPUT_MANIFEST.read_text())
    identity = manifest["lhe_inputs"][run]["lhe_identity"]

    fresh = lhe_identity.compute_identity(str(canonical), 9000006, 35, 1000, 2000)
    assert fresh["source_lhe_sha256"] == identity["source_lhe_sha256"]
    assert fresh["canonical_uncompressed_sha256"] == identity["canonical_uncompressed_sha256"]
    assert (
        fresh["deterministic_relabelled_gzip_sha256"]
        == identity["deterministic_relabelled_gzip_sha256"]
    )

    checksums_path = RESULTS_DIR / run / "input_checksums.txt"
    committed_lhe_hash = None
    for line in checksums_path.read_text().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        digest, path = line.split(None, 1)
        if path.strip().endswith(".lhe.gz"):
            committed_lhe_hash = digest
    assert committed_lhe_hash == fresh["deterministic_relabelled_gzip_sha256"]
