"""What an invention is worth, by dimension.

An invention carries gains along named dimensions (military, infrastructure,
prestige and so on). A node may declare them in a `gains` mapping; otherwise
each trait it carries is a gain of one unit in the dimension of that name.
An actor turns gains into worth with its own weights, so the same invention
is valued differently by a government and a firm, and no id is special.
"""
from typing import Any, Dict, Mapping

from .tuning import UNIT_GAIN


def invention_gains(node: Mapping[str, Any]) -> Dict[str, float]:
	"""Gain per dimension: declared `gains` if present, else one per trait."""
	declared = node.get("gains")
	if isinstance(declared, Mapping):
		return {str(dimension): float(amount) for dimension, amount in declared.items()}
	return {trait: UNIT_GAIN for trait in node.get("traits") or ()}


def weighted_gain(gains: Mapping[str, float], weights: Mapping[str, float]) -> float:
	"""Sum of gain times the observer's weight for that dimension."""
	return sum(amount * weights.get(dimension, 0.0) for dimension, amount in gains.items())
