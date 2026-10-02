"""Which society an institution belongs to, from data/institution_societies.json.

A civilisation's own society is its `society` field, or its id when absent, so
"foreign" follows from data for every civilisation, mods included.
"""
import functools
import json
import os
from typing import Dict, Mapping

_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "institution_societies.json")


@functools.lru_cache(maxsize=None)
def _table() -> Dict[str, Dict[str, str]]:
    with open(_PATH, encoding="utf-8") as handle:
        document = json.load(handle)
    return {"markers": document["markers"],
            "exclusive_markers": document["exclusive_markers"]}


def society_of(civilisation: Mapping) -> str:
    return civilisation.get("society") or civilisation.get("id") or ""


def belongs_to_other_society(text: str, civilisation: Mapping, table_name: str) -> bool:
    """True when `text` contains a marker of `table_name` that another society owns."""
    own = society_of(civilisation)
    return any(marker in text and society != own
               for marker, society in _table()[table_name].items())
