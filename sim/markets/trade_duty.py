"""What a country's relation toward another costs goods crossing the border between them (Complaint 598).

A state's tariff is a share of the goods' value at the source, charged on goods crossing from the other country
into its markets, and its embargo stops that crossing. Both are read from the relations store (the `store_book` view)
each time a price is worked out, so a change mid-game is seen at once. The home state is the destination of an import; a
partner is the destination of an export, so any country's side counts. `world` is what the port reads of the game
(port_world.py): its `civ` and `border_terms`."""
import math

from sim.agents.api import relations


def terms_in_book(book, destination, source):
    """(tariff share, embargoed) that the state of `destination` holds toward goods crossing from `source`, read from the
    relations store."""
    return relations.tariff_on(book, destination, source), relations.embargoes(book, destination, source)


def terms(world, destination, source):
    """(tariff share, embargoed) that `destination` holds toward goods from `source`."""
    if destination == source:
        return 0.0, False
    return world.border_terms(destination, source)


def home_country(world):
    return world.civ.get("id")


def import_terms(world, partner):
    """What the home state holds toward goods from `partner`."""
    return terms(world, home_country(world), partner)


def export_terms(world, partner):
    """What `partner`'s state holds toward goods from the home country."""
    return terms(world, partner, home_country(world))


def signature(world, partners):
    """The terms both ways with each partner: part of the key a cached price table is valid for."""
    return tuple((import_terms(world, partner), export_terms(world, partner)) for partner in partners)


def duty_per_tonne(world, source, destination, price_per_tonne):
    """Money the destination country's state charges on a tonne bought at `price_per_tonne` in `source`;
    infinite when it embargoes the crossing. Places are countries (the home one by its id)."""
    share, embargoed = terms(world, destination, source)
    return math.inf if embargoed else share * price_per_tonne
