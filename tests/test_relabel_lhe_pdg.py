from __future__ import annotations

import gzip
import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "relabel_lhe_pdg.py"
_spec = importlib.util.spec_from_file_location("relabel_lhe_pdg", _SCRIPT_PATH)
relabel_lhe_pdg = importlib.util.module_from_spec(_spec)
sys.modules["relabel_lhe_pdg"] = relabel_lhe_pdg
_spec.loader.exec_module(relabel_lhe_pdg)


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


def test_relabel_preserves_momenta_and_changes_only_id(tmp_path):
    src = _write_gz(tmp_path / "in.lhe.gz", _MINI_LHE)
    dst = tmp_path / "out.lhe.gz"
    n_events, n_relabelled = relabel_lhe_pdg.relabel(str(src), str(dst), 9000006, 35)
    assert n_events == 1
    assert n_relabelled == 2

    with gzip.open(dst, "rt") as fh:
        out_lines = fh.readlines()
    with gzip.open(src, "rt") as fh:
        in_lines = fh.readlines()

    changed_ids = 0
    for in_line, out_line in zip(in_lines, out_lines, strict=True):
        in_fields, out_fields = in_line.split(), out_line.split()
        if len(in_fields) == 13:
            # momenta/status/mothers/colours/mass/tau/spin must be unchanged
            assert in_fields[1:] == out_fields[1:]
            if in_fields[0] != out_fields[0]:
                changed_ids += 1
                assert in_fields[0] == "9000006"
                assert out_fields[0] == "35"
    assert changed_ids == 2


def test_relabel_rejects_wrong_expected_event_count(tmp_path):
    src = _write_gz(tmp_path / "in.lhe.gz", _MINI_LHE)
    dst = tmp_path / "out.lhe.gz"
    n_events, n_relabelled = relabel_lhe_pdg.relabel(str(src), str(dst), 9000006, 35)
    assert n_events != 2  # sanity: this fixture has exactly 1 event


def test_relabel_refuses_when_target_pdg_already_present(tmp_path):
    already_relabelled = _MINI_LHE.replace("9000006", "35")
    src = _write_gz(tmp_path / "in.lhe.gz", already_relabelled)
    dst = tmp_path / "out.lhe.gz"
    with pytest.raises(SystemExit, match="already carry target PDG"):
        relabel_lhe_pdg.relabel(str(src), str(dst), 9000006, 35)


def test_relabel_refuses_when_source_pdg_absent(tmp_path):
    no_source = _MINI_LHE.replace("9000006", "99")
    src = _write_gz(tmp_path / "in.lhe.gz", no_source)
    dst = tmp_path / "out.lhe.gz"
    with pytest.raises(SystemExit, match="no particle line carried source PDG"):
        relabel_lhe_pdg.relabel(str(src), str(dst), 9000006, 35)
