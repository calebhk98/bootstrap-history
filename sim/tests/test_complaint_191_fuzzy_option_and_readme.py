"""Complaint 191: fuzzy estimates are a normal game option; the settings default exists and is off. The new-game menu,
in-game options screen, settings default applied and save are the smoke test in
test_complaint_191_fuzzy_option_and_readme_smoke."""
from .harness import check
from sim.engine import settings as _settings

# ---- settings default ---------------------------------------------------------
check("settings: a default for fuzzy estimates exists and is off",
      _settings.CONFIG_DEFAULTS.get("default_fuzzy_estimates") is False,
      _settings.CONFIG_DEFAULTS)
