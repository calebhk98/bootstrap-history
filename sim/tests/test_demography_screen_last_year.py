"""Complaint 640: the demography screen's last year is read from the yearly record when no step has run in this process (a loaded game)."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.ui.proto.screen_demography import _last_year

record = [{"year": 100, "population": 990.0, "births": 40, "deaths": 30, "nutrition_ratio": 1.0},
          {"year": 101, "population": 1000.0, "births": 45, "deaths": 35, "nutrition_ratio": 0.98}]
loaded = SimpleNamespace(_last_demographic_step=None, view=lambda name: lambda: record)
check("a loaded game shows the newest record's births, deaths, nutrition and year",
      _last_year(loaded) == {"births": 45, "deaths": 35, "nutrition_ratio": 0.98, "year": 101}, _last_year(loaded))
empty = SimpleNamespace(_last_demographic_step=None, view=lambda name: lambda: [])
check("with no record and no step there is no last year", _last_year(empty) is None, _last_year(empty))
