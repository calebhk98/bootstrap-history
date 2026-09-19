"""Money, buying and trading commands: bounty, buy, sell, money, quote,
close, withdraw, bribe - everything whose job is spending or reporting
capital, as opposed to labour or a project's own progress.

dispatch.py stays the composition point - the command table, the
dispatcher, and every name protocol.py's shim re-exports - and imports
these handlers back from here (see dispatch.py's own docstring for why
these live in a separate file).
"""

from .util import _qty


def _cmd_bounty(sim, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s); nothing more can be bought. 'state' shows where you finished and how far you got" % ended}
    node_id = cmd.get("id")
    if node_id not in nodes:
        return {"ok": False, "error": "unknown node id %r" % node_id}
    if node_id in sim.done:
        return {"ok": False, "error": "%s is already done" % node_id}
    # ELIGIBILITY FIRST, ALWAYS: since an active project's prerequisites
    # are already satisfied (that is what let it start), eligibility here
    # depends only on craft recognition, so checking it before the
    # "already active" branch costs nothing and never sends a player to
    # stop something that could not become a bounty anyway.
    if not sim.bounty_eligible(node_id):
        node = nodes[node_id]
        missing = [prereq_id for prereq_id in node["pre"] if prereq_id not in sim.done]
        if missing:
            # SAME FOG FILTER `why` USES, not a second one: printing a
            # missing prerequisite by raw id regardless of whether the
            # player has ever heard of it would leak it as a spoiler.
            return {"ok": False, "error": sim.missing_prereq_message(missing)}
        return {"ok": False,
                "error": "not bounty-eligible (category %s): a craftsman "
                         "in %s could not recognise success at this without "
                         "understanding the theory, so there is nothing to "
                         "award the prize for. A bounty works where the craft "
                         "already exists here and success is visible."
                         % (node["cat"],
                            sim.civ.get("name", "this society"))}
    if node_id in sim.active:
        return {"ok": False, "error": "%s is already active; stop it first if you want "
                                      "to switch to a bounty instead" % node_id}
    price = (nodes[node_id]["_total_cost"] * 2.5 * sim.civ_cost_factor(node_id)
             * sim.material_cost_factor(node_id) * sim.cost_money_factor())
    if not sim.post_bounty(node_id):
        return {"ok": False, "error": "cannot afford the bounty: needs about %.0f denarii, "
                                      "you have %.0f. Earn or wait, then try again" % (price, sim.capital)}
    return {"ok": True, "posted": node_id, "price": round(price, 1), "capital": round(sim.capital, 1)}



def _buy_forest(sim, cmd, quantity):
    got = sim.buy_forest(quantity)
    if got <= 0:
        return {"ok": False, "error": "cannot afford %.0f ha of coppice woodland "
                                      "(you have %.0f denarii)" % (quantity, sim.capital)}
    return {"ok": True, "bought_ha": got, "forest_ha": round(sim.forest_ha, 1),
            "capital": round(sim.capital, 1)}


def _buy_nitre(sim, cmd, quantity):
    got = sim.build_nitre(quantity)
    if got <= 0:
        return {"ok": False,
                "error": "cannot afford %.0f square metres of nitre bed "
                         "(that is %s denarii and you have %s). Nothing "
                         "was changed."
                         % (quantity, "{:,.0f}".format(quantity * sim.NITRE_COST_PER_M2
                                                * sim.price_index),
                            "{:,.0f}".format(sim.capital))}
    return {"ok": True, "laid_m2": got,
            "nitre_bed_m2": round(sim.nitre_bed_m2, 1),
            "saltpetre_it_yields_per_year_tonnes":
                round(sim.nitre_bed_m2 * sim.NITRE_YIELD_T_PER_M2, 3),
            "capital": round(sim.capital, 1)}


def _buy_farm(sim, cmd, quantity):
    got = sim.invest_farm(quantity)
    if got <= 0:
        return {"ok": False, "error": "cannot afford that farmland"}
    return {"ok": True, "bought_farm_hectares": got,
            "farm_hectares": round(sim.farm_hectares, 1),
            "food_cost_factor": round(sim.essential_price_ratio(), 3),
            "capital": round(sim.capital, 1)}


