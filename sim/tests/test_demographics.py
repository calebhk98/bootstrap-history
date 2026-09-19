"""demographics: regression checks, run individually with `--only demographics`."""
from .harness import *  # noqa: F401,F403

# =============================================================================
# THE DEMOGRAPHICS FIX: the labour market was sized for a village. Measured
# on the pre-fix build: market_supply("smith") was 22,500 hours - 11.25
# people - for the whole of Rome, and hiring one scholar moved
# labour_price_factor from 1.0000 to 1.6151, a 61% jump, against a
# civilisation of 65,000,000 the game never told the player it was not
# actually reaching. Three things to pin: the reachable pool for a common
# trade is now realistically sized, a genuinely scarce or literacy-bound
# trade still spikes, and the 'population' command that is supposed to make
# all of this visible actually says what it claims to.
# =============================================================================

# --- a common, urban trade (smith - no special note, on the explicit
# "common" list) now reads a real town's worth, not a village's. Pinned to
# the formula itself (TOWN_POPULATION_REFERENCE x TRADE_DENSITY["common"] x
# HOURS_PER_PERSON_YEAR at Rome's own pop_scale of 1.0) rather than to a
# bare "> 11.25", so a future recalibration of the constants moves this
# check's expectation with it instead of silently drifting out of sync.
s_dm = sim(capital=1e9)
_expect_common = (s_dm.TOWN_POPULATION_REFERENCE * s_dm.TRADE_DENSITY["common"]
                  * s_dm.HOURS_PER_PERSON_YEAR)
check("a common trade's reachable pool is a real town's worth, not the old "
      "11.25-person village",
      abs(s_dm.market_supply("smith") - s_dm.employees.get("smith", 0.0)
          * s_dm.HOURS_PER_PERSON_YEAR - _expect_common) < 1.0,
      (s_dm.market_supply("smith"), _expect_common))
check("...which is at least two orders of magnitude above the pre-fix "
      "figure of 22,500 hours, not a marginal tweak",
      s_dm.market_supply("smith") > 22500.0 * 10,
      s_dm.market_supply("smith"))

# --- the SAME curve (_labour_price_factor_from is untouched), fed a
# realistic denominator: hiring ten smiths against Rome's own reachable
# pool is barely a ripple, where the same ten against millwright - "the
# scarcest useful trade you can hire", deliberately left alone - still
# spikes hard, and a literacy-bound trade (scribe) still hits ITS ceiling
# (literate_capacity, not market depth) rather than being waved through.
s_rip = sim(capital=1e9)
s_rip._add_labour_pressure("smith", 10 * s_rip.HOURS_PER_PERSON_YEAR)
check("ten more smiths barely moves the going wage in a city this size",
      s_rip.labour_price_factor("smith") < 1.03,
      s_rip.labour_price_factor("smith"))
s_spike = sim(capital=1e9)
s_spike._add_labour_pressure("millwright", 10 * s_spike.HOURS_PER_PERSON_YEAR)
check("...while the same ten against a genuinely scarce trade still spikes",
      s_spike.labour_price_factor("millwright") > 2.0,
      s_spike.labour_price_factor("millwright"))

# --- reachable_trade_population and national_trade_population: the two
# numbers 'population' shows side by side. Reach well above the old
# 11.25-person figure, and the country's own total bigger again than one
# household's reach into it (a trade is not entirely HELD by one town).
s_pop = sim(capital=1e9)
_reach_smith = s_pop.reachable_trade_population("smith")
_nat_smith = s_pop.national_trade_population("smith")
check("reachable_trade_population reads market_supply as people, not hours",
      abs(_reach_smith - s_pop.market_supply("smith") / s_pop.HOURS_PER_PERSON_YEAR) < 1e-6,
      _reach_smith)
check("the country holds more smiths than one household's own town reaches",
      _nat_smith > _reach_smith, (_nat_smith, _reach_smith))
check("a trade that does not exist here at all has no national population "
      "either - trade_available() already says so, read once rather than "
      "claiming a pool for a trade this society cannot have at any price",
      s_pop.national_trade_population("chemist") == 0.0,
      s_pop.national_trade_population("chemist"))

# --- scholar and scribe: reachable_trade_population reads the SAME wall
# hire()/train() actually enforce (literate_capacity, floored at 1.5), not
# market_supply's own unfloored figure - otherwise a thin civilisation
# (Norse) reads "0.2 scribes within your reach" on the population screen
# while hire() will in fact grant one, which is the false "nobody's there"
# literate_capacity's own floor exists to prevent (see that function's
# docstring).
s_lit_pop = sim(civ="norse_900ad", capital=1e9)
check("a literate trade's reachable figure matches the real hiring wall, "
      "not the unfloored market-share number beneath it",
      s_lit_pop.reachable_trade_population("scribe")
      == s_lit_pop.literate_capacity("scribe"),
      (s_lit_pop.reachable_trade_population("scribe"),
       s_lit_pop.market_supply("scribe") / s_lit_pop.HOURS_PER_PERSON_YEAR))

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
s_fr = sim(capital=50.0)
s_fr._add_labour_pressure("millwright", 10 * s_fr.HOURS_PER_PERSON_YEAR)
ok_fr, msg_fr = s_fr.hire("millwright", 3)
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
_s_pop = sim(civ="rome_100ad")
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

# NOTHING FOLLOWS: a RUNNER'S EPILOGUE here - the === banner, the
# "N checks, N failures" summary, the slowest-five table, the FAILED list,
# the subprocess tally, the --profile dump, and `sys.exit(1 if FAILURES
# else 0)` - is exactly the bug this guards against. sim/tests/__main__.py
# already prints all of that. A `sys.exit` here instead reaches this
# module, prints a plausible summary, and TERMINATES, so the ten topics
# listed after "demographics" in __main__.TOPICS never run. Ninety-three
# checks - every complaints_* module, dynamic_wages, economic_levers_inventory,
# explicit_starting_techs and all four realism_part modules - would never
# once execute in a full-suite run, and the run would say "0 failures" on
# its way out.
#
# The failure mode is worth naming because it is not "the tests fail". It is
# "the tests report success for work they did not do", which is the only kind
# of test failure that gets more dangerous the longer it survives. The TOPICS
# list even carries a comment about an EARLIER round of the same bug, where
# those modules existed on disk but were not registered; registering them
# alone would not fix it, because the run would still stop here.
#
# A topic module must only run checks. Printing and exiting belong to the
# runner, and sim/tests/test_suite_portability.py now fails if any topic module
# calls sys.exit at import time.
