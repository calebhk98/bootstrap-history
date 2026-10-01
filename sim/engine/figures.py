"""Headline figures that explain their own change.

A figure registers once with `@figure(name, label, unit)` on a function that
reads the engine and returns {"value", "components", "flows", "drivers"}, all
but value optional:
  components  named parts of the value; the change in each is its cause
  flows       named amounts that fed the change directly (for a stock)
  drivers     named inputs that are not additive, shown beside the causes
`figure_snapshot` records every figure once a year; `explain_figure` sets the
live value against the latest earlier record. Whatever the named parts leave
out is reported as its own cause, so the causes always add up to the change.
"""

FIGURES = {}   # name -> {"name", "label", "unit", "digits", "compute"}

UNEXPLAINED_CAUSE = "not itemised (commands, hazards and one-off payments)"
DEFAULT_DIGITS = 1


def figure(name, label, unit="", digits=DEFAULT_DIGITS):
    """Decorator: register `compute(sim)` as the figure `name`."""
    def register(compute):
        FIGURES[name] = {"name": name, "label": label, "unit": unit,
                         "digits": digits, "compute": compute}
        return compute
    return register


def _round(value, digits):
    return None if value is None else round(float(value), digits)


def read_figure(sim, name):
    """The figure's value, components, flows and drivers now, rounded."""
    entry = FIGURES[name]
    digits = entry["digits"]
    raw = entry["compute"](sim) or {}
    return {
        "value": _round(raw.get("value"), digits),
        "components": {cause: _round(part, digits)
                       for cause, part in (raw.get("components") or {}).items()},
        "flows": {cause: _round(part, digits)
                  for cause, part in (raw.get("flows") or {}).items()},
        "drivers": {driver: _round(part, 4)
                    for driver, part in (raw.get("drivers") or {}).items()},
    }


def figure_snapshot(sim):
    """Every registered figure read now, for the yearly history."""
    return {name: read_figure(sim, name) for name in FIGURES}


def _cause_name(cause):
    return cause[1:].replace("_", " ") if cause.startswith("_") else cause


def _component_causes(current, previous):
    causes = []
    for cause in sorted(current, key=lambda key: -abs(current[key] or 0.0)):
        now = current[cause]
        before = (previous or {}).get(cause, 0.0) if previous is not None else None
        causes.append({"cause": _cause_name(cause), "previous": before, "current": now,
                       "contribution": None if before is None else now - before})
    for cause in sorted(set(previous or {}) - set(current)):
        causes.append({"cause": _cause_name(cause), "previous": previous[cause], "current": 0.0,
                       "contribution": -previous[cause]})
    return causes


def explain_figure(sim, name, history):
    """What `name` was last year, is now, and what moved it.

    `history` is the yearly records (each with a "figures" map); the latest one
    from an earlier year is "last year".
    """
    entry = FIGURES[name]
    digits = entry["digits"]
    now = read_figure(sim, name)
    earlier = [record for record in (history or [])
               if record.get("year", sim.year) < sim.year and name in (record.get("figures") or {})]
    before = earlier[-1]["figures"][name] if earlier else None
    out = {"ok": True, "name": name, "label": entry["label"], "unit": entry["unit"],
           "current": now["value"], "previous": None if before is None else before["value"],
           "previous_year": None if before is None else earlier[-1]["year"]}
    if before is None or now["value"] is None or before["value"] is None:
        out["change"] = None
        out["causes"] = _component_causes(now["components"], None) + [
            {"cause": cause, "previous": None, "current": part, "contribution": part}
            for cause, part in now["flows"].items()]
        out["note"] = "no earlier year recorded yet: step a year and ask again to see what moved it"
        out["drivers"] = [{"driver": driver, "previous": None, "current": part}
                          for driver, part in now["drivers"].items()]
        return out
    change = round(now["value"] - before["value"], digits)
    causes = _component_causes(now["components"], before["components"])
    causes += [{"cause": _cause_name(cause), "previous": None, "current": part, "contribution": part}
               for cause, part in now["flows"].items()]
    explained = sum(cause["contribution"] or 0.0 for cause in causes)
    leftover = round(change - explained, digits)
    if abs(leftover) >= 10 ** -digits:
        causes.append({"cause": UNEXPLAINED_CAUSE, "previous": None, "current": None,
                       "contribution": leftover})
    for cause in causes:
        if cause["contribution"] is not None:
            cause["contribution"] = round(cause["contribution"], digits)
    out["change"] = change
    out["causes"] = causes
    out["drivers"] = [{"driver": driver, "previous": before["drivers"].get(driver), "current": part}
                      for driver, part in now["drivers"].items()]
    return out
