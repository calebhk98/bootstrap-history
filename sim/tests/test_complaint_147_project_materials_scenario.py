"""Scenarios for Complaints/147 in a whole game: the real bill reads the game's own stock, output, supply and market
quotes; starting a project pays for the missing materials and delivers them; `why` shows the same total the engine
charges; `quote material` charges what `buy material` charges. The rules (stock first, own output shared between
projects, the instalments beyond a year's supply, the owned-supply note) are in test_complaint_147_project_materials."""
import os

from .harness import *  # noqa: F401,F403
from sim.engine.saveload import save_state, load_state
from sim.ui.proto.dispatch_money import _cmd_quote


def scenario(name, **claims):
    """One named scenario check: it passes when every claim holds, and names the claims that do not."""
    failed = sorted(label for label, held in claims.items() if not held)
    check(name, not failed, failed)


_LEAD, _SMALL = "lead_metallurgy", "tex_horizontal_loom"
_FIRST, _SECOND, _CHARCOAL = "case_hardening", "arc_light_lamp", "charcoal_kg"
_GUNPOWDER, _NITRE = "gunpowder", "nitre_kg"


def _own_held(game, node_id):
    return sum(row["held_from_own_output_tonnes"] for row in game.project_material_bill(node_id)["rows"]
               if row["material"] == _CHARCOAL)


# --- the bill reads the game: a year's supply, owned output shared between projects, owned supply, the market quote ------
game = unopened_sim(capital=5e7)
_nitre = next(row for row in game.project_material_bill(_GUNPOWDER)["rows"] if row["material"] == _NITRE)
_spot = game.material_purchase_cost(_nitre["material"], 0.0)[1]
_beyond = _nitre["missing_tonnes"] - _nitre["deliverable_now_tonnes"]
_bare_charcoal = next(row for row in game.project_material_bill(_FIRST)["rows"] if row["material"] == _CHARCOAL)
_owner = unopened_sim(capital=5e7)
_owner.state.holdings.forest_ha += 500
_owner_charcoal = next(row for row in _owner.project_material_bill(_FIRST)["rows"] if row["material"] == _CHARCOAL)
_small_priced = []
for _row in game.project_material_bill(_SMALL)["rows"]:
    _quote = game.material_trade_quote(_row["material"])
    _units_per_tonne = 1e6 if _row["material"].endswith("_g") else 1e3
    _expected = _row["needed_tonnes"] * _quote["buy_per_tonne"] * (1e3 / _units_per_tonne)
    _small_priced.append(abs(_row["cost_of_missing"] - _expected) <= 0.02 * max(_expected, 1e-9))
game.state.holdings.forest_ha += 4
_alone = _own_held(game, _SECOND)
game.initialize_project(_FIRST)
_after = _own_held(game, _SECOND)
scenario("scenario: the real bill prices the part beyond a year's supply at spot, shares owned output between projects and is the market's quote",
         part_beyond_a_years_supply_costs_the_spot_quote=_beyond > 0 and abs((_nitre["cost_of_missing"] - _nitre["cost_of_deliverable"]) - _beyond * _spot)
         <= 1e-6 * _nitre["cost_of_missing"],
         owned_supply_lowers_the_bill=_owner_charcoal["missing_tonnes"] < _bare_charcoal["missing_tonnes"]
         and _owner_charcoal["cost_of_missing"] < _bare_charcoal["cost_of_missing"],
         the_second_project_counts_only_the_output_left=_alone > 0 and _after < _alone,
         each_row_is_priced_at_the_quote_material_price=bool(_small_priced) and all(_small_priced))

# --- buying is demand; `quote material` is what `buy material` charges ---------------------------------------------------------
_RICH = 1e13    # buys any of the orders below whatever the material's price
_price = sim(capital=_RICH)
# a material the economy's market at the founder's tile offers and has a book for (a good the opening leaves with no seller
# there has no price to climb); the order is a share of what the market offers in a year, the small one a tenth of it
_BOUGHT = next(material for material in ("coal", "iron", "timber_m3", "copper")
               if _price.material_trade_quote(material) is not None
               and _price.economy.agent_price_response(_price.goods_market._economy_good(material), 0.0, 1.0,
                                                       _price.economy.acting_tile()) is not None)
_ORDER = 0.75 * _price.material_trade_quote(_BOUGHT)["market_available_tonnes_per_year"]
_one_tonne = _price.material_trade_quote(_BOUGHT)["buy_per_tonne"]
_before = _price.capital
_got = _price.buy_material_stock(_BOUGHT, _ORDER)
_average = (_before - _price.capital) / max(_got, 1e-9)
_smaller = sim(capital=_RICH)
_before_small = _smaller.capital
_smaller.buy_material_stock(_BOUGHT, _ORDER / 10.0)
_quote_game = sim(capital=_RICH)
_quoted = _cmd_quote(_quote_game, NODES, {"what": "material", "material": _BOUGHT, "n": _ORDER}, None)
_before_quote = _quote_game.capital
_quote_game.buy_material_stock(_BOUGHT, _ORDER)
scenario("scenario: a large purchase delivers and pays more a tonne, and the quote for an order is what buying it costs",
         delivered=_got > 0.95 * _ORDER, pays_more_than_the_one_tonne_quote=_average > _one_tonne,
         a_smaller_purchase_pays_less_a_tonne=(_before_small - _smaller.capital) / (_ORDER / 10.0) < _average,
         quote_is_what_buying_costs=abs(_quoted["to_buy_it"] - (_before_quote - _quote_game.capital)) < 1.0)

