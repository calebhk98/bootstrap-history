"""SCENARIO: the labour market's demographics through a real game: the price curve against a realistic pool, the
`population` command, the hire refusal that says whose market it is. The pool arithmetic is in test_demographics."""
from .harness import *  # noqa: F401,F403

# --- the SAME curve (_labour_price_factor_from is untouched), fed a
# realistic denominator: hiring ten smiths against Rome's own reachable
# pool is barely a ripple, where the same ten against millwright - "the
# scarcest useful trade you can hire", deliberately left alone - still
# spikes hard, and a literacy-bound trade (scribe) still hits ITS ceiling
# (literate_capacity, not market depth) rather than being waved through.
s_rip = unopened_sim(capital=1e9)
s_rip.labour.market.press("smith", 10 * s_rip.HOURS_PER_PERSON_YEAR)
check("ten more smiths barely moves the going wage in a city this size",
      s_rip.labour.market.price_factor("smith") < 1.03,
      s_rip.labour.market.price_factor("smith"))
s_spike = unopened_sim(capital=1e9)
s_spike.labour.market.press("millwright", 10 * s_spike.HOURS_PER_PERSON_YEAR)
check("...while the same ten against a genuinely scarce trade still spikes",
      s_spike.labour.market.price_factor("millwright") > 2.0,
      s_spike.labour.market.price_factor("millwright"))

s_pop = unopened_sim(capital=1e9)
check("a trade that does not exist here at all has no national population "
      "either - trade_available() already says so, read once rather than "
      "claiming a pool for a trade this society cannot have at any price",
      s_pop.labour.national_trade_population("chemist") == 0.0,
      s_pop.labour.national_trade_population("chemist"))

# --- the 'population' command itself: every trade in WAGES accounted for,
# the country's own numbers present, and the framing sentence actually
# printed (not just computed and dropped) - this is the command a player
# asked for directly, so its presence and shape are pinned here rather
# than only exercised by hand.
_pop_r, _, _ = proto([{"cmd": "population"}])
_pop_out = _pop_r[0]
check("the population command answers ok and names the civilisation",
      _pop_out.get("ok") and _pop_out.get("civilisation"), _pop_out.get("civilisation"))
check("every trade in the wage table gets a row, fog or no fog - this is "
      "demography, not the tech tree",
      {trade_row["trade"] for trade_row in _pop_out.get("trades", [])} == set(WAGES),
      sorted(set(WAGES) - {trade_row["trade"] for trade_row in _pop_out.get("trades", [])}))
# presentation: the population note's framing
check("the one-town framing is actually said, not only computed",
      "one household" in (_pop_out.get("what_this_means") or "").lower()
      or "ONE household" in (_pop_out.get("what_this_means") or ""),
      _pop_out.get("what_this_means"))
check("'population' is in KNOWN_COMMANDS and survives the fog/pointer "
      "scanners above - no node id leaked, no dangling command reference",
      "population" in S.KNOWN_COMMANDS, S.KNOWN_COMMANDS)

# --- the hire refusal says WHOSE market this is, at the moment a player
# actually feels a price premium bite (not only in the literate-wall text,
# which already said this before this fix existed).
s_fr = unopened_sim(capital=50.0)
s_fr.labour.market.press("millwright", 10 * s_fr.HOURS_PER_PERSON_YEAR)
# Nothing left to spend: a squeezed market now finds only some of a big hire (Complaint 271), and the
# one it finds would otherwise be affordable, so the refusal this check reads needs an empty purse.
s_fr.capital = -s_fr.credit_limit()
ok_fr, msg_fr = s_fr.labour.hire("millwright", 3)
check("a cash refusal driven by a real price premium says this is one "
      "household's reach into one town's market, not a national figure",
      ok_fr is False and "population command" in msg_fr and "one town" in msg_fr,
      msg_fr)

# THE TWO COLUMNS OF `population` MUST NOT READ AS A CONTRADICTION. A
# specialised trade's reachable figure comes from its own separately tuned
# hiring ceiling while its country figure comes from the town-density law, so
# engraver reads 7,800 in the country and 3.1 within reach. Both are
# defensible - a specialist does not practise in every town - but a player
# who is not told will file it as a bug, and the whole point of this screen is
# to stop players inferring absurdities from numbers nobody explained.
_s_pop = unopened_sim(civ="rome_100ad")
_pop = S._agent_dispatch(_s_pop, NODES, {"cmd": "population"})
_pop_note = (_pop.get("what_this_means") or "")
check("the population screen warns that a specialised trade's reachable "
      "figure is tighter than its country total implies, before a player "
      "works it out and calls it broken",
      "specialised" in _pop_note.lower() and "do not" in _pop_note.lower(),
      _pop_note[-320:])
check("...and it still says the thing it was built to say, that every limit "
      "is one household's reach into one town",
      "ONE town's labour market" in _pop_note, _pop_note[:160])

# A topic module that prints a summary or exits stops every later topic from running.
# A topic module must only run checks. Printing and exiting belong to the
# runner, and sim/tests/test_suite_portability.py now fails if any topic module
# calls sys.exit at import time.
