"""The text the solve key hashed before large inputs kept their text, as plain reference code."""
import json
from typing import Any, Dict


def payload_by_dumping(inputs: Dict[str, Any], environment: str) -> str:
    return json.dumps({"inputs": inputs, "environment": environment}, sort_keys=True, default=lambda value: sorted(value))
