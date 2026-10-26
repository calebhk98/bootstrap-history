"""What a society finds harder or easier to build than Rome does, from its cost multipliers.

`multipliers` is the civilisation file's table of factors by category or trait (above 1 is harder), and `remedies` its
`handicap_remedies`: a remedy names the node that answers a handicap and the residual factor once that node is done.
The category is the craft and the traits are what it is for, so traits apply at a damped exponent when the craft is in
the table and at full weight when it is not.
"""
from typing import Any, Collection, Mapping, Optional, Sequence

TRAIT_EXPONENT_WHEN_CRAFT_KNOWN = 0.25


def multiplier_for(key: str, multipliers: Mapping[str, Any], remedies: Mapping[str, Any], done: Collection[str]) -> float:
    """The factor for one category or trait, replaced by the remedy's residual once its node is done."""
    multiplier = float(multipliers[key])
    remedy = remedies.get(key)
    if isinstance(remedy, dict) and remedy.get("node") in done:
        multiplier = float(remedy.get("residual", 1.0))
    return multiplier


def civ_cost_factor(multipliers: Optional[Mapping[str, Any]], remedies: Optional[Mapping[str, Any]],
                    done: Collection[str], category: Optional[str], traits: Sequence[str]) -> float:
    """The cost factor of a node of `category` with `traits`; one for a society with no multipliers."""
    if not multipliers:
        return 1.0
    remedies = remedies or {}
    listed_traits = [trait for trait in traits if trait in multipliers]
    if category in multipliers:
        factor = multiplier_for(category, multipliers, remedies, done)
        for trait in listed_traits:
            factor *= multiplier_for(trait, multipliers, remedies, done) ** TRAIT_EXPONENT_WHEN_CRAFT_KNOWN
        return factor
    factor = 1.0
    for trait in listed_traits:
        factor *= multiplier_for(trait, multipliers, remedies, done)
    return factor
