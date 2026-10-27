from pathlib import Path
import hashlib

import yaml

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "4f3a938ed54dbc779d25f691ce1dd06fe17af69751105dc3b69ccb6b7d92fff6"
EXPECTED_COMMIT = "087ba246e9a9fa34b16249b52629a62703893b5c"


def test_convention_cache_has_pinned_provenance():
    path = ROOT / "conventions/physics_conventions.yaml"
    sidecar = yaml.safe_load((ROOT / "conventions/physics_conventions.lock.yaml").read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == EXPECTED_SHA256
    assert sidecar["source_repository"] == "fbientrigo/dihiggs"
    assert sidecar["source_commit"] == EXPECTED_COMMIT
    assert sidecar["source_path"] == "conventions/physics_conventions.yaml"
    assert sidecar["source_sha256"] == EXPECTED_SHA256
    assert sidecar["schema_version"] == "physics_conventions_v3"
    assert yaml.safe_load(path.read_text())["schema_version"] == "physics_conventions_v3"
