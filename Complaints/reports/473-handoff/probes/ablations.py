"""Experiment switches for probe_spin_years.py (ABLATE=name,name). Each patches data or a plain function the year calls;
none edits a kernel, so a warm kernel cache stays valid.
floor   the wage ask cannot fall below the subsistence wage (the floor is the outside option, not the plot's worth)
nowear  coin does not wear
held    coin wears only as far as the mint struck in the year (the stock cannot fall; it rises where the mint strikes more)
"""
import dataclasses


def apply(names):
    for name in names.split(","):
        SWITCHES[name]()


def _floor():
    from sim.economy import economy as economy_module
    original = economy_module.labour_context

    def patched(*args, **kwargs):
        context = original(*args, **kwargs)
        return dataclasses.replace(context, ask_floor_per_worker_year=dict(context.subsistence_per_worker_year))
    economy_module.labour_context = patched


def _nowear():
    from sim.economy import metal_stock
    metal_stock.wear_share = lambda spec: None


def _held():
    from sim.economy import metal_stock, wear_year
    from sim.economy.types import EDGE_MINT
    original, share_of = wear_year._wear_coin, metal_stock.wear_share

    def patched(book, spec, order):
        worn = share_of(spec)
        if worn is None:
            return original(book, spec, order)
        share, purpose = worn
        supply = book.money_supply(spec.currency_id)
        struck = max(0.0, book.edge_net(EDGE_MINT, spec.currency_id))
        capped = min(share, struck / supply) if supply > 0.0 else share
        metal_stock.wear_share = lambda _spec: (capped, purpose)
        try:
            return original(book, spec, order)
        finally:
            metal_stock.wear_share = share_of
    wear_year._wear_coin = patched


SWITCHES = {"floor": _floor, "nowear": _nowear, "held": _held}
