"""Goods the home cannot make cross the partner border (Complaints/347, 322).

Silk needs sericulture, which the home society did not hold; the partner that did holds it as
starting knowledge and offers silk at its own cost plus freight plus the merchants' terms. A crop
that grows only in some climates is made only where the territory has one of them (a production
entry's `grown_in_climate_classes`, read against the Koppen class of the territory's tiles), and
households want spices through the seasoning need.
"""
from .harness import *  # noqa: F401,F403
from functools import partial

sim = partial(sim, agent_economy=False)   # legacy: pins luxury imports paid in coin through the engine's own foreign trade; see test_economy_agent_foreign.py


from sim.geography import crop_climate
from sim.geography.api import tiles_held
from sim.engine import foreign_economies as _foreign_module
from sim.engine.data import goods_provenance, load_civ
from sim.engine.prices import default_production_entries

PARTNER = "han_china_100ad"
HOME = "rome_100ad"

_shipped_records = _foreign_module.foreign_economy_records
_foreign_module.foreign_economy_records = lambda: tuple(
    dict(record, enabled=True) for record in _shipped_records())

entries = default_production_entries()

# --- the sericulture chain is made of stages, each with its own labour, land and basis.
for stage in ("mulberry_leaves_kg", "silk_cocoon_kg", "silk_kg"):
    check("%s is a production entry with a stated basis and yield basis" % stage,
          stage in entries and len(entries[stage]["yield_basis"]) > 200 and entries[stage]["basis"], None)
check("cocoons are reared from mulberry leaf",
      "mulberry_leaves_kg" in entries["silk_cocoon_kg"]["inputs"], None)
check("silk is reeled and woven from cocoons and carries no land of its own",
      "silk_cocoon_kg" in entries["silk_kg"]["inputs"] and "land_hectare_years" not in entries["silk_kg"], None)
check("the leaf, which stands on the land, is what carries the hectare",
      entries["mulberry_leaves_kg"].get("land_hectare_years", 0) > 0, None)

# --- the partner holds sericulture at its start; the home does not.
han_techs = set(load_civ(PARTNER)["starting_techs"])
rome_techs = set(load_civ(HOME)["starting_techs"])
check("the partner starts with every node sericulture needs",
      {"tx2_sericulture", "tx2_silk_fibre"} <= han_techs, None)
check("the partner holds the eggs itself, with no stock node and no Indian Ocean route",
      load_civ(PARTNER)["opening_stock"].get("silkworm_eggs_kg", 0) > 0
      and "sea_monsoon_route" not in han_techs and not {n for n in han_techs if n.endswith("_stock")}, None)
check("the home does not hold sericulture",
      "tx2_sericulture" not in rome_techs, None)
check("silk is solved for the partner and not for the home",
      goods_provenance(frozenset(han_techs), civilization_id=PARTNER).get("silk_kg") == "solved"
      and goods_provenance(frozenset(rome_techs), civilization_id=HOME).get("silk_kg") != "solved", None)

# --- the climate gate.
check("a class list admits a territory holding one of the classes",
      crop_climate.territory_suits({"grown_in_climate_classes": ["Aw", "Cwa"]}, {"Cwa", "BWh"}), None)
check("...and refuses one that holds none",
      not crop_climate.territory_suits({"grown_in_climate_classes": ["Aw"]}, {"Csa", "BWh"}), None)
check("an entry that names no classes grows anywhere",
      crop_climate.territory_suits({}, {"Csa"}), None)
check("a territory's classes follow its home regions' tiles",
      "Csa" in crop_climate.territory_classes(tiles_held(load_civ(HOME))) and "Aw" not in crop_climate.territory_classes(tiles_held(load_civ(HOME))), None)
check("the pepper entry names tropical classes and the home territory has none",
      entries["pepper_kg"]["grown_in_climate_classes"]
      and not crop_climate.entry_grows_in(entries["pepper_kg"], tiles_held(load_civ(HOME))), None)
provenance = goods_provenance(frozenset(rome_techs), civilization_id=HOME)
check("a crop the home climate cannot grow is not solved at home, but still priced",
      provenance.get("cassia_kg") not in (None, "solved"), provenance.get("cassia_kg"))
check("the partner's southern tiles grow cassia",
      goods_provenance(frozenset(han_techs), civilization_id=PARTNER).get("cassia_kg") == "solved", None)

# --- households want spices.
from sim.engine import need_data  # noqa: E402
from sim.engine.data import ROOT  # noqa: E402
needs = need_data.load_needs(ROOT)
check("a seasoning need exists and spices satisfy it",
      "seasoning" in needs["needs"] and "pepper_kg" in needs["goods"]
      and "seasoning" in needs["goods"]["cassia_kg"]["satisfies"], None)

# --- the trade rule finds the partner's silk and cassia, and prices them.
home = sim(civ=HOME, capital=1e9)
facts = home._foreign_economy_facts(PARTNER)
check("silk is a trade key the partner alone can make",
      home._foreign_trade_key("silk_kg", facts) is not None
      and home._foreign_trade_key("silk_kg", facts)[1:] == (False, True), home._foreign_trade_key("silk_kg", facts))
check("the home's unmet household demand for silk is positive",
      home.home_unmade_demand_tonnes("silk_kg") > 0.0, home.home_unmade_demand_tonnes("silk_kg"))
home_price, partner_price = home._foreign_price_pair("silk_kg", facts)
check("a side that cannot make the good takes the maker's cost as its own",
      abs(home_price - partner_price) < 1e-9, (home_price, partner_price))
terms = home.trader_terms(PARTNER, facts, home_price, partner_price)
check("merchants add a cost over the partner's price on top of freight",
      terms.cost_share_of_price > 0.0 and facts["freight_per_tonne"] > 0.0, terms)
_capacity_before = home._market_entry("silk_kg")["capacity_tonnes"]
for _year in range(3):
    home.step()
check("a good only the partner makes gets no home capacity from its dear price",
      home._market_entry("silk_kg")["capacity_tonnes"] == _capacity_before, None)
check("silk is imported once the partner offers it",
      home.market_state("silk_kg")["trade_tonnes"] > 0.0, home.market_state("silk_kg").get("trade_tonnes"))
payments = home.foreign_balance_of_payments(PARTNER)
check("the import is paid for in coin that leaves the home",
      payments["goods_in_value"] > 0.0 and payments["coin_paid_out_units"] > 0.0, payments)

# --- cassia, which the partner grows and the home climate does not, crosses too.
check("the partner's cassia reaches the home market",
      home.market_state("cassia_kg")["trade_tonnes"] > 0.0, home.market_state("cassia_kg").get("trade_tonnes"))
