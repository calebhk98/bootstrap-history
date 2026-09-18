"""Labour and hiring commands: work, allocate, labour, hire, fire, train,
commission - everything whose job is staffing the household or selling and
directing its own hours, as opposed to spending on capital goods or a
project's own progress.

Split out of dispatch.py (see that file's own docstring for why): dispatch.py
stays the composition point - the command table, the dispatcher, and every
name protocol.py's shim re-exports - and imports these handlers back from
here. Behaviour is unchanged and moved verbatim.
"""

from ..data import ANNUAL_WAGE, TRADES_ABSENT, TRADE_NOTES, WAGES, trade_family
from .state import _staff_fraction_note
from .util import _num, _qty


def _cmd_work(s, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    # WHAT THE PRACTICE WAS EARNING BEFORE YOU TOOK THE JOB. Selling your
    # hours takes them out of your own surgery, which is where most of your
    # income comes from at the start - so a play tester earned 80.1 for 500
    # hours as a scribe and lost 58.3 of practice income the same instant,
    # netting 22 for a quarter of their year. Nothing anywhere said founder
    # hours drove revenue, and they only found it by diffing the ledger.
    _rev_before = s.revenue()
    pay, err = s.work_for_wages(cmd.get("trade"), cmd.get("hours", 0))
    # A message WITH pay is a warning about a bad trade, not a refusal:
    # the work happened and the player should be told what it cost them.
    if err and pay <= 0:
        return {"ok": False, "error": err}
    _rev_after = s.revenue()
    _cost = _rev_before - _rev_after
    out = {"ok": True, "trade": cmd.get("trade"), "hours": cmd.get("hours"),
           "earned": round(pay, 1), "capital": round(s.capital, 1),
           "your_hours_left_this_year": round(
               max(0.0, s.director_pool() - s.wage_hours_this_year), 1)}
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



def _cmd_allocate(s, nodes, cmd, ended):
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
                 for target_id, hours in sorted(s.hour_allocations.items()) if target_id != "work"]
        _out = {"ok": True, "allocations": _rows or "none"}
        if s.hour_allocations.get("work"):
            _out["work"] = {"trade": s.work_trade,
                            "hours_a_year": s.hour_allocations["work"]}
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
            had = s.hour_allocations.pop("work", None)
            s.work_trade = None
            return {"ok": True, "cleared": "work",
                    "had_been": had} if had else {"ok": True, "cleared": "work"}
        trade = cmd.get("trade") or s.work_trade
        if not trade:
            return {"ok": False,
                    "error": "say which trade to sell hours as, e.g. "
                             "{\"cmd\":\"allocate\",\"id\":\"work\","
                             "\"trade\":\"labourer\",\"hours\":100}"}
        if trade not in WAGES:
            here = sorted(trade for trade in WAGES if s.trade_available(trade))
            return {"ok": False, "error": "no such trade. you could work "
                                          "as: " + ", ".join(here)}
        if not s.trade_available(trade):
            return {"ok": False,
                    "error": "nobody here will pay you to be a %s yet: "
                             "the trade does not exist in this society. "
                             "Teach it first with train." % trade}
        s.hour_allocations["work"] = float(hours)
        s.work_trade = trade
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
    if target_id not in s.active:
        return {"ok": False,
                "error": "%s is not active, so there is nothing for a "
                         "directive to apply to yet. 'start' it first, "
                         "then 'allocate' it hours" % target_id}
    if hours <= 0:
        had = s.hour_allocations.pop(target_id, None)
        return ({"ok": True, "cleared": target_id, "had_been_a_year": had}
                if had else {"ok": True, "cleared": target_id})
    s.hour_allocations[target_id] = float(hours)
    return {"ok": True, "set": target_id, "name": nodes[target_id]["name"],
            "hours_a_year": float(hours),
            "note": "this many of your own hours go to %s every year "
                    "from now on, ahead of anything you have not "
                    "directed - it can still never exceed what the pool "
                    "has or what this project's own pace can use; "
                    "'portfolio' shows what it actually gets each year "
                    "and why. 'allocate' with hours 0 clears it"
                    % nodes[target_id]["name"]}