# --- `why` shows the rows and the same total the engine charges -----------------------------------------------------------------
_why = proto([{"cmd": "why", "id": _LEAD}])[0][0]
_why_rows = _why.get("material_rows") or []
_reference = sim()
scenario("scenario: `why` shows a row per material and the total the engine charges",
         rows_carry_needed_held_missing_and_cost=bool(_why_rows) and all(
             {"material", "needed_tonnes", "held_tonnes", "missing_tonnes", "cost_of_missing"} <= set(row) for row in _why_rows),
         headline_total_is_the_engines=abs(_why["cost"]["total"] - round(_reference.project_cost(_LEAD), 1)) < 1.0,
         headline_materials_is_the_cost_of_the_missing_part=abs(
             _why["cost"]["materials"] - round(_reference.project_material_bill(_LEAD)["cost_of_missing"], 1)) < 1.0,
         bounty_is_priced_from_the_same_cost=abs(
             _reference.bounty_price(_LEAD) - _reference.BOUNTY_PRICE_MULTIPLIER * _reference.project_cost(_LEAD)
             / _reference.opposition_factor(_LEAD)) < 1e-6)

# --- stock is drawn first; starting pays for the missing materials and delivers them; the bill is fixed at the start -----------
_start = sim(capital=5e7)


def _market_has_all_of(game, node_id):
    """True when the project needs materials and the economy offers every one of them in full: buying them all is
    then the rule's question, not whether this year's opening happens to leave an ore unmined."""
    rows = game.project_material_bill(node_id)["rows"]
    return bool(rows) and all((game.economy.agent_offered_tonnes(row["material"]) or 0.0) >= row["needed_tonnes"]
                              for row in rows)


def _starts_on_a_fresh_game(node_id):
    """Whether a game that holds the prerequisites and the hands starts the project (the state's wariness of a project is
    not what this scenario asks)."""
    fresh = sim(capital=5e7)
    run_it(fresh, *fresh.nodes[node_id]["pre"])
    fresh.artisans = fresh.scholars = 50.0
    return bool(fresh.start_project(node_id)[0])


# the named projects first; where the opening leaves one of their materials unmined, or the state forbids one, the first project in
# id order that the market stocks and a game can start
_STOCKED = next((node_id for node_id in (_LEAD, _FIRST, _SECOND, _GUNPOWDER) + tuple(sorted(NODES))
                 if _market_has_all_of(_start, node_id) and _starts_on_a_fresh_game(node_id)), None)
check("a project whose every material the economy offers in full exists for the stock scenario", _STOCKED is not None, _STOCKED)
_STOCKED = _STOCKED or _LEAD
_cost_empty = _start.project_cost(_STOCKED)
_needed = {row["material"]: row["needed_tonnes"] for row in _start.project_material_bill(_STOCKED)["rows"]}
_cash_before = _start.capital
_bought = {material: _start.buy_material_stock(material, tonnes) for material, tonnes in sorted(_needed.items())}
_paid = _cash_before - _start.capital
_cost_held = _start.project_cost(_STOCKED)
_held_bill = _start.project_material_bill(_STOCKED)
_start = sim(capital=5e7)   # a fresh game: the materials are missing at the start
run_it(_start, *_start.nodes[_STOCKED]["pre"])
_start.artisans = _start.scholars = 50.0
_fuel_key = _start._material_tag(sorted(_needed)[0])[0]
_stock_before = _start.material_stock_t(_fuel_key)
_cash_before = _start.capital
_started, _why_not = _start.start_project(_STOCKED)
_spent_at_start = _cash_before - _start.capital
_stock_after = _start.material_stock_t(_fuel_key)
_frozen = _start.project_cost(_STOCKED)
_path = os.path.join(tempfile.mkdtemp(), "bill.json")
save_state(_start, _path)
_reloaded = sim(capital=1.0)
load_state(_reloaded, _path)
_start.buy_material_stock(_BOUGHT, 500.0)
scenario("scenario: holding the materials lowers the bill, starting delivers them, and the bill is fixed at the start across a save",
         bought_in_full=all(abs(_bought[key] - _needed[key]) < 1e-6 for key in _needed),
         held_materials_take_their_value_off_the_cost=_cost_held <= _cost_empty - 0.9 * _paid,
         with_everything_held_nothing_is_missing=_held_bill["cost_of_missing"] < 1e-6,
         the_project_starts=bool(_started),
         materials_are_paid_for_at_the_start=_spent_at_start > 0.0 and _stock_after > _stock_before,
         the_bill_survives_save_and_load=abs(_reloaded.project_cost(_STOCKED) - _frozen) < 1e-6 and _frozen > 0,
         buying_stock_afterwards_leaves_a_running_bill_alone=abs(_start.project_cost(_STOCKED) - _frozen) < 1e-6)
