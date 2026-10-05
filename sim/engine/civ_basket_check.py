"""Goods a civilisation's households buy but nothing available at its start can supply.

Pure data check. A basket good (one in data/world/needs.json) is supplied when some production
entry for it is ungated or gated on a node the civilisation holds, or when an enabled foreign
economy that exists in the civilisation's year holds such a gate and does not refuse to sell it.
A good with no production entry at all is raw (mined, grown, gathered) and is not judged here.
A civilisation lists the rest in `unsupplied_basket_goods` ({good: reason}); the reason "unreviewed"
only warns.

Used by `simulator.py validate`, and importable for tests.
"""
from .civ_start_check import UNREVIEWED, MINIMUM_REASON_LENGTH, _producers


def _makes(held, gates):
    return any(gate is None or gate in held for gate in gates)


def _partners_for(civilisation_id, civilisation, civilisations, economies):
    year = civilisation.get("year")
    found = []
    for record in economies:
        partner_id = record.get("civilization")
        if not record.get("enabled") or partner_id == civilisation_id or partner_id not in civilisations:
            continue
        if year is not None and not record.get("from_year", year) <= year <= record.get("until_year", year):
            continue
        found.append(civilisations[partner_id])
    return found


def unsupplied_basket_goods(civilisation_id, civilisations, production, goods, economies):
    """Basket goods with a recipe, none of which the civilisation can run or buy from a partner."""
    civilisation = civilisations[civilisation_id]
    by_material = _producers(production)
    held = set(civilisation.get("starting_techs") or ())
    partners = _partners_for(civilisation_id, civilisation, civilisations, economies)
    missing = []
    for good in sorted(goods):
        gates = [gate for gate, _entry in by_material.get(good, ())]
        if not gates or _makes(held, gates):
            continue
        if any(good not in (partner.get("will_not_sell") or ())
               and _makes(set(partner.get("starting_techs") or ()), gates) for partner in partners):
            continue
        missing.append(good)
    return missing


def basket_supply_findings(civilisations, production, goods, economies):
    """(errors, warnings): an unsupplied good needs a reason in the civilisation's own file, and a
    listed good that is in fact supplied is a stale entry."""
    errors, warnings = [], []
    for name, civilisation in sorted(civilisations.items()):
        declared = civilisation.get("unsupplied_basket_goods") or {}
        missing = unsupplied_basket_goods(name, civilisations, production, goods, economies)
        for good in missing:
            reason = declared.get(good)
            text = "%s: households buy %s but no technique it holds or partner supplies it" % (name, good)
            if reason is None:
                errors.append(text + "; gate the recipe on a node it holds, or declare the good in "
                              "unsupplied_basket_goods with a reason")
            elif reason == UNREVIEWED:
                warnings.append(text + "; reason is unreviewed")
            elif len(reason) < MINIMUM_REASON_LENGTH:
                errors.append(text + "; its unsupplied_basket_goods reason is too short to be a reason")
        for good in sorted(set(declared) - set(missing)):
            errors.append("%s: unsupplied_basket_goods lists %s, which it can now supply; remove the entry"
                          % (name, good))
    return errors, warnings