def _buy_housing(sim, cmd, quantity):
    got = sim.build_worker_housing(quantity)
    if got <= 0:
        return {"ok": False, "error": "cannot afford that worker housing"}
    return {"ok": True, "built_worker_housing_places": got,
            "worker_housing_places": round(sim.worker_housing_places, 1),
            "capital": round(sim.capital, 1)}


def _buy_school(sim, cmd, quantity):
    trade = str(cmd.get("trade") or cmd.get("material") or "").lower()
    school_founded, why = sim.found_trade_school(trade, quantity)
    if not school_founded:
        return {"ok": False, "error": why}
    return {"ok": True, "trade": trade, "new_training_seats": quantity,
            "trade_school_seats": sim.trade_schools[trade],
            "market_supply_hours_per_year": round(sim.market_supply(trade), 1),
            "capital": round(sim.capital, 1)}


def _buy_material(sim, cmd, quantity):
    material = cmd.get("material")
    got = sim.buy_material_stock(material, quantity)
    if got <= 0:
        return {"ok": False, "error": "cannot buy that quantity at the current material quote"}
    return {"ok": True, "material": material, "bought_tonnes": got,
            "stock_on_hand_tonnes": sim.material_stock_t(material),
            "capital": round(sim.capital, 1)}


def _buy_mine(sim, cmd, quantity):
    mat = cmd.get("material")
    # GENERALISED beyond the seven hand-named metals (see
    # economy.py's mineable()/mine_catalog_hint(), and
    # COMMODITY_DYNAMISM.md for why a closed list here would be a real
    # bug: "no mine, no supply lever" for anything else the tree ever
    # asks a node to buy). The membership check lives in economy.py's
    # mineable(); this file calls it rather than keeping its own list.
    if not sim.mineable(mat):
        return {"ok": False, "error": "material must be one of: "
                                      + sim.mine_catalog_hint()}
    # partial=False: a mine you ask for by name must be bought in full or
    # not at all, never spend every denarius you have and hand back a
    # fraction without asking.
    price = sim.mine_quote(mat, quantity).get("to_sink_it") if hasattr(sim, "mine_quote") else None
    got = sim.open_mine(mat, quantity, partial=False)
    if got <= 0:
        if price is not None and price > sim.capital:
            return {"ok": False,
                    "error": "%.0f tonnes a year of %s costs %s denarii to "
                             "sink and you have %s. Nothing was changed - ask "
                             "for what you can pay for, or check the price "
                             'first with {"cmd":"quote","what":"mine",'
                             '"material":"%s","n":%g}.'
                             % (float(quantity), mat, "{:,.0f}".format(price),
                                "{:,.0f}".format(sim.capital), mat, float(quantity))}
        return {"ok": False, "error": "could not commission any %s capacity right now "
                                      "(ceiling reached, or standing too low for a "
                                      "concession that size)" % mat}
    # Say what was actually commissioned and WHEN it arrives. A tester
    # asked for 999,999,999 tonnes a year, silently got 59, and found
    # ready_year was always null so there was no way to know whether the
    # workings would appear in four years or ninety-five. Both of those
    # are the model being coy about its own arithmetic.
    tranche = [entry for entry in getattr(sim, "mine_tranches", []) if entry[0] == mat]
    ready = min((entry[2] for entry in tranche), default=None)
    asked = float(quantity)
    reply = {"ok": True, "material": mat,
             "you_asked_for_t_per_yr": asked,
             "commissioned_t_per_yr": round(got, 2),
             "ready_year": ready,
             "years_until_producing": (None if ready is None
                                       else round(ready - sim.year, 1)),
             "already_producing_t_per_yr": round(sim.mine_capacity.get(mat, 0.0), 2),
             "capital": round(sim.capital, 1)}
    if got < asked * 0.999:
        reply["note"] = ("less than you asked for: limited by capital, by the "
                         "ceiling your standing supports, or both. Nothing was "
                         "wasted, you paid only for what was sunk.")
    return reply


def _buy_slaves(sim, cmd, quantity):
    sim._last_buy_refusal = None
    got = sim.buy_slaves(int(quantity))
    if got <= 0 and getattr(sim, "_last_buy_refusal", None):
        return {"ok": False, "error": sim._last_buy_refusal}
    if got <= 0:
        # Quote the price actually asked, not a flat per-head figure: a
        # large purchase bids the local market up, and saying "300 each"
        # while charging far more is the model lying to the player.
        quote = sim.slave_quote(int(quantity))
        return {"ok": False,
                "error": "cannot afford %d slaves: %.0f denarii "
                         "(%.0f each after the market moves against a purchase "
                         "this size) and you have %.0f"
                         % (int(quantity), quote, quote / max(1, int(quantity)), sim.capital)}
    return {"ok": True, "bought": got, "slaves": sim.slaves, "capital": round(sim.capital, 1)}


