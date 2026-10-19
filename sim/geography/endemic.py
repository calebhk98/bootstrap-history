"""Endemic disease as a tile layer: a vector's pressure on a tile and what it costs each host.

A file in data/disease/endemic/ gives a range (conditions on tile layers), a climate and vegetation
envelope, and per host an annual loss at full pressure. The pressure ("challenge", 0 to 1) is the envelope's
suitability on tiles inside the range; a host's loss is the sum of each disease's loss times its challenge,
compounded across diseases. Hosts are herd animal ids or "people"; nothing here names a place or a species.
"""
import functools
import json
import os
from typing import Dict, Iterable, List, Mapping

from sim.geography import content_rules, tile_layers
from sim.geography.map_source import WorldMap

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        "data", "disease", "endemic")
SCALAR_STRATUM = "all"


@functools.lru_cache(maxsize=None)
def diseases() -> Dict[str, dict]:
    """{id: file contents} of every endemic disease file."""
    found = {}
    for name in sorted(os.listdir(DATA_DIR)):
        if name.endswith(".json") and not name.startswith("_"):
            with open(os.path.join(DATA_DIR, name), encoding="utf-8") as handle:
                found[name[:-5]] = json.load(handle)
    return found


def challenge(world_map: WorldMap, tile_id: str, disease_id: str) -> float:
    """0 to 1: the vector's pressure on the tile; 0 outside its range."""
    cache = world_map.__dict__.setdefault("_endemic_cache", {})
    key = (tile_id, disease_id)
    if key not in cache:
        spec = diseases()[disease_id]
        reader = tile_layers.reader(world_map, tile_id)
        cache[key] = (content_rules.suitability(spec["challenge_envelope"], reader)
                      if content_rules.matches(spec.get("range", ()), reader) else 0.0)
    return cache[key]


def host_loss(world_map: WorldMap, tile_id: str, host: str) -> Dict[str, float]:
    """{stratum: share of the host lost in a year} on the tile, compounded over the diseases that list the
    host; the stratum is "all" for an animal and a population band for people. Empty when no disease does."""
    survival: Dict[str, float] = {}
    for disease_id, spec in sorted(diseases().items()):
        row = spec["hosts"].get(host)
        if row is None:
            continue
        pressure = challenge(world_map, tile_id, disease_id)
        loss = row["annual_loss_at_full_challenge"]
        for stratum, rate in (loss if isinstance(loss, Mapping) else {SCALAR_STRATUM: loss}).items():
            survival[stratum] = survival.get(stratum, 1.0) * (1.0 - min(1.0, rate * pressure))
    return {stratum: 1.0 - kept for stratum, kept in survival.items()}


def animal_loss(world_map: WorldMap, tile_id: str, species: Iterable[str]) -> float:
    """Share lost in a year by the hardiest of the listed species on the tile (a keeper works the animal that
    survives best); 0 for no species."""
    losses = [host_loss(world_map, tile_id, each).get(SCALAR_STRATUM, 0.0) for each in species]
    return min(losses) if losses else 0.0


def mean_people_loss(world_map: WorldMap, tile_ids: Iterable[str]) -> Dict[str, float]:
    """{band: excess death rate per year} averaged over the tiles; empty for no tiles or no disease."""
    tiles = list(tile_ids)
    total: Dict[str, float] = {}
    for tile_id in tiles:
        for band, rate in host_loss(world_map, tile_id, "people").items():
            total[band] = total.get(band, 0.0) + rate
    return {band: rate / len(tiles) for band, rate in total.items()}


def problems() -> List[str]:
    """What is wrong with the endemic files: a missing source tag or a host with no loss."""
    found = []
    for disease_id, spec in sorted(diseases().items()):
        where = "data/disease/endemic/%s.json" % disease_id
        if spec.get("id") != disease_id:
            found.append("%s: id %r does not match the file name" % (where, spec.get("id")))
        for needed in ("challenge_envelope", "hosts", "sources"):
            if needed not in spec:
                found.append("%s: missing %s" % (where, needed))
        for field in ["challenge_envelope"] + ["hosts." + host for host in spec.get("hosts", {})]:
            source = spec.get("sources", {}).get(field)
            if not source or not source.get("source") or not source.get("confidence"):
                found.append("%s: sources needs a source and confidence for %s" % (where, field))
        for host, row in spec.get("hosts", {}).items():
            if "annual_loss_at_full_challenge" not in row:
                found.append("%s: host %s has no annual_loss_at_full_challenge" % (where, host))
    return found
