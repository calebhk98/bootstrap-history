"""SCENARIO: the labour market's demographics through a real game: the `population` command and the hire refusal when a pressed
trade's price puts a hire past the purse. The pool arithmetic is in test_demographics, the price curve against a pool in
test_labour_price_factor_rule, and a trade that does not exist here having no national population in
test_labour_population_derived_scenario."""
from .harness import *  # noqa: F401,F403

# --- the 'population' command: every trade in WAGES accounted for and the civilisation named
_pop_out = S._agent_dispatch(unopened_sim(capital=1e9), NODES, {"cmd": "population"})
check("the population command answers ok and names the civilisation",
      _pop_out.get("ok") and _pop_out.get("civilisation"), _pop_out.get("civilisation"))
check("every trade in the wage table gets a row, fog or no fog - this is demography, not the tech tree",
      {trade_row["trade"] for trade_row in _pop_out.get("trades", [])} == set(WAGES),
      sorted(set(WAGES) - {trade_row["trade"] for trade_row in _pop_out.get("trades", [])}))
check("'population' is in KNOWN_COMMANDS", "population" in S.KNOWN_COMMANDS, S.KNOWN_COMMANDS)

# --- a hire past the purse, at a price the pressure on the trade has raised, is refused for cash
s_fr = unopened_sim(capital=50.0)
s_fr.labour.market.press("millwright", 10 * s_fr.HOURS_PER_PERSON_YEAR)
# Nothing left to spend: a squeezed market now finds only some of a big hire (Complaint 271), and the
# one it finds would otherwise be affordable, so the refusal this check reads needs an empty purse.
s_fr.capital = -s_fr.credit_limit()
refusal = S._agent_dispatch(s_fr, NODES, {"cmd": "hire", "trade": "millwright", "n": 3})
check("a hire driven past the purse by a real price premium is refused for cash",
      refusal.get("ok") is False and refusal.get("cause") == "cash_short", refusal.get("cause"))
