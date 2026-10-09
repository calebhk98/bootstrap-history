"""The baseline ensemble (Complaints/266): several runs of a civilisation with no player intervention, summarised
into distributions by year and kept in a cache file, so a run can be compared with what the baseline society
tends to do rather than with dated history.

A runner is a function `(civilisation_id, seed, years)` returning one snapshot per year from the opening:
`{year, population, wage_index, literacy_general, literacy_elite, territory_tiles, technologies}`. The real
runner is `baseline_game.play_baseline`; tests pass a stub.
"""
import json
import os
from typing import Any, Callable, Dict, List, Optional, Sequence

from sim import cache_root

METRICS = ("population", "wage_index", "literacy_general", "literacy_elite", "territory_tiles")
BANDS = (("p10", 0.1), ("median", 0.5), ("p90", 0.9))
CACHE_NAME = "baseline_ensemble"

Runner = Callable[[str, int, int], List[Dict[str, Any]]]


def cache_directory() -> str:
    return cache_root.cache_directory(CACHE_NAME)


def cache_path(civilisation_id: str, directory: Optional[str] = None) -> str:
    return os.path.join(directory or cache_directory(), "%s.json" % civilisation_id)


def _quantile(values: Sequence[float], share: float) -> float:
    ordered = sorted(values)
    return ordered[int(round((len(ordered) - 1) * share))]


def _bands(runs: List[List[Dict[str, Any]]], metric: str) -> Dict[str, List[float]]:
    """Each band's value at every year offset, over the runs that reached that offset."""
    horizon = max(len(run) for run in runs)
    bands: Dict[str, List[float]] = {name: [] for name, _share in BANDS}
    for offset in range(horizon):
        values = [run[offset][metric] for run in runs if offset < len(run)]
        for name, share in BANDS:
            bands[name].append(_quantile(values, share))
    return bands


def _first_offsets(runs: List[List[Dict[str, Any]]]) -> Dict[str, List[int]]:
    """Technology id -> the offset at which each run that ever held it first did, sorted."""
    first: Dict[str, List[int]] = {}
    for run in runs:
        seen: set = set()
        for offset, row in enumerate(run):
            for node_id in row["technologies"]:
                if node_id not in seen:
                    seen.add(node_id)
                    first.setdefault(node_id, []).append(offset)
    return {node_id: sorted(offsets) for node_id, offsets in sorted(first.items())}


def summarise(civilisation_id: str, seeds: Sequence[int], runs: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    return {"civilisation": civilisation_id, "seeds": list(seeds), "runs": len(runs),
            "years": max(len(run) for run in runs) - 1, "start_year": runs[0][0]["year"],
            "metrics": {metric: _bands(runs, metric) for metric in METRICS},
            "technologies": _first_offsets(runs)}


def run_ensemble(civilisation_id: str, seeds: Sequence[int], years: int, runner: Optional[Runner] = None,
                 jobs: int = 1) -> Dict[str, Any]:
    """Play every seed with `runner` (several at once when `jobs` > 1 and the runner can be pickled)."""
    if not seeds:
        raise ValueError("an ensemble needs at least one seed")
    if runner is None:
        from sim.engine.baseline_game import play_baseline as runner
    if jobs > 1:
        import concurrent.futures
        with concurrent.futures.ProcessPoolExecutor(max_workers=jobs) as pool:
            runs = list(pool.map(runner, [civilisation_id] * len(seeds), list(seeds), [years] * len(seeds)))
    else:
        runs = [runner(civilisation_id, seed, years) for seed in seeds]
    return summarise(civilisation_id, seeds, runs)


def write_cache(ensemble: Dict[str, Any], directory: Optional[str] = None) -> str:
    path = cache_path(ensemble["civilisation"], directory)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temporary = path + ".part"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(ensemble, handle)
    os.replace(temporary, path)
    return path


def read_cache(civilisation_id: str, directory: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """The stored ensemble, or None when there is none or the file cannot be read."""
    try:
        with open(cache_path(civilisation_id, directory), encoding="utf-8") as handle:
            stored = json.load(handle)
    except (OSError, ValueError):
        return None
    return stored if isinstance(stored, dict) and "metrics" in stored else None


def position(value: float, bands: Dict[str, float]) -> str:
    """Where `value` sits against the baseline's lower and upper band."""
    if value < bands["p10"]:
        return "below"
    return "above" if value > bands["p90"] else "within"


def technology_standing(ensemble: Dict[str, Any], node_id: str, offset: int) -> Dict[str, Any]:
    """How many baseline runs held the technology by `offset`, and the year the median holder first did.
    The society would not yet hold it when fewer than half the runs did."""
    first = ensemble["technologies"].get(node_id, [])
    holding = [reached for reached in first if reached <= offset]
    median_year = None
    if len(first) * 2 >= ensemble["runs"]:
        median_year = ensemble["start_year"] + first[len(first) // 2]
    return {"runs_holding": len(holding), "of_runs": ensemble["runs"],
            "would_not_yet_hold": len(holding) * 2 < ensemble["runs"],
            "median_first_year": median_year}
