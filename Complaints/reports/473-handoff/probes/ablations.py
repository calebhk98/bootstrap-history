"""Experiment switches for probe_spin_years.py (ABLATE=name,name). Each patches data or a plain function the year calls;
none edits a kernel, so a warm kernel cache stays valid.
floor   the wage ask cannot fall below the subsistence wage (the floor is the outside option, not the plot's worth)
nowear  coin does not wear
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


SWITCHES = {"floor": _floor, "nowear": _nowear}
