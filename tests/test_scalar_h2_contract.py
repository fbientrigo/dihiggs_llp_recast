from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]
SOURCE = (ROOT / "src/scalar_h2_recast.cc").read_text(encoding="utf-8")


def test_default_mode_is_upstream_susy() -> None:
    assert 'MODE="${2:-upstream-susy}"' in (ROOT / "scripts/run_recast.sh").read_text()


def test_scalar_pdg_and_lifetime_units_are_explicit() -> None:
    assert "9000006" in SOURCE and "--ctau" in SOURCE and "setTau0(a.ctau)" in SOURCE


def test_single_pythia_owner_and_no_second_shower() -> None:
    assert "single_pythia_pass" in SOURCE
    assert "single_pythia_decay_shower_hadronization_pass" not in SOURCE
    assert "pythia.next()" in SOURCE
    assert "pack_aa_driver" not in SOURCE


def test_requested_bb_not_gamma_gamma() -> None:
    config = (ROOT / "configs/scalar_h2_ctau_1000_bb.yaml").read_text()
    assert "decay: [5, -5]" in config and "22" not in config


def test_atlas_selection_literals_are_present() -> None:
    for value in (
        "250.",
        "195.",
        "116.",
        "90.",
        "137.",
        "101.",
        "83.",
        "55.",
        "70.",
        "50.",
        "3870.",
        "300.",
        "4.",
        "520.",
        "10.",
    ):
        assert value in SOURCE


def test_pack_a_and_pack_aa_hash_contracts_are_pinned() -> None:
    audit = (ROOT / "scripts/audit_scalar_input.py").read_text()
    assert "58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6" in audit
    assert "c83fbf9d29b3f58bbe98579e6c7b9846d60f45ed4f0262528cb61875b3646838" in audit


def test_upstream_submodule_pin_is_unchanged() -> None:
    assert (
        "d4047c744062094c9f88e507bb1ccf69e9fe88d6"
        in (ROOT / "configs/upstream.lock.json").read_text()
    )


def test_replica_accounting_is_explicit() -> None:
    assert "production_event_id" in SOURCE and "replica_id" in SOURCE