def _buy_manumit(sim, cmd, quantity):
    got = sim.manumit(int(quantity))
    if got <= 0:
        return {"ok": False, "error": "you have no slaves to free"}
    return {"ok": True, "manumitted": got, "freedmen": sim.freedmen, "slaves": sim.slaves}


# Dispatch over what is being bought: one small handler per kind, keyed by
# every spelling this command must match. Same pattern as
# _parse_command_body's own table - see that one's docstring for why a
# dict beats a long if/elif chain here too.
_BUY_HANDLERS = {
    "forest": _buy_forest,
    "nitre": _buy_nitre,
    "nitre_bed": _buy_nitre,
    "saltpetre": _buy_nitre,
    "nitre beds": _buy_nitre,
    "farm": _buy_farm,
    "food": _buy_farm,
    "housing": _buy_housing,
    "houses": _buy_housing,
    "school": _buy_school,
    "trade_school": _buy_school,
    "trade school": _buy_school,
    "material": _buy_material,
    "stock": _buy_material,
    "mine": _buy_mine,
    "slaves": _buy_slaves,
    "manumit": _buy_manumit,
}


def _cmd_buy(sim, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s); nothing more can be bought. 'state' shows where you finished and how far you got" % ended}
    what = cmd.get("what")
    # THE SAME READER AS EVERY OTHER QUANTITY: a bare float() here instead
    # of _qty would miss its guards, letting a huge or malformed number
    # through to print a refusal in binary rounding error.
    quantity, _err_n = _qty(cmd, "n", 0)
    if _err_n:
        return {"ok": False, "error": _err_n + ". Nothing was changed."}
    # A negative n would let buy_forest compute a NEGATIVE cost, pass the
    # affordability test because a negative cost is always less than what
    # is on hand, then credit the capital and mutate state anyway, all
    # while the reply says ok:false. Validate before touching anything.
    if not (quantity > 0):
        return {"ok": False,
                "error": "n must be greater than zero, got %g. Nothing was changed." % quantity}
    handler = _BUY_HANDLERS.get(what)
    if handler is None:
        return {"ok": False, "error": "what must be one of: forest, farm, housing, school, material, mine, slaves, manumit"}
    return handler(sim, cmd, quantity)



def _cmd_sell(sim, nodes, cmd, ended):
    material = str(cmd.get("material") or cmd.get("what") or "").lower()
    quantity, err = _qty(cmd, "n", 0)
    if err or quantity <= 0:
        return {"ok": False, "error": err or "n must be greater than zero"}
    sold = sim.sell_material_stock(material, quantity)
    if sold <= 0:
        return {"ok": False, "error": "you have none of that material stock to sell"}
    return {"ok": True, "material": material, "sold_tonnes": sold,
            "stock_on_hand_tonnes": sim.material_stock_t(material),
            "capital": round(sim.capital, 1)}



