"""A copy of dicts, lists and values that shares nothing with what it was made from.

A seat's patents, shares and offers are kept by the seats module; its views hand out copies, and the module's rules return new figures."""
import copy
from typing import Any


def plain(value: Any) -> Any:
	"""`value` as dicts, lists and values only, copied."""
	if isinstance(value, dict):
		return {key: plain(item) for key, item in value.items()}
	if isinstance(value, list):
		return [plain(item) for item in value]
	return copy.deepcopy(value)
