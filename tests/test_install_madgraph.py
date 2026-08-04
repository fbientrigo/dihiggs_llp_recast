from __future__ import annotations

import subprocess
from pathlib import Path

SCRIPT = Path("scripts/install_madgraph_local.sh")
COMMIT = "59b4b9c1238978f39a32b8bc83244328187704b6"


def test_madgraph_installer_dry_run_is_explicit(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            str(SCRIPT),
            "--version",
            "3.5.3",
            "--git-commit",
            COMMIT,
            "--prefix",
            str(tmp_path / "mg5"),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "[DRY-RUN]" in result.stdout
    assert "version=3.5.3" in result.stdout


def test_madgraph_installer_refuses_existing_nonmatching_prefix(tmp_path: Path) -> None:
    prefix = tmp_path / "mg5"
    prefix.mkdir()

    result = subprocess.run(
        [
            str(SCRIPT),
            "--version",
            "3.5.3",
            "--git-commit",
            COMMIT,
            "--prefix",
            str(prefix),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 3
    assert "Refusing to overwrite" in result.stderr


def test_madgraph_installer_refuses_repository_prefix() -> None:
    result = subprocess.run(
        [
            str(SCRIPT),
            "--version",
            "3.5.3",
            "--git-commit",
            COMMIT,
            "--prefix",
            str(Path.cwd() / "local-mg5-test"),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "outside the repository" in result.stderr
