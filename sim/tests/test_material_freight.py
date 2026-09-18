"""Regression tests for the freight crossing wired into sim/engine/economy.py:
material_freight_distance_km / material_freight_cost_per_kg /
material_freight_factor, and their effect on material_price_factor().

Uses the flat check()-at-import style most topics use (see harness.py),
because this exercises a live Sim through the engine, unlike sim/tests/
test_transport.py, which tests sim/world/transport.py entirely standalone
(see that module's own docstring for why it is written differently).

WHAT THIS GUARDS. sim/world/transport.py derives freight cost per tonne-km
from animal metabolism and road physics but had nothing in the engine
calling it (see docs/architecture/ENDOGENOUS_COSTS_AND_DOMAINS.md's
milestone table, "partly built, none wired"). These checks pin the crossing
that wires it in: a material this civilization already produces somewhere
in its own territory costs nothing extra to move (geography.json's own
per-region `minerals` table decides "produces," never an invented distance);
a material it does not costs MORE, by an amount traceable to transport.py's
own per-tonne-km feed and driver-hour figures and the real great-circle
distance between two real region centroids; and a material geography.json
has no location data for at all (gold, and everything outside the seven
tracked minerals) is left alone rather than guessed at, per CLAUDE.md SS3.1.
"""
from .harness import *  # noqa: F401,F403

from sim.world import transport as _transport
from sim.engine.data import haversine_km

# =============================================================================
# HOME IS HOME: a material produced somewhere in this civilization's own
# territory costs nothing extra to haul, regardless of how far that region
# sits from the civilization's own geographic centroid.
# =============================================================================
s_rome = sim(capital=1.0)
for _mat in ("iron", "copper", "coal"):
    check("Rome already mines %s somewhere in its own provinces, so freight "
          "distance is zero" % _mat,
          s_rome.material_freight_distance_km(_mat) == 0.0,
          s_rome.material_freight_distance_km(_mat))
    check("...and the freight markup on %s is therefore exactly 1.0, no "
          "change from the pre-freight price" % _mat,
          s_rome.material_freight_factor(_mat) == 1.0,
          s_rome.material_freight_factor(_mat))

# =============================================================================
# NOT HOME: a civilization whose own territory has none of a mineral pays a
# real, positive freight distance to the nearest place that has it - the
# mechanism this whole crossing exists to add. Han China's home region
# (`china`) carries real abundance for every one of the seven tracked
# minerals in geography.json (it is, in this project's own geography data,
# a major iron and coal producer - see data/world/geography.json), so coal
# is the clean case: americas_carib (mexica_1500's only home region) is the
# one region in the whole table with zero coal abundance of its own.
# =============================================================================
s_mexica = sim(civ="mexica_1500", capital=1.0)
_mexica_coal_km = s_mexica.material_freight_distance_km("coal")
check("Mesoamerica has no coal of its own anywhere in its home territory, "
      "so coal has a real, positive freight distance",
      _mexica_coal_km is not None and _mexica_coal_km > 0.0,
      _mexica_coal_km)
check("...and that turns into a freight markup strictly above 1.0 once it "
      "reaches material_price_factor()",
      s_mexica.material_freight_factor("coal") > 1.0,
      s_mexica.material_freight_factor("coal"))
check("...so the SAME node cost calculation prices coal higher for a "
      "civilization that must import it than for one that mines it at home",
      s_mexica.material_price_factor("coal") > s_rome.material_price_factor("coal"),
      (s_mexica.material_price_factor("coal"), s_rome.material_price_factor("coal")))

# =============================================================================
# THE DISTANCE IS REAL GEOGRAPHY, NOT INVENTED. material_freight_distance_km
# has to equal an independent great-circle calculation between this
# civilization's own home centroid and the nearest coal-bearing region's
# real lat/lon in data/world/geography.json - not a number this crossing
# made up for the occasion (CLAUDE.md SS3.1).
# =============================================================================
_home_lat, _home_lon = s_mexica._home_centroid
_candidates = [region_id for region_id, region in s_mexica._regions.items()
               if float((region.get("minerals") or {}).get("coal", 0.0)) > 0.0]
