"""Reading JSON data from disk: the one place every package lists a folder's .json files and loads one."""
import json
import os
from typing import Any, List


def json_files(folder: str) -> List[str]:
    """Paths of the .json files directly in `folder`, in name order; empty when the folder does not exist."""
    if not os.path.isdir(folder):
        return []
    return [os.path.join(folder, name) for name in sorted(os.listdir(folder)) if name.endswith(".json")]


def read_json(path: str) -> Any:
    with open(path, encoding="utf-8") as source:
        return json.load(source)
