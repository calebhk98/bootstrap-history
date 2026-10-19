"""What a country's relation toward another costs goods crossing the border between them (Complaint 598).

A state's tariff is a share of the goods' value at the source, charged on goods crossing from the other country
into its markets, and its embargo stops that crossing. Both are read from the relations store
(sim/agents/relations.py) each time a price is worked out, so a change mid-game is seen at once. The home state
is the destination of an import; a partner is the destination of an export, so any country's side counts."""
import math

from sim.agents.api import relations


def terms(sim, destination, source):
    """(tariff share, embargoed) that `destination` holds toward goods from `source`; none where the game keeps no stores."""
    stores = getattr(sim, "stores", None)
    if stores is None or destination == source:
        return 0.0, False
    return relations.tariff_on(stores, destination, source), relations.embargoes(stores, destination, source)


def home_country(sim):
    return getattr(sim, "civ", {}).get("id")


def import_terms(sim, partner):
    """What the home state holds toward goods from `partner`."""
    return terms(sim, home_country(sim), partner)


def export_terms(sim, partner):
    """What `partner`'s state holds toward goods from the home country."""
    return terms(sim, partner, home_country(sim))


def signature(sim, partners):
    """The terms both ways with each partner: part of the key a cached price table is valid for."""
    return tuple((import_terms(sim, partner), export_terms(sim, partner)) for partner in partners)


def duty_per_tonne(sim, source, destination, price_per_tonne):
    """Money the destination country's state charges on a tonne bought at `price_per_tonne` in `source`;
    infinite when it embargoes the crossing. Places are countries (the home one by its id)."""
    share, embargoed = terms(sim, destination, source)
    return math.inf if embargoed else share * price_per_tonne
