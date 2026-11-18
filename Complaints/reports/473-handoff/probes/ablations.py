"""Experiment switches for probe_spin_years.py (ABLATE=name,name). Each patches data or a plain function the year calls;
none edits a kernel, so a warm kernel cache stays valid.
floor   the wage ask cannot fall below the subsistence wage (the floor is the outside option, not the plot's worth)
nowear  coin does not wear
nominal     the wage ask's base and floor stay at the first year's figures (wages do not follow prices by rule)
fastask     unsold hours cut next year's wage ask by half their share, not about a ninth
notoolbids  households place no bids for the tools their own plots wear
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


def _nominal():
    """The wage ask's price-indexed base and floor are held at the first year's figures: wages move only with the labour market."""
    from sim.economy import economy as economy_module
    original = economy_module.labour_context
    held = {}

    def patched(*args, **kwargs):
        context = original(*args, **kwargs)
        if not held:
            held["subsistence"] = dict(context.subsistence_per_worker_year)
            held["floor"] = dict(context.ask_floor_per_worker_year)
        return dataclasses.replace(context, subsistence_per_worker_year=dict(held["subsistence"]),
                                   ask_floor_per_worker_year=dict(held["floor"]))
    economy_module.labour_context = patched


def _fastask():
    """Hours left unsold cut next year's ask by half their share (the declared rule cuts by about a ninth of it)."""
    from sim.labour.market import clearing_tail
    real = clearing_tail.kernel

    class Proxy:
        def __getattr__(self, name):
            return getattr(real, name)

        def finish_markets(self, *args):
            args = list(args)
            args[21] = 1.0 - 0.5 ** (1.0 / args[20])        # the cut a round that compounds to a half over the year's rounds
            return real.finish_markets(*args)
    clearing_tail.kernel = Proxy()


def _notoolbids():
    from sim.economy import year_order_sources
    year_order_sources.tool_wear.tool_bids = lambda *args, **kwargs: []


def _woodland():
    """A producer whose recipe is bound to a declared site (standing timber, a seam) asks for none of the tile's cropland."""
    from sim.economy import land_market, sites
    original = land_market.demands_of

    def demands_of(setup, record, view, wanted_runs):
        by_recipe = sites.limits_by_recipe(setup.site_limits)
        sited = {producer_id for producer_id, producer in record.producers.items() if by_recipe.get(producer.recipe_id)}
        return [demand for demand in original(setup, record, view, wanted_runs) if demand.agent_id not in sited]
    land_market.demands_of = demands_of


def _fieldsall():
    """Every recipe with land in its data asks for cropland, sited or not (the rule before Update 36)."""
    from sim.economy import land_market
    land_market.cropland_recipes = lambda land_per_run, site_limits: frozenset(name for name, hectares in land_per_run.items() if hectares > 0.0)


def _noplottools():
    """The opening neither seeds the plots' tools nor adds their wear to final demand."""
    from sim.economy import opening_plot_tools
    opening_plot_tools.add_wear = lambda *args: None
    opening_plot_tools.seed_moves = lambda *args: []


def _nocarry():
    """Each opening pass gives the plots all the land the cohorts hold, whatever the last pass's land market left them."""
    from sim.economy import opening_own
    opening_own.plot_land = lambda held, kept_last: dict(held)


def _farmsfirst():
    """A hectare of the households' own plots is counted as returning nothing every year, as at the opening, so a producer
    that bids anything for contested land takes it before the plots."""
    from sim.economy import land_lease_year
    original = land_lease_year.own_plot_returns
    land_lease_year.own_plot_returns = lambda *args, **kwargs: {tile: 0.0 for tile in original(*args, **kwargs)}


def _plotsfirst():
    """The plots keep every hectare the households work before any producer is granted land, whatever is bid."""
    from sim.economy import land_lease_year
    land_lease_year.own_plot_returns = lambda *args, **kwargs: {}


SWITCHES = {"farmsfirst": _farmsfirst, "plotsfirst": _plotsfirst, "floor": _floor, "nowear": _nowear, "held": _held, "notoolbids": _notoolbids, "nominal": _nominal, "fastask": _fastask,
            "woodland": _woodland, "fieldsall": _fieldsall, "noplottools": _noplottools, "nocarry": _nocarry}