def _cmd_labour(s, nodes, cmd, ended):
    one = (cmd.get("trade") or "").strip().lower()
    if one and one not in WAGES:
        return {"ok": False, "error": "no such trade: %s. They are: %s"
                % (one, ", ".join(sorted(WAGES)))}
    def row(t, long=False):
        # THE PRICE YOU ACTUALLY PAY, not the table price. A play tester
        # watched engineers go from 781 a year to 1,094 and budgeted wrong
        # for decades: leaning on a trade's local supply bids it up, and
        # the premium appeared in the bill and nowhere else.
        _lpf = s.labour_price_factor(t)
        entry = {"trade": t,
             "a_year_of_one": round(s.annual_wage(t), 0),
             "you_employ": round(s.employees.get(t, 0.0), 2)}
        if long:
            entry["wage_foundation"] = {
                "base_for_skill_and_difficulty": ANNUAL_WAGE.get(t, 375.0),
                **{factor_key: round(value, 3) for factor_key, value in s.wage_cost_factors(t).items()},
                "demographic_scarcity": round(s.wage_index, 3),
                "local_trade_scarcity": round(_lpf, 3),
                "society_price_level": round(s.price_index, 3),
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
        # THE CEILING, ON THE SCREEN. "This society's literacy will not
        # supply more than 6.4 scholars in total, ever" gates the goal
        # itself - which wants twenty-five - and appeared in no screen at
        # all: a play tester found it in a refusal message in year 463 of a
        # 500-year game. A wall you can only discover by walking into it is
        # not a wall, it is a trap.
        if t in s.LITERATE_TRADES:
            entry["most_this_society_can_ever_supply"] = round(
                s.literate_capacity(t), 1)
            entry["you_have_or_are_teaching"] = round(
                s._trade_headcount_pending(t), 2)
            entry["what_widens_it"] = ("printing, paper, schools and academies - "
                                   "they raise how many people here can "
                                   "read, and this ceiling rises with it")
        if _lpf > 1.005:
            entry["dearer_than_usual_by"] = "%d%%" % ((_lpf - 1.0) * 100)
            # "HERE" IS ONE TOWN, NOT THE COUNTRY. A player who reads
            # this as a claim about the whole of Rome or Han China
            # concludes the game is absurd - that is the demographics
            # complaint this line exists to head off. See the
            # population command for the country-wide figure this
            # household's own reach is being measured against.
            entry["because"] = ("you have taken on a large share of the %ss "
                            "within this household's reach - one town's "
                            "labour market, not the whole country; the "
                            "population command shows how the two "
                            "compare. Teaching more of the trade, or "
                            "anything that widens the supply, brings it "
                            "back down" % t)
        if long:
            entry.update({"kind": trade_family(t),
                      "wage_per_hour": round(WAGES[t] * s.wage_index
                                             * s.price_index, 3),
                      # SPLIT, because the total includes your own people
                      # and calling all of it "the market" made hiring look
                      # like it created smiths out of nothing.
                      "hours_the_market_can_supply": round(s.market_supply_split(t)[0], 0),
                      "hours_your_own_people_add": round(s.market_supply_split(t)[1], 0),
                      # AND THE SECOND CHANNEL. A break tester read one
                      # ceiling in three places and then commissioned past
                      # it. There are two: who you can HIRE here, and what
                      # an outside shop will take on, at a premium.
                      "hours_you_have_commissioned": round(s.hours_reserved(t), 0),
                      "hours_you_could_still_commission": round(
                          max(0.0, s.market_supply(t) - s.hours_reserved(t)), 0),
                      "hours_available_to_you_in_all": round(
                          s.hours_you_can_call_on(t), 0),
                      # THE NOTE IS STATIC AND THE WORLD IS NOT. A break
                      # tester read "exists here: True" and "does not exist
                      # yet; you must create this trade" three lines apart,
                      # because the note is a fixed string about the
                      # society as it started and they had since taught the
                      # trade into existence. Teaching one is the whole
                      # point of `train`; the reply has to notice it
                      # happened.
                      "note": (("you taught this trade into existence here; "
                                "the only %ss in this society are yours and "
                                "the ones they have taught since" % t)
                               if t in s.trades_created
                               else TRADE_NOTES.get(t, ""))})
            # THE HIRE YOU ARE CONTEMPLATING, NOT THE MARKET AS IT STANDS.
            # a_year_of_one above is true the instant it is quoted and can
            # be false one command later: hiring is what moves
            # labour_price_factor, and wage_bill charges the NEW factor
            # to every head of the trade you then have, not only the one
            # you added. A Norse player was quoted "a year of one: 525"
            # for a scholar, hired one, and the standing wage bill came to
            # 847.92 - 61% more - from exactly this. See
            # labour_price_factor_after_hiring's own docstring for the
            # full account; this is that forecast, priced and put on the
            # one screen a player actually reads before committing.
            if s.trade_available(t):
                _lpf_after = s.labour_price_factor_after_hiring(t, 1.0)
                _rate_after = round(
                    s.annual_wage(t, include_local_scarcity=False) * _lpf_after, 0)
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
                # reason your wage bill actually moved - which is what
                # the Norse scholar case (1.0 to 1.615) plainly was and a
                # common trade like labourer or smith (~1.01) plainly
                # is not.
                if _lpf_after > 1.05:
                    _have = s.employees.get(t, 0.0)
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
        entry["exists_here"] = s.trade_available(one)
        return {"ok": True, "trade": entry}
    have = sorted(trade for trade in WAGES if s.employees.get(trade, 0.0) > 0.005)
    # NOT "TRADES YOU DO NOT YET EMPLOY", and not "trades that exist"
    # either. Excluding the ones you have reads as "no more smiths
    # available" the moment you hire your first smith, which `hire smith 1`
    # then contradicts; including every available trade put machinist on
    # the list while `labour machinist` said "the town can supply: 0
    # hours", which a play tester read side by side. It is every trade
    # there is actually somebody here to hire.
    hirable = sorted(trade for trade in WAGES
                     if s.trade_available(trade) and s.market_supply_split(trade)[0] > 0)
    taught_only = sorted(trade for trade in WAGES
                         if s.trade_available(trade) and trade not in hirable)
    absent = sorted(trade for trade in WAGES if not s.trade_available(trade))
    return {"ok": True,
            "on_your_staff": [row(trade) for trade in have] or "nobody",
            "you_could_hire_here": hirable,
            "only_the_ones_you_taught": taught_only,
            "do_not_exist_here": absent,
            "you_employ_in_total": round(sum(s.employees.values()), 2),
            # THE CAP, WHERE A PLAYER CAN SEE IT. This number decided a
            # play tester's entire mid-game and appeared NOWHERE: not in
            # state, not in state full, not here. The only way to learn it
            # was to try to hire and be refused, and the only way to learn
            # what RAISED it was to read the refusal, which changed as the
            # tree opened. They sat on 285,000 denarii unable to take on a
            # sixth person and had no idea why.
            "household_places_used": round(s.headcount(), 2),
            "household_places_in_all":
                round(s.headcount() + max(0.0, s.household_room()), 2),
            "room_for_more_people": round(max(0.0, s.household_room()), 2),
            # _room_advice, NOT _staff_advice. This is `labour`, and
            # `state` sends a player here with the words "'labour' says
            # what raises it" - meaning the CEILING on people. It answered
            # with _staff_advice, which names hiring, commissioning and
            # buying, every one of which needs the room you have not got.
            # Two play testers followed it in a circle; one found the real
            # answer only by guessing the word "workshop" in a search.
            # _room_advice exists for exactly this and was written after
            # the same complaint about the hire refusal.
            "what_raises_that_room": s._room_advice(),
            # NOT "NEVER", AND NOT "HOWEVER RICH". This sentence is mine
            # and it went stale the same day I wrote it. It said the
            # ceiling could never move, which was true of the old model and
            # is now false: the ceiling grows with the institutions that
            # train scholars and carry their keep. The user caught it by
            # reading the sentence literally, which is the right way to
            # read a sentence, and noticing it implies no research you do
            # can ever help. The `hire` refusal had already been corrected
            # and this screen had not, so the game was saying both things.
            "and_how_many_of_the_lettered_trades_this_society_supplies": (
                "%s: right now your household can hold at most %.1f of them "
                "in total, hired and taught together. That is your reach "
                "into the labour market, not a fact about how many people "
                "here can read. It RISES: a school, an academy and an "
                "imperial patron train and pay scholars on their own "
                "budget and lift this ceiling with them, which is the large "
                "effect; printing, paper and libraries widen literacy "
                "itself, which is the smaller one."
                % (", ".join(sorted(s.LITERATE_TRADES)),
                   s.literate_capacity("scholar"))),
            "slaves": s.slaves, "freedmen": s.freedmen,
            "annual_wage_bill": round(s.wage_bill(), 1),
            "craftsmen_on_your_staff": round(s.artisans, 2),
            "scholars_including_you": round(s.effective_scholars(), 2),
            # SAME EXPLANATION AS `state`'s - see _staff_fraction_note.
            # A player who asks `labour` without ever asking `state`
            # deserves the same answer to "why is this not a whole
            # number", not silence on this screen and a footnote only
            # on the other one.
            "staff_are_fractional_because": _staff_fraction_note(s),
            # A ROW WITH NO TRADE IS PEOPLE YOU BOUGHT, and printing that
            # as the literal string "None" - "None x3.3", "None x0.55" -
            # is how two separate testers concluded the game had lost track
            # of their household. It knows exactly what they are.
            "in_training": [
                {"trade": (training_record[2] if len(training_record) > 2
                           else "people you bought, learning the work"),
                 "people": (training_record[3] if len(training_record) > 3
                            else round(training_record[0] / 0.55, 2)),
                 "ready_year": training_record[1]}
                for training_record in getattr(s, "training", [])],
            "one_trade_in_full": '{"cmd":"labour","trade":"smith"}',
            "how_to_grow_staff": {"scholars": s._staff_advice("scholars"),
                                  "artisans": s._staff_advice("artisans")},
            "note": "A trade that does not exist here cannot be hired at any "
                    "price; teach one with train. Trades are not "
                    "interchangeable. Buying a job instead of a person is "
                    "commission. Every figure above is this household's "
                    "own reach into ONE town's labour market, not the "
                    "whole country - the population command shows both, "
                    "side by side, for every trade."}



def _cmd_hire(s, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    if not s.founder_alive and s.directors_extra < 0.5:
        return {"ok": False,
                "error": "there is nobody left to take anyone on: the "
                         "founder is dead and no deputy remains to direct "
                         "the work"}
    quantity, err = _qty(cmd, "n", 1)
    if err:
        return {"ok": False, "error": err + ". Nothing was changed."}
    ok, err = s.hire(cmd.get("trade"), quantity)
    if not ok:
        return {"ok": False, "error": err}
    # HIRING AND LETTING GO ARE DECISIONS, not standing facts the way
    # payroll is - neither labour.py nor core.py logs either one, so a
    # player reading `log` back saw the wage bill change with nothing
    # saying they were the one who changed it. `hire` already composed a
    # precise sentence for this ("2 smiths taken on for 750 denarii...");
    # using it here rather than rebuilding one from cmd["n"] keeps the log
    # honest about what actually happened, not just what was asked for.
    s.log.append((s.year, err or ("hired %s %s" % (cmd.get("n"), cmd.get("trade")))))
    return {"ok": True, "hired": cmd.get("trade"), "n": cmd.get("n"),
            "you_now_employ": round(s.employees.get(str(cmd.get("trade")).lower(), 0.0), 2),
            "annual_wage_bill": round(s.wage_bill(), 1),
            "capital": round(s.capital, 1)}



def _cmd_fire(s, nodes, cmd, ended):
    quantity, err = _qty(cmd, "n", 1)
    if err:
        return {"ok": False, "error": err + ". Nothing was changed."}
    ok, err = s.fire(cmd.get("trade"), quantity)
    if not ok:
        return {"ok": False, "error": err}
    # Same reasoning as `hire` above: `err` here is fire()'s own success
    # message, which says exactly what happened - staff let go, an
    # apprenticeship cancelled, or both - and cmd["n"] alone would not.
    s.log.append((s.year, err or ("let go %s %s" % (cmd.get("n"), cmd.get("trade")))))
    out = {"ok": True, "let_go": cmd.get("trade"),
           "annual_wage_bill": round(s.wage_bill(), 1)}
    if err:
        out["what_happened"] = err
    return out



def _cmd_train(s, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    quantity, err = _qty(cmd, "n", 1)
    if err:
        return {"ok": False, "error": err + ". Nothing was changed."}
    ok, msg = s.train(cmd.get("trade"), quantity, cmd.get("from"))
    if not ok:
        return {"ok": False, "error": msg}
    out = {"ok": True, "training": msg, "capital": round(s.capital, 1),
           "your_hours_left_this_year": round(
               max(0.0, s.director_pool() - s.director_hours_committed()), 1)}
    # TRAIN AND HIRE ARE TWO SEPARATE STEPS, and this message was the only
    # one a player saw at the moment they took the first of them. This
    # trade did not exist here before, and a project's hired_labour for it
    # draws only on people you have trained or hired INTO it - there is no
    # open market to fall back on the way there is for a smith or a
    # scribe. Nobody can do that work until the people above finish
    # learning, and 'hire' is how you add more without that wait, now that
    # the trade exists to hire into at all. A Rome player found this out
    # only when `start` refused a project outright, having read nothing on
    # this screen or on `why` that named the gap in advance.
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



def _cmd_commission(s, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    hours, err = _qty(cmd, "hours")
    if err:
        return {"ok": False, "error": err + ". Nothing was changed."}
    ok, msg = s.commission(cmd.get("trade"), hours)
    if not ok:
        return {"ok": False, "error": msg}
    return {"ok": True, "commissioned": msg, "capital": round(s.capital, 1),
            "note": "These hours are available to your projects this year only."}