def _cmd_money(sim, nodes, cmd, ended):
    # LESS THE YEAR YOU HAVE ALREADY PAID FOR: `hire` takes a finder's fee
    # and the first year's wages up front, and step() nets that advance off
    # the living cost it charges, so this screen has to do the same or it
    # double-bills the same year - a discrepancy that only shows up in the
    # first year, which is what makes it easy to miss.
    _prepaid = min(sim.living_cost(), sim.wages_prepaid)
    fixed = (sim.upkeep() + sim.living_cost() - _prepaid
             + sim.mine_operating_cost())
    _standing_revenue = sim.revenue_capacity()
    _standing_upkeep = sim.upkeep()
    _standing_living = sim.living_cost(
        _rev=_standing_revenue, _upkeep=_standing_upkeep)
    _standing_prepaid = min(
        _standing_living, sim.wages_prepaid)
    _standing_fixed = (_standing_upkeep + _standing_living
                       - _standing_prepaid + sim.mine_operating_cost())
    _ramp, _prac = sim.still_ramping(), sim.practice_note()
    _mkt = sim.goods_market_summary()
    # A PLAYER MUST SEE IT (data/review/COMMODITY_DYNAMISM.md):
    # material_price_factor() responds for every material a node
    # buys, not just the 9 curated commodities, so what it
    # is doing to costs needs a line here too, not only inside one
    # project's own `why`. See economy.py's material_market_summary().
    _mat_mkt = sim.material_market_summary()
    return {"ok": True,
            "capital": round(sim.capital, 1),
            "revenue": round(sim.revenue(), 1),
            "where_the_money_comes_from": sim.revenue_sources(),
            **({"still_building_up_custom": _ramp} if _ramp else {}),
            **({"about_your_own_practice": _prac} if _prac else {}),
            **({"materials_costing_you_a_premium": _mat_mkt} if _mat_mkt else {}),
            **({"the_market_you_sell_into": _mkt} if _mkt else {}),
            "what_it_costs_you": {
                "upkeep_of_what_you_built": round(sim.upkeep(), 1),
                "living_and_appearances": round(sim.living_cost() - sim.wage_bill(), 1),
                # NAME THE PART THAT IS THERE BECAUSE YOU ARE RICH. A break
                # tester started with a million, built nothing, hired
                # nobody, and read "living and appearances ~14,990, Net/yr
                # -14,990" with no explanation anywhere of why an idle
                # fortune bleeds. It is not a fee: it is that a man visibly
                # richer than he lives is suspected in a patronage society.
                "_of_which_because_you_are_rich":
                    round(max(0.0, sim.capital) * 0.015, 1) or None,
                "wages": round(sim.wage_bill(), 1),
                "of_which_already_paid_as_hiring_advances":
                    round(_prepaid, 1) or None,
                "mines_standing": round(sim.mine_operating_cost(), 1),
                # A COST LIKE ANY OTHER: this must be included in the net
                # figures below, not left as a line the net ignores, or a
                # debt spiral can show a positive net while capital is
                # actually falling.
                "interest_on_arrears": round(
                    max(0.0, -sim.capital) * sim.debt_interest_rate(), 1)},
            # revenue_capacity(), not revenue() - this is the STANDING
            # figure (see the comment two lines below, and state's own
            # net_per_year, protocol.py: same fix, same reason). A
            # player who sold founder-hours with `work` watched this
            # swing to -193/yr for exactly one year and back, which is
            # not what "recurring" means.
            "net_per_year": round(
                _standing_revenue - _standing_fixed
                - max(0.0, -sim.capital) * sim.debt_interest_rate(), 1),
            "spent_on_projects_last_year": round(getattr(sim, "spend_last_year", 0.0), 1),
            # THE SAME FIGURE `state` PRINTS: net_per_year is the standing
            # flows, before anything goes into the work in hand, and this
            # is the figure after - the two must stay clearly distinct, or
            # two individually correct numbers on different screens read
            # as a contradiction.
            "net_after_project_spend": round(
                sim.revenue() - fixed
                - max(0.0, -sim.capital) * sim.debt_interest_rate()
                - getattr(sim, "spend_last_year", 0.0), 1),
            "credit_limit": round(sim.credit_limit(), 1),
            "interest_rate_on_arrears": round(sim.debt_interest_rate(), 4),
            "interest_paid_in_total": round(getattr(sim, "interest_paid", 0.0), 1),
            # HOW CLOSE, not just how far it goes. See warn_near_the_limit.
            "of_that_limit_you_have_used": (
                "%d%%" % (100.0 * -sim.capital / max(1e-9, sim.credit_limit()))
                if sim.capital < 0 and sim.credit_limit() > 0 else "none"),
            # committed_spend(), NOT A SECOND SUM OF THE SAME FIELD: 'start'
            # needs the identical total for its own aggregate warning (see
            # committed_spend()'s docstring, economy.py). One call, read
            # from both places.
            "still_owed_on_work_in_hand": round(sim.committed_spend(), 1),
            # THE OTHER HALF OF THE SAME QUESTION 'start' WARNS ABOUT:
            # what you have promised (just above) against what you can
            # actually expect to have. See funding_capacity()'s own
            # docstring for why this is the same number the un-manual
            # director's own start heuristic uses to avoid over-committing
            # itself.
            "you_could_actually_fund_up_to": round(sim.funding_capacity(), 1)}



