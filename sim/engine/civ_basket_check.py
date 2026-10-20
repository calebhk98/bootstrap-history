"""Goods a civilisation's households buy but nothing available at its start can supply.

Pure data check. A basket good (one in data/world/needs.json) is supplied when some production
entry for it is ungated or gated on a node the civilisation holds, or when an enabled foreign
economy that exists in the civilisation's year holds such a gate and does not refuse to sell it.
A good with no production entry at all is raw (mined, grown, gathered) and is not judged here.
A civilisation lists the rest in `unsupplied_basket_goods` ({good: reason}); the reason "unreviewed"
only warns.

Used by `simulator.py validate`, and importable for tests.
"""
from types import SimpleNamespace

from sim.agents.api import exports_allowed

from .civ_start_check import UNREVIEWED, MINIMUM_REASON_LENGTH, _producers


def _makes(held, gates):
    return any(gate is None or gate in held for gate in gates)


def _sells_abroad(partner, good):
    """Whether the partner's state, at its start, lets the good leave: its export policy answers from the
    monopolies its data gives it."""
    state = SimpleNamespace(record=SimpleNamespace(state_monopolies=set(partner.get("state_monopolies") or ())),
                            decision_policy=None)
    return bool(exports_allowed(state, [good]))


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


def _obtainable(held, by_material, bought_in):
    """Materials a holder of `held` nodes can end up with: raw ones (no recipe), those in `bought_in`, and
    those some recipe makes whose gate is held and whose every input is itself obtainable (a fixed point,
    so a cycle of recipes with no way in is not obtainable)."""
    inputs_of = {}
    for recipes in by_material.values():
        for _gate, entry in recipes:
            for material in entry.get("inputs") or ():
                inputs_of.setdefault(material, [])
    have = {material for material in inputs_of if material not in by_material} | set(bought_in)
    changed = True
    while changed:
        changed = False
        for material, recipes in by_material.items():
            if material in have:
                continue
            if any(_makes(held, [gate]) and all(item in have or item not in by_material
                                                 for item in entry.get("inputs") or ())
                   for gate, entry in recipes):
                have.add(material)
                changed = True
    return have


def unsupplied_basket_goods(civilisation_id, civilisations, production, goods, economies):
    """Basket goods with a recipe, none of which the civilisation can run to the end of its inputs, or buy
    from a partner that can. A recipe whose own gate is held but whose input has no held chain does not count."""
    civilisation = civilisations[civilisation_id]
    by_material = _producers(production)
    held = set(civilisation.get("starting_techs") or ())
    partners = _partners_for(civilisation_id, civilisation, civilisations, economies)
    partner_makes = [(partner, _obtainable(set(partner.get("starting_techs") or ()), by_material, ()))
                     for partner in partners]
    candidates = [good for good in goods if (goods[good] or {}).get("bought_by_households") is not False]
    bought_in = {good for good in by_material
                 if any(good in made and _sells_abroad(partner, good) for partner, made in partner_makes)}
    own = _obtainable(held, by_material, bought_in)
    return [good for good in sorted(candidates) if good in by_material and good not in own]


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
