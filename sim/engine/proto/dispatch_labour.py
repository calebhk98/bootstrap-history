"""Labour and hiring commands: work, allocate, labour, hire, fire, train,
commission - everything whose job is staffing the household or selling and
directing its own hours, as opposed to spending on capital goods or a
project's own progress.

dispatch.py stays the composition point - the command table, the
dispatcher, and every name protocol.py's shim re-exports - and imports
these handlers back from here (see dispatch.py's own docstring for why
these live in a separate file).
"""

from ..data import ANNUAL_WAGE, TRADES_ABSENT, TRADE_NOTES, WAGES, trade_family
from .state import _staff_fraction_note
from .util import _num, _qty


def _cmd_work(sim, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    # WHAT THE PRACTICE WAS EARNING BEFORE YOU TOOK THE JOB: selling your
    # hours takes them out of your own surgery, which is where most of
    # your income comes from at the start, so the true cost has to be
    # measured against revenue before and after, not just the wage paid.
    _rev_before = sim.revenue()
    pay, err = sim.work_for_wages(cmd.get("trade"), cmd.get("hours", 0))
    # A message WITH pay is a warning about a bad trade, not a refusal:
    # the work happened and the player should be told what it cost them.
    if err and pay <= 0:
        return {"ok": False, "error": err}
    _rev_after = sim.revenue()
    _cost = _rev_before - _rev_after
    out = {"ok": True, "trade": cmd.get("trade"), "hours": cmd.get("hours"),
           "earned": round(pay, 1), "capital": round(sim.capital, 1),
           "your_hours_left_this_year": round(
               max(0.0, sim.director_pool() - sim.wage_hours_this_year), 1)}
    if _cost > 0.5:
        # Same rule: round the parts, then take the difference from the
        # rounded parts, so the three figures on the screen subtract.
        out["earned"] = round(pay, 1)
        out["it_cost_your_own_practice"] = round(_cost, 1)
        out["so_you_are_up"] = round(round(pay, 1) - round(_cost, 1), 1)
        # "THE PRACTICE" THROUGHOUT, not "the surgery" halfway through.
        # A Roman founder selling a year of smith's work does not have a
        # surgery, and the sentence named the same thing two ways inside
        # fourteen words.
        out["why"] = ("You cannot be in two places. Hours sold for wages "
                      "come out of your own practice, so what you really "
                      "made this year is the wage less what the practice "
                      "did not earn while you were gone. Hours you put "
                      "into your OWN projects do not cost you this.")
    if err:
        out["but"] = err
    return out



def _cmd_allocate(sim, nodes, cmd, ended):
    # A STANDING INSTRUCTION, NOT A ONE-TURN COMMAND. "Divide your own
    # year's hours yourself": `start` and `work` already let a player
    # act for one year at a time, and a player who wants a fixed split
    # - 100 hours a year of manual work, 500 to one project, 1400 to
    # another - had no way to say so once and have it stand, in a game
    # played over hundreds of turns. This writes s.hour_allocations,
    # which core.py's step() - and nowhere else - reads; `portfolio`
    # below reads the same numbers step() actually applied, never a
    # second guess at them. See core.py's own long comment on exactly
    # how a directive changes the allocator (order, not ceiling) and
    # what happens when it cannot be honoured.
    target_id = cmd.get("id")
    if target_id is None:
        _rows = [{"id": target_id, "hours_a_year": hours}
                 for target_id, hours in sorted(sim.hour_allocations.items()) if target_id != "work"]
        _out = {"ok": True, "allocations": _rows or "none"}
        if sim.hour_allocations.get("work"):
            _out["work"] = {"trade": sim.work_trade,
                            "hours_a_year": sim.hour_allocations["work"]}
        _out["note"] = (
            "hours you have NOT directed keep being shared out by "
            "priority, exactly as before - this only affects what you "
            "have explicitly put here. {\"cmd\":\"allocate\",\"id\":X,"
            "\"hours\":N} sets or replaces one; hours 0 (or leaving "
            "hours out) clears it. id \"work\" sells hours for wages "
            "every year instead of a project - it also needs \"trade\".")
        return _out
    hours = cmd.get("hours")
    hours = 0.0 if hours is None else _num(hours, -1.0)
    if hours < 0:
        return {"ok": False, "error": "hours must be a number, 0 or "
                                      "more. 0 clears the standing order."}
    if target_id == "work":
        if hours <= 0:
            had = sim.hour_allocations.pop("work", None)
            sim.work_trade = None
            return {"ok": True, "cleared": "work",
                    "had_been": had} if had else {"ok": True, "cleared": "work"}
        trade = cmd.get("trade") or sim.work_trade
        if not trade:
            return {"ok": False,
                    "error": "say which trade to sell hours as, e.g. "
                             "{\"cmd\":\"allocate\",\"id\":\"work\","
                             "\"trade\":\"labourer\",\"hours\":100}"}
        if trade not in WAGES:
            here = sorted(trade for trade in WAGES if sim.trade_available(trade))
            return {"ok": False, "error": "no such trade. you could work "
                                          "as: " + ", ".join(here)}
        if not sim.trade_available(trade):
            return {"ok": False,
                    "error": "nobody here will pay you to be a %s yet: "
                             "the trade does not exist in this society. "
                             "Teach it first with train." % trade}
        sim.hour_allocations["work"] = float(hours)
        sim.work_trade = trade
        return {"ok": True, "set": "work", "trade": trade,
                "hours_a_year": float(hours),
                "note": "this much of your own pool is sold for wages as "
                        "a %s every year from now on, topping up anything "
                        "you sell by hand the same year, before your "
                        "projects see what is left. 'allocate' with "
                        "hours 0 clears it" % trade}
    if target_id not in nodes:
        return {"ok": False, "error": "unknown node id %r. 'state' lists "
                                      "what is active" % target_id}
    if target_id not in sim.active:
        return {"ok": False,
                "error": "%s is not active, so there is nothing for a "
                         "directive to apply to yet. 'start' it first, "
                         "then 'allocate' it hours" % target_id}
    if hours <= 0:
        had = sim.hour_allocations.pop(target_id, None)
        return ({"ok": True, "cleared": target_id, "had_been_a_year": had}
                if had else {"ok": True, "cleared": target_id})
    sim.hour_allocations[target_id] = float(hours)
    return {"ok": True, "set": target_id, "name": nodes[target_id]["name"],
            "hours_a_year": float(hours),
            "note": "this many of your own hours go to %s every year "
                    "from now on, ahead of anything you have not "
                    "directed - it can still never exceed what the pool "
                    "has or what this project's own pace can use; "
                    "'portfolio' shows what it actually gets each year "
                    "and why. 'allocate' with hours 0 clears it"
                    % nodes[target_id]["name"]}



def _cmd_labour(sim, nodes, cmd, ended):
    one = (cmd.get("trade") or "").strip().lower()
    if one and one not in WAGES:
        return {"ok": False, "error": "no such trade: %s. They are: %s"
                % (one, ", ".join(sorted(WAGES)))}
    def row(trade, long=False):
        # THE PRICE YOU ACTUALLY PAY, not the table price: leaning on a
        # trade's local supply bids it up, and the premium has to appear
        # here, not only in the bill.
        _lpf = sim.labour_price_factor(trade)
        entry = {"trade": trade,
             "a_year_of_one": round(sim.annual_wage(trade), 0),
             "you_employ": round(sim.employees.get(trade, 0.0), 2)}
        if long:
            entry["wage_foundation"] = {
                "base_for_skill_and_difficulty": ANNUAL_WAGE.get(trade, 375.0),
                **{factor_key: round(value, 3) for factor_key, value in sim.wage_cost_factors(trade).items()},
                "demographic_scarcity": round(sim.wage_index, 3),
                "local_trade_scarcity": round(_lpf, 3),
                "society_price_level": round(sim.price_index, 3),
            }
        # SAME EXPLANATION AS THE FULL LIST'S, for whoever asks about
        # one trade without ever asking for all of them - see
        # _staff_fraction_note. Checked on this one trade alone, not
        # the whole household, so a whole-number trade gets no
        # footnote even while another trade is mid-attrition.
        if abs(entry["you_employ"] - round(entry["you_employ"])) >= 0.02:
            entry["you_employ_is_fractional_because"] = (
                "a continuous full-time-equivalent, not a count of "
                "whole people: hiring phases in, training takes years, "
                "and attrition trims a little every year rather than "
                "dismissing one named person at a time.")
        # THE CEILING, ON THE SCREEN: a hard cap on how many of a literate
        # trade this society can ever supply has to be visible here, not
        # something only discoverable by walking into a refusal deep into
        # a run. A wall you can only discover by walking into it is not a
        # wall, it is a trap.
        if trade in sim.LITERATE_TRADES:
            entry["most_this_society_can_ever_supply"] = round(
                sim.literate_capacity(trade), 1)
            entry["you_have_or_are_teaching"] = round(
                sim._trade_headcount_pending(trade), 2)
            entry["what_widens_it"] = ("printing, paper, schools and academies - "
                                   "they raise how many people here can "
                                   "read, and this ceiling rises with it")
        if _lpf > 1.005:
            entry["dearer_than_usual_by"] = "%d%%" % ((_lpf - 1.0) * 100)
            # "HERE" IS ONE TOWN, NOT THE COUNTRY. Reading this as a claim
            # about the whole of Rome or Han China makes the game read as
            # absurd, so this line has to be clear it is not that. See the
            # population command for the country-wide figure this
            # household's own reach is being measured against.
            entry["because"] = ("you have taken on a large share of the %ss "
                            "within this household's reach - one town's "
                            "labour market, not the whole country; the "
                            "population command shows how the two "
                            "compare. Teaching more of the trade, or "
                            "anything that widens the supply, brings it "
                            "back down" % trade)
        if long:
            entry.update({"kind": trade_family(trade),
                      "wage_per_hour": round(WAGES[trade] * sim.wage_index
                                             * sim.price_index, 3),
                      # SPLIT, because the total includes your own people
                      # and calling all of it "the market" made hiring look
                      # like it created smiths out of nothing.
                      "hours_the_market_can_supply": round(sim.market_supply_split(trade)[0], 0),
                      "hours_your_own_people_add": round(sim.market_supply_split(trade)[1], 0),
                      # AND THE SECOND CHANNEL: there are two distinct
                      # capacities, who you can HIRE here and what an
                      # outside shop will take on at a premium, and both
                      # must be shown or a reader treats one ceiling as
                      # the only one and commissions past it.
                      "hours_you_have_commissioned": round(sim.hours_reserved(trade), 0),
                      "hours_you_could_still_commission": round(
                          max(0.0, sim.market_supply(trade) - sim.hours_reserved(trade)), 0),
                      "hours_available_to_you_in_all": round(
                          sim.hours_you_can_call_on(trade), 0),
                      # THE NOTE IS STATIC AND THE WORLD IS NOT: TRADE_NOTES
                      # is a fixed string about the society as it started,
                      # so if the trade has since been taught into
                      # existence, the reply must say that instead - or it
                      # contradicts itself, claiming the trade both exists
                      # and does not in the same reply. Teaching one is the
                      # whole point of `train`; the reply has to notice it
                      # happened.
                      "note": (("you taught this trade into existence here; "
                                "the only %ss in this society are yours and "
                                "the ones they have taught since" % trade)
                               if trade in sim.trades_created
                               else TRADE_NOTES.get(trade, ""))})
            # THE HIRE YOU ARE CONTEMPLATING, NOT THE MARKET AS IT STANDS.
            # a_year_of_one above is true the instant it is quoted and can
            # be false one command later: hiring is what moves
            # labour_price_factor, and wage_bill charges the NEW factor
            # to every head of the trade you then have, not only the one
            # you added, so the standing wage bill after hiring can be far
            # higher than "a year of one" quoted before the hire. See
            # labour_price_factor_after_hiring's own docstring for the
            # full account; this is that forecast, priced and put on the
            # one screen a player actually reads before committing.
            if sim.trade_available(trade):
                _lpf_after = sim.labour_price_factor_after_hiring(trade, 1.0)
                _rate_after = round(
                    sim.annual_wage(trade, include_local_scarcity=False) * _lpf_after, 0)
                # ALWAYS SHOWN, QUIETLY: this is the number the task is
                # actually about, and it belongs on the screen whether or
                # not the move is large enough to also earn the banner
                # below.
                entry["a_year_of_one_after_you_hire_one"] = _rate_after
                # THE BANNER IS FOR SCARCITY, NOT ARITHMETIC. One more
                # hire measurably moves the price of almost any trade in
                # a town this size - labourer's base pool is roughly a
                # dozen person-years, so even it crosses a 0.5% move from
                # a single hire. Flagging that every time would be a
                # warning nobody reads by the tenth trade. 5% (the same
                # bound `labour_pressure` itself treats as worth a name,
                # see labour_price_factor's own note on what "roughly
                # doubles the price at the whole of it" means) is where a
                # single hire stops being noise and starts being the
                # reason your wage bill actually moved - true of a rare,
                # thin-market trade and false of a common one like
                # labourer or smith.
                if _lpf_after > 1.05:
                    _have = sim.employees.get(trade, 0.0)
                    entry["hiring_moves_the_price"] = True
                    # NOT JUST THE NEW HIRE. The whole point is that this
                    # rate applies to everyone you already have too, the
                    # instant you take one more on - so the bill, not
                    # only the per-head rate, is what has to be shown.
                    entry["wage_bill_for_this_trade_now"] = round(
                        _have * entry["a_year_of_one"], 0)
                    entry["wage_bill_for_this_trade_after_hiring_one_more"] = round(
                        (_have + 1.0) * _rate_after, 0)
        return entry
    if one:
        entry = row(one, long=True)
        entry["exists_here"] = sim.trade_available(one)
        return {"ok": True, "trade": entry}
    have = sorted(trade for trade in WAGES if sim.employees.get(trade, 0.0) > 0.005)
    # NOT "TRADES YOU DO NOT YET EMPLOY", and not "trades that exist"
    # either: excluding the ones you have would read as "no more smiths
    # available" the moment you hire your first smith, which `hire smith 1`
    # then contradicts; including every available trade would put
    # machinist on the list while `labour machinist` says "the town can
    # supply: 0 hours" - a direct contradiction between the two screens.
    # It is every trade there is actually somebody here to hire.
    hirable = sorted(trade for trade in WAGES
                     if sim.trade_available(trade) and sim.market_supply_split(trade)[0] > 0)
    taught_only = sorted(trade for trade in WAGES
                         if sim.trade_available(trade) and trade not in hirable)
    absent = sorted(trade for trade in WAGES if not sim.trade_available(trade))
    return {"ok": True,
            "on_your_staff": [row(trade) for trade in have] or "nobody",
            "you_could_hire_here": hirable,
            "only_the_ones_you_taught": taught_only,
            "do_not_exist_here": absent,
            "you_employ_in_total": round(sum(sim.employees.values()), 2),
            # THE CAP, WHERE A PLAYER CAN SEE IT: this number can decide an
            # entire mid-game and must not be discoverable only by trying
            # to hire and being refused, with no earlier screen - state
            # included - showing it at all.
            "household_places_used": round(sim.headcount(), 2),
            "household_places_in_all":
                round(sim.headcount() + max(0.0, sim.household_room()), 2),
            "room_for_more_people": round(max(0.0, sim.household_room()), 2),
            # _room_advice, NOT _staff_advice: this is `labour`, and
            # `state` sends a player here with the words "'labour' says
            # what raises it" - meaning the CEILING on people. Answering
            # with _staff_advice instead, which names hiring, commissioning
            # and buying, every one of which needs the room you have not
            # got, sends a player in a circle. _room_advice exists for
            # exactly this.
            "what_raises_that_room": sim._room_advice(),
            # NOT "NEVER", AND NOT "HOWEVER RICH": the ceiling is not
            # fixed. It grows with the institutions that train scholars and
            # carry their keep, and this sentence has to say so
            # consistently with the `hire` refusal, which already does.
            "and_how_many_of_the_lettered_trades_this_society_supplies": (
                "%s: right now your household can hold at most %.1f of them "
                "in total, hired and taught together. That is your reach "
                "into the labour market, not a fact about how many people "
                "here can read. It RISES: a school, an academy and an "
                "imperial patron train and pay scholars on their own "
                "budget and lift this ceiling with them, which is the large "
                "effect; printing, paper and libraries widen literacy "
                "itself, which is the smaller one."
                % (", ".join(sorted(sim.LITERATE_TRADES)),
                   sim.literate_capacity("scholar"))),
            "slaves": sim.slaves, "freedmen": sim.freedmen,
            "annual_wage_bill": round(sim.wage_bill(), 1),
            "craftsmen_on_your_staff": round(sim.artisans, 2),
            "scholars_including_you": round(sim.effective_scholars(), 2),
            # SAME EXPLANATION AS `state`'s - see _staff_fraction_note.
            # A player who asks `labour` without ever asking `state`
            # deserves the same answer to "why is this not a whole
            # number", not silence on this screen and a footnote only
            # on the other one.
            "staff_are_fractional_because": _staff_fraction_note(sim),
            # A ROW WITH NO TRADE IS PEOPLE YOU BOUGHT: printing that as
            # the literal string "None" - "None x3.3", "None x0.55" -
            # would read as the game having lost track of its own
            # household. It knows exactly what they are, so this
            # substitutes a description instead.
            "in_training": [
                {"trade": (training_record[2] if len(training_record) > 2
                           else "people you bought, learning the work"),
                 "people": (training_record[3] if len(training_record) > 3
                            else round(training_record[0] / 0.55, 2)),
                 "ready_year": training_record[1]}
                for training_record in sim.training],
            "one_trade_in_full": '{"cmd":"labour","trade":"smith"}',
            "how_to_grow_staff": {"scholars": sim._staff_advice("scholars"),
                                  "artisans": sim._staff_advice("artisans")},
            "note": "A trade that does not exist here cannot be hired at any "
                    "price; teach one with train. Trades are not "
                    "interchangeable. Buying a job instead of a person is "
                    "commission. Every figure above is this household's "
                    "own reach into ONE town's labour market, not the "
                    "whole country - the population command shows both, "
                    "side by side, for every trade."}



def _cmd_hire(sim, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    if not sim.founder_alive and sim.directors_extra < 0.5:
        return {"ok": False,
                "error": "there is nobody left to take anyone on: the "
                         "founder is dead and no deputy remains to direct "
                         "the work"}
    quantity, err = _qty(cmd, "n", 1)
    if err:
        return {"ok": False, "error": err + ". Nothing was changed."}
    hired, err = sim.hire(cmd.get("trade"), quantity)
    if not hired:
        return {"ok": False, "error": err}
    # HIRING AND LETTING GO ARE DECISIONS, not standing facts the way
    # payroll is - neither labour.py nor core.py logs either one, so a
    # player reading `log` back saw the wage bill change with nothing
    # saying they were the one who changed it. `hire` already composed a
    # precise sentence for this ("2 smiths taken on for 750 denarii...");
    # using it here rather than rebuilding one from cmd["n"] keeps the log
    # honest about what actually happened, not just what was asked for.
    sim.log.append((sim.year, err or ("hired %s %s" % (cmd.get("n"), cmd.get("trade")))))
    return {"ok": True, "hired": cmd.get("trade"), "n": cmd.get("n"),
            "you_now_employ": round(sim.employees.get(str(cmd.get("trade")).lower(), 0.0), 2),
            "annual_wage_bill": round(sim.wage_bill(), 1),
            "capital": round(sim.capital, 1)}



def _cmd_fire(sim, nodes, cmd, ended):
    quantity, err = _qty(cmd, "n", 1)
    if err:
        return {"ok": False, "error": err + ". Nothing was changed."}
    fired, err = sim.fire(cmd.get("trade"), quantity)
    if not fired:
        return {"ok": False, "error": err}
    # Same reasoning as `hire` above: `err` here is fire()'s own success
    # message, which says exactly what happened - staff let go, an
    # apprenticeship cancelled, or both - and cmd["n"] alone would not.
    sim.log.append((sim.year, err or ("let go %s %s" % (cmd.get("n"), cmd.get("trade")))))
    out = {"ok": True, "let_go": cmd.get("trade"),
           "annual_wage_bill": round(sim.wage_bill(), 1)}
    if err:
        out["what_happened"] = err
    return out



def _cmd_train(sim, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    quantity, err = _qty(cmd, "n", 1)
    if err:
        return {"ok": False, "error": err + ". Nothing was changed."}
    trained, msg = sim.train(cmd.get("trade"), quantity, cmd.get("from"))
    if not trained:
        return {"ok": False, "error": msg}
    out = {"ok": True, "training": msg, "capital": round(sim.capital, 1),
           "your_hours_left_this_year": round(
               max(0.0, sim.director_pool() - sim.director_hours_committed()), 1)}
    # TRAIN AND HIRE ARE TWO SEPARATE STEPS, and this message is the one
    # place a player sees that at the moment they take the first of them:
    # a newly-created trade has no open market to fall back on the way a
    # smith or a scribe does, so a project's hired_labour for it draws
    # only on people trained or hired INTO it directly. Nobody can do that
    # work until the people above finish learning, and 'hire' is how you
    # add more without that wait, now that the trade exists to hire into
    # at all. That gap has to be named here, or the first anyone learns of
    # it is `start` refusing a project outright.
    _trade = str(cmd.get("trade") or "").strip().lower()
    if _trade in TRADES_ABSENT:
        out["means"] = (
            "%s now exists here, but nobody can do that work yet: a "
            "project needing it draws only on people trained or hired "
            "into this exact trade, never a general market. "
            "'hire %s <n>' adds more right away, without waiting; "
            "otherwise the people above are it until they finish."
            % (_trade, _trade))
    return out



def _cmd_commission(sim, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    hours, err = _qty(cmd, "hours")
    if err:
        return {"ok": False, "error": err + ". Nothing was changed."}
    commissioned, msg = sim.commission(cmd.get("trade"), hours)
    if not commissioned:
        return {"ok": False, "error": msg}
    return {"ok": True, "commissioned": msg, "capital": round(sim.capital, 1),
            "note": "These hours are available to your projects this year only."}