_expected_km = min(
    haversine_km(_home_lat, _home_lon,
                 s_mexica._regions[_rid]["lat"], s_mexica._regions[_rid]["lon"])
    for _rid in _candidates)
check("the freight distance matches an independent haversine calculation "
      "against geography.json's own region coordinates, to the metre",
      abs(_mexica_coal_km - _expected_km) < 1e-6,
      (_mexica_coal_km, _expected_km))

# =============================================================================
# THE COST IS TRACEABLE TO TRANSPORT.PY'S OWN TONNE-KM FIGURES. Recomputing
# material_freight_cost_per_kg by hand, from transport.py's own physical
# inputs for the same team/vehicle/surface plus this file's own book feed
# price and labourer wage, must match exactly - this crossing is not
# allowed to add a fudge factor transport.py's own numbers cannot explain.
# =============================================================================
_inputs = _transport.draught_freight_physical_inputs(
    _transport.OX, int(s_mexica.LAND_FREIGHT_TEAM_SIZE),
    _transport.CART, _transport.DIRT_TRACK)
_feed_price = s_mexica._book_price_per_kg(s_mexica.FREIGHT_FEED_PRICE_MATERIAL)
_wage = WAGES[s_mexica.FREIGHT_DRIVER_WAGE_TRADE]
_expected_denarii_per_tonne_km = (_inputs.feed_kg_per_tonne_km * _feed_price
                                   + _inputs.driver_hours_per_tonne_km * _wage)
_expected_cost_per_kg = _expected_denarii_per_tonne_km * _mexica_coal_km / 1000.0
check("coal's freight cost per kilogram matches transport.py's own feed and "
      "driver-hour figures times the real distance, exactly",
      abs(s_mexica.material_freight_cost_per_kg("coal") - _expected_cost_per_kg) < 1e-9,
      (s_mexica.material_freight_cost_per_kg("coal"), _expected_cost_per_kg))
check("doubling the distance doubles the freight cost - transport.py's "
      "per-tonne-km rate is constant, only distance multiplies it",
      abs(2.0 * s_mexica.material_freight_cost_per_kg("coal")
          - _expected_denarii_per_tonne_km * (2.0 * _mexica_coal_km) / 1000.0) < 1e-9,
      s_mexica.material_freight_cost_per_kg("coal"))

# =============================================================================
# AN UNLOCATED MATERIAL IS LEFT ALONE, NEVER GUESSED AT (CLAUDE.md SS3.1).
# gold has no entry in geography.json's per-region `minerals` table (it is
# priced through pop_scale, not mineral_scale, elsewhere in this file), so
# its freight distance is genuinely unknown and this crossing must say so
# rather than inventing one, and its price must be completely unaffected.
# =============================================================================
check("gold has no located-region data in geography.json, so its freight "
      "distance is reported as unknown rather than guessed",
      s_mexica.material_freight_distance_km("gold") is None,
      s_mexica.material_freight_distance_km("gold"))
check("...so its freight cost is exactly zero",
      s_mexica.material_freight_cost_per_kg("gold") == 0.0,
      s_mexica.material_freight_cost_per_kg("gold"))
check("...and its freight markup is exactly 1.0, for every civilization, "
      "not just the ones that already hold a gold-bearing region",
      s_mexica.material_freight_factor("gold") == 1.0 == s_rome.material_freight_factor("gold"),
      (s_mexica.material_freight_factor("gold"), s_rome.material_freight_factor("gold")))

# =============================================================================
# THE MARKUP COMPOSES MULTIPLICATIVELY, THE SAME SHAPE AS EVERY OTHER FACTOR
# project_cost() STACKS (civ_cost_factor, material_cost_factor, and this
# function's own pre-existing scarcity curve) - material_price_factor() must
# equal the scarcity component TIMES the freight component, not some other
# combination, so it composes correctly rather than silently double- or
# under-counting when project_cost() multiplies several of these together.
# =============================================================================
_scarcity_only = s_mexica.material_price_factor("coal") / s_mexica.material_freight_factor("coal")
check("material_price_factor is exactly the scarcity curve times the "
      "freight markup, not some other combination of the two",
      abs(s_mexica.material_price_factor("coal")
          - _scarcity_only * s_mexica.material_freight_factor("coal")) < 1e-9,
      s_mexica.material_price_factor("coal"))
