"""Reads data/disease/<pathogen_id>.json and checks it (the `validate` hook calls `check_pathogen_data`)."""
import json
import os

from . import network
from .types import Pathogen

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "disease")
# Report tags (Complaints/reports/epidemic-model-research.md section 3.2) plus the two this package adds.
CONFIDENCE_TAGS = ("read", "summary", "snippet", "recalled", "disputed", "derived", "unsourced")
_REQUIRED_KEYS = ("id", "name", "stages", "transmissibility_per_day", "case_fatality", "immunity",
                  "reproduction_number_range", "density_exponent", "sources")


def pathogen_ids(directory=None):
    directory = directory or DATA_DIR
    return sorted(name[:-5] for name in os.listdir(directory) if name.endswith(".json") and not name.startswith("_"))


def load_pathogen_plain(pathogen_id, directory=None):
    with open(os.path.join(directory or DATA_DIR, pathogen_id + ".json"), encoding="utf-8") as handle:
        return json.load(handle)


def load_pathogens(directory=None):
    return {pathogen_id: Pathogen.from_plain(load_pathogen_plain(pathogen_id, directory))
            for pathogen_id in pathogen_ids(directory)}


def _source_problems(plain):
    sources = plain.get("sources")
    if not isinstance(sources, dict):
        return ["sources must map each numeric field to a source and a confidence tag"]
    needed = ["transmissibility_per_day", "case_fatality", "immunity", "reproduction_number_range", "density_exponent"]
    needed += ["stage." + stage["id"] for stage in plain.get("stages") or [] if isinstance(stage, dict) and "id" in stage]
    problems = []
    for key in needed:
        entry = sources.get(key)
        if not isinstance(entry, dict) or not str(entry.get("source", "")).strip():
            problems.append("sources.%s: needs a non-empty source" % key)
        elif entry.get("confidence") not in CONFIDENCE_TAGS:
            problems.append("sources.%s: confidence must be one of %s" % (key, ", ".join(CONFIDENCE_TAGS)))
    return problems


def _stage_problems(plain):
    stages = plain.get("stages")
    if not isinstance(stages, list) or not stages:
        return ["stages must be a non-empty list"]
    problems = []
    for stage in stages:
        label = "stage %s" % stage.get("id", "?")
        if not isinstance(stage.get("shape"), int) or stage["shape"] < 1:
            problems.append("%s: shape must be a whole number of at least 1" % label)
        if not isinstance(stage.get("mean_duration_in_days"), (int, float)) or stage["mean_duration_in_days"] <= 0:
            problems.append("%s: mean_duration_in_days must be positive" % label)
        if not isinstance(stage.get("infectiousness"), (int, float)) or stage["infectiousness"] < 0:
            problems.append("%s: infectiousness must be zero or more" % label)
    if not any(isinstance(stage.get("infectiousness"), (int, float)) and stage["infectiousness"] > 0 for stage in stages):
        problems.append("no stage is infectious")
    return problems


def pathogen_problems(plain):
    """Everything wrong with one pathogen record, as sentences; empty when it is usable."""
    problems = ["missing key %s" % key for key in _REQUIRED_KEYS if key not in plain]
    if problems:
        return problems
    problems += _stage_problems(plain) + _source_problems(plain)
    if not 0.0 <= plain["case_fatality"] <= 1.0:
        problems.append("case_fatality must lie between 0 and 1")
    if not isinstance(plain["density_exponent"], (int, float)) or not 0.0 <= plain["density_exponent"] <= 1.0:
        problems.append("density_exponent must lie between 0 (frequency dependent) and 1 (mass action)")
    immunity = plain["immunity"]
    if not immunity.get("permanent") and not (immunity.get("duration_in_days") or 0) > 0:
        problems.append("immunity needs permanent true or a positive duration_in_days")
    low, high = plain["reproduction_number_range"]
    if problems:
        return problems
    value = network.reproduction_number(Pathogen.from_plain(plain))
    if not low * (1 - 1e-9) <= value <= high * (1 + 1e-9):
        problems.append("reproduction number %.3f from the stages and transmissibility lies outside the sourced range "
                        "%s to %s" % (value, low, high))
    return problems


def check_pathogen_data(directory=None):
    """Problems across every pathogen file, each prefixed with the file name."""
    directory = directory or DATA_DIR
    problems = []
    for pathogen_id in pathogen_ids(directory):
        try:
            plain = load_pathogen_plain(pathogen_id, directory)
        except ValueError as exc:
            problems.append("data/disease/%s.json: not valid JSON (%s)" % (pathogen_id, exc))
            continue
        if plain.get("id") != pathogen_id:
            problems.append("data/disease/%s.json: id %r does not match the file name" % (pathogen_id, plain.get("id")))
        problems += ["data/disease/%s.json: %s" % (pathogen_id, problem) for problem in pathogen_problems(plain)]
    return problems
