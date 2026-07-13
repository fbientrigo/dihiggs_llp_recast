from __future__ import annotations

import subprocess
from pathlib import Path

from dvrecast.config import UpstreamLock
from dvrecast.manifest import build_environment_manifest, pythia_source_provenance


def _git(path: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=path, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _source_checkout(tmp_path: Path) -> tuple[Path, str]:
    source = tmp_path / "pythia-source"
    source.mkdir()
    _git(source, "init", "-q")
    _git(source, "config", "user.email", "tests@example.invalid")
    _git(source, "config", "user.name", "Tests")
    (source / "README").write_text("source\n", encoding="utf-8")
    _git(source, "add", "README")
    _git(source, "commit", "-qm", "source")
    head = _git(source, "rev-parse", "HEAD")
    _git(source, "tag", "pythia8308")
    (source / "build-artifact").write_text("untracked\n", encoding="utf-8")
    return source, head


def test_manifest_contains_expected_provenance(tmp_path: Path) -> None:
    lock = UpstreamLock(
        repository="https://github.com/example/repo.git",
        commit="a" * 40,
        analysis_path=Path("analysis/path"),
    )
    manifest = build_environment_manifest(tmp_path, lock)
    assert manifest["schema_version"] == 2
    assert manifest["upstream"]["expected_commit"] == "a" * 40
    assert manifest["upstream"]["checkout"] is None
    assert isinstance(manifest["tools"], list)
    assert manifest["build"]["available"] is False
    assert manifest["readiness"]["selected_upstream_benchmark"]["state"] == "BLOCKED"


def test_pythia_source_checkout_declarations_match(tmp_path: Path) -> None:
    source, head = _source_checkout(tmp_path)
    provenance = pythia_source_provenance(
        {
            "PYTHIA8_SOURCE_DIR": str(source),
            "PYTHIA8_SOURCE_TAG": "pythia8308",
            "PYTHIA8_SOURCE_COMMIT": head,
        }
    )
    assert provenance["source_checkout_declaration_status"] == "MATCHES"
    assert provenance["source_checkout_path"] == str(source.resolve())
    assert provenance["source_checkout_head"] == head
    assert provenance["declared_commit_matches_head"] is True
    assert provenance["declared_tag_matches_head"] is True
    assert provenance["source_checkout_tracked_dirty"] is False
    assert provenance["source_checkout_untracked_entries_present"] is True
    assert provenance["install_origin_status"] == "UNVERIFIED"


def test_pythia_source_checkout_declarations_unverified_without_checkout() -> None:
    provenance = pythia_source_provenance(
        {"PYTHIA8_SOURCE_TAG": "pythia8308", "PYTHIA8_SOURCE_COMMIT": "b" * 40}
    )
    assert provenance["source_checkout_declaration_status"] == "UNVERIFIED"
    assert provenance["declared_commit"] == "b" * 40
    assert provenance["source_checkout_head"] is None
    assert provenance["install_origin_status"] == "UNVERIFIED"


def test_pythia_source_provenance_mismatch(tmp_path: Path) -> None:
    source, _ = _source_checkout(tmp_path)
    provenance = pythia_source_provenance(
        {
            "PYTHIA8_SOURCE_DIR": str(source),
            "PYTHIA8_SOURCE_TAG": "wrong-tag",
            "PYTHIA8_SOURCE_COMMIT": "b" * 40,
        }
    )
    assert provenance["source_checkout_declaration_status"] == "MISMATCH"
    assert provenance["declared_commit_matches_head"] is False
    assert provenance["declared_tag_matches_head"] is False
    assert provenance["install_origin_status"] == "UNVERIFIED"


def test_pythia_source_provenance_separates_tracked_changes(tmp_path: Path) -> None:
    source, head = _source_checkout(tmp_path)
    (source / "README").write_text("modified\n", encoding="utf-8")

    provenance = pythia_source_provenance(
        {
            "PYTHIA8_SOURCE_DIR": str(source),
            "PYTHIA8_SOURCE_TAG": "pythia8308",
            "PYTHIA8_SOURCE_COMMIT": head,
        }
    )

    assert provenance["source_checkout_declaration_status"] == "MATCHES"
    assert provenance["source_checkout_tracked_dirty"] is True
    assert provenance["source_checkout_untracked_entries_present"] is True


def test_manifest_records_installed_toolchain_and_source_provenance(tmp_path: Path) -> None:
    lock = UpstreamLock(
        repository="https://github.com/example/repo.git",
        commit="a" * 40,
        analysis_path=Path("analysis/path"),
    )
    manifest = build_environment_manifest(
        tmp_path,
        lock,
        {
            "PYTHIA8": str(tmp_path / "pythia"),
            "FASTJET3": str(tmp_path / "fastjet"),
            "PYTHIA8_SOURCE_TAG": "pythia8308",
            "PYTHIA8_SOURCE_COMMIT": "b" * 40,
        },
    )
    pythia = manifest["toolchain"]["pythia"]
    provenance = pythia["source_provenance"]
    assert provenance["source_checkout_declaration_status"] == "UNVERIFIED"
    assert provenance["install_origin_status"] == "UNVERIFIED"
    assert manifest["toolchain"]["fastjet"]["prefix"] == str(tmp_path / "fastjet")