def _cmd_quote(sim, nodes, cmd, ended):
    what = (cmd.get("what") or "mine").strip().lower()
    # EVERYTHING YOU CAN BUY, NOT JUST MINES: any purchase command with no
    # price shown anywhere, no way to ask for one, and no market to sell
    # it back into risks spending far more than intended. `quote` has to
    # cover every counter, not just one.
    if what in ("forest", "coppice", "woodland"):
        n_f, err_f = _qty(cmd, "n", 100)
        if err_f:
            return {"ok": False, "error": err_f}
        per = sim.FOREST_COST_PER_HA * sim.price_index
        return {"ok": True, "what": "forest", "hectares": n_f,
                "to_buy_it": round(per * n_f, 1),
                "per_hectare": round(per, 2),
                "you_have": round(sim.capital, 1),
                "you_could_raise": round(sim.spending_power("buy"), 1),
                "you_can_afford_about": round(sim.spending_power("buy") / max(per, 1e-9), 1),
                "afford_means": "cash plus half the credit line",
                "it_yields_per_hectare_per_year":
                    "%.2f tonnes of charcoal, sustainably" % sim.CHARCOAL_PER_HA,
                "note": "Coppice is bought once and yields every year after. "
                        "There is no market to sell it back into."}
    if what in ("nitre", "nitre_bed", "saltpetre"):
        n_n, err_n = _qty(cmd, "n", 10000)
        if err_n:
            return {"ok": False, "error": err_n}
        per_n = sim.NITRE_COST_PER_M2 * sim.price_index
        return {"ok": True, "what": "nitre bed", "square_metres": n_n,
                "to_lay_it": round(per_n * n_n, 1),
                "per_square_metre": round(per_n, 2),
                "you_have": round(sim.capital, 1),
                "you_could_raise": round(sim.spending_power("buy"), 1),
                "you_can_afford_about": round(sim.spending_power("buy") / max(per_n, 1e-9), 0),
                "afford_means": "cash plus half the credit line",
                "it_yields_per_square_metre_per_year":
                    "%.4f tonnes of saltpetre" % sim.NITRE_YIELD_T_PER_M2,
                "note": "Saltpetre is made, not mined: dung, straw and ash "
                        "turned for a couple of years. Cheap by the metre "
                        "and thin by the metre, so beds are laid in "
                        "thousands of square metres, not hundreds."}
    if what in ("slaves", "people"):
        n_s, err_s = _qty(cmd, "n", 1)
        if err_s:
            return {"ok": False, "error": err_s}
        return {"ok": True, "what": "slaves", "people": n_s,
                "to_buy_them": round(sim.slave_quote(n_s), 1),
                "you_have": round(sim.capital, 1),
                "note": "The price rises with how many you take at once, and "
                        "they are worth nothing to you for the first few "
                        "years while they learn the work. Freeing them "
                        "afterwards makes them worth more, not less."}
    if what != "mine":
        return {"ok": False,
                "error": "you can quote a mine, a forest or people: "
                         "quote mine coal 500, quote forest 100, quote slaves 5"}
    quantity, err = _qty(cmd, "n", 1)
    if err:
        return {"ok": False, "error": err}
    quote = sim.mine_quote(cmd.get("material"), quantity)
    if quote is None:
        return {"ok": False, "error": "no such material: %r. %s"
                % (cmd.get("material"), sim.mine_catalog_hint())}
    return dict(ok=True, **quote)



def _cmd_close(sim, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    mine_closed, msg = sim.close_mine(cmd.get("material") or cmd.get("what"))
    if not mine_closed:
        return {"ok": False, "error": msg}
    return {"ok": True, "closed": msg,
            "mine_operating_cost": round(sim.mine_operating_cost(), 1)}



def _cmd_withdraw(sim, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    withdrew, msg = sim.withdraw_from_public_life()
    if not withdrew:
        return {"ok": False, "error": msg}
    return {"ok": True, "withdrew": msg,
            "eminence": round(sim.eminence, 2),
            "reputation": round(sim.reputation, 1),
            "protection": round(sim.protection, 3)}



def _cmd_bribe(sim, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    amount, err = _qty(cmd, "amount")
    if err:
        return {"ok": False, "error": err + ". Nothing was changed."}
    bribed, msg = sim.bribe(amount)
    if not bribed:
        return {"ok": False, "error": msg}
    return {"ok": True, "bribed": msg, "capital": round(sim.capital, 1)}
