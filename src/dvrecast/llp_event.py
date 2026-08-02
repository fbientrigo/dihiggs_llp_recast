from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from .config import resolve_llp_pdg_id
from .cutflow import CutflowRow


class LlpNotFoundError(ValueError):
    """Raised when the configured LLP PDG id is absent from an event record."""


@dataclass(frozen=True)
class Particle:
    index: int
    pdg_id: int
    mother: int | None
    is_final: bool
    charge: float = 0.0
    decay_vertex_mm: tuple[float, float, float] | None = None


@dataclass(frozen=True)
class VertexReading:
    radius_mm: float
    z_mm: float


def find_llp(particles: Sequence[Particle], pdg_id: int) -> int:
    """Return the index of the first particle matching ``pdg_id``.

    Raises :class:`LlpNotFoundError` when no particle in the event carries the
    configured PDG id, per the requirement to fail clearly rather than
    silently produce an empty cutflow.
    """
    for particle in particles:
        if particle.pdg_id == pdg_id:
            return particle.index
    raise LlpNotFoundError(
        f"configured LLP pdg_id={pdg_id} not found among {len(particles)} particles"
    )


def collect_descendants(particles: Sequence[Particle], index: int) -> list[Particle]:
    """Recursively collect all descendants of ``particles[index]`` by mother links."""
    by_mother: dict[int, list[Particle]] = {}
    for particle in particles:
        if particle.mother is not None:
            by_mother.setdefault(particle.mother, []).append(particle)

    result: list[Particle] = []
    frontier = [index]
    seen: set[int] = set()
    while frontier:
        current = frontier.pop()
        for child in by_mother.get(current, []):
            if child.index in seen:
                continue
            seen.add(child.index)
            result.append(child)
            frontier.append(child.index)
    return result


def read_decay_vertex(particle: Particle) -> VertexReading | None:
    """Read (not reconstruct) the LLP decay vertex already present on the record."""
    if particle.decay_vertex_mm is None:
        return None
    x, y, z = particle.decay_vertex_mm
    return VertexReading(radius_mm=math.hypot(x, y), z_mm=z)


def _particles_from_mapping(raw: Sequence[Mapping[str, object]]) -> list[Particle]:
    particles: list[Particle] = []
    for entry in raw:
        vertex = entry.get("decay_vertex_mm")
        particles.append(
            Particle(
                index=int(entry["index"]),
                pdg_id=int(entry["pdg_id"]),
                mother=None if entry.get("mother") is None else int(entry["mother"]),
                is_final=bool(entry.get("is_final", False)),
                charge=float(entry.get("charge", 0.0)),
                decay_vertex_mm=tuple(float(v) for v in vertex) if vertex is not None else None,
            )
        )
    return particles


def load_fixture(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run_llp_smoke_cutflow(
    fixture: Mapping[str, object],
    *,
    llp_pdg_id: int | str | None = None,
) -> tuple[list[CutflowRow], str | None]:
    """Run the fixture event through the generic, fixture-driven smoke cutflow.

    All numeric thresholds (fiducial vertex region, minimum charged
    descendants) come from ``fixture`` itself, not from constants in this
    module. Returns the cutflow rows plus the name of the first failed stage
    (``None`` if every stage passed).
    """
    pdg_id = resolve_llp_pdg_id(llp_pdg_id, config=fixture)
    particles = _particles_from_mapping(fixture["particles"])

    llp_index = find_llp(particles, pdg_id)
    llp = next(p for p in particles if p.index == llp_index)
    descendants = collect_descendants(particles, llp_index)
    vertex = read_decay_vertex(llp)
    region = fixture.get("vertex_region_mm", {})
    selection = fixture.get("final_selection", {})

    stages: list[tuple[str, bool]] = [("events_read", True), ("llp_identified", True)]
    stages.append(("descendants_collected", len(descendants) > 0))
    stages.append(("displaced_vertex_read", vertex is not None))

    if vertex is not None:
        max_radius = float(region.get("max_radius", math.inf))
        max_abs_z = float(region.get("max_abs_z", math.inf))
        fiducial = vertex.radius_mm <= max_radius and abs(vertex.z_mm) <= max_abs_z
    else:
        fiducial = False
    stages.append(("vertex_in_fiducial_region", fiducial))

    charged_descendants = sum(1 for p in descendants if p.is_final and p.charge != 0)
    min_charged = int(selection.get("min_charged_descendants", 0))
    stages.append(("final_selection", charged_descendants >= min_charged))

    rows: list[CutflowRow] = []
    rejection_stage: str | None = None
    alive = True
    for name, passed in stages:
        alive = alive and passed
        rows.append(CutflowRow(name, 1.0 if alive else 0.0))
        if rejection_stage is None and not alive:
            rejection_stage = name

    return rows, rejection_stage
