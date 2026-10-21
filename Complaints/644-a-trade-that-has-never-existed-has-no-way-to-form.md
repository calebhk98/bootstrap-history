# A trade that has never existed has no way to form

**Status:** open - four stages built (first hands from the nearest trades, migration and bonded purchase, a converted cohort's early slice); the owners' sale rule, a bonded price and a learning curve on output are open

**What is wrong now.** When a technique needs a trade nobody in the world practises (the first engine fitters, machinists,
printers), the first people now come from the nearest practised trade, by migration, conversion or bonded purchase. What is
still missing:

- Owners' sale rule and a price from the person's remaining service: `BONDED_SALE_SHARE_PER_YEAR`
  (`sim/agents/bonded_sale.py`) is a labelled share with `retire`; the price is a labelled number of years of the area's
  ask floor (`sim/economy/bonded_purchase.py`). People bought arrive with the bonded stratum's trade only and are not held
  bonded in the economy's workforce (they work as free hands); a country without home tiles offers none.
- A trade no recipe books hours to (optician) has no task description, so no source trade covers it and it gets no early hands.
- The early slice of a converted cohort is a flat share (`SOURCE_TASK_FLOOR_FRACTION`), not a proficiency rising by
  repetition (Wright 1936; Thornton and Thompson), so the error rate and the floor of output are not modelled; the
  teacher's proficiency does not cap the first cohort's start.
- `taught_from` links in `data/world/trades.json` are few (count with a `python3 -c` over the file); the registry link
  overrides the nearest trade when present. Conversion is carried out only through `train`.

**What it would take.** Output and error following a learning curve with a physical floor for any actor and trade; a
first cohort whose start is capped by the teacher; the owners' sale rule from the owner's own choice. Tests call the
training functions: a trade with no teacher stays empty; a nearer source trade trains faster.

**Sources.** `Complaints/reports/research-how-a-brand-new-trade-forms.md`: the first hands of a new trade came from the
nearest trades (Boulton and Watt's from millwrights, smiths and instrument makers), trained inside the inventor's firm on
narrow tasks; it was slow and early work was poor. Skill distance between occupations is measured from task content
(Gathmann and Schonberg). Learning curves: Wright 1936 with quality change and spillovers (Thompson; Thornton and Thompson).
How an existing trade spreads is in `research-how-trades-spread-and-skill-premia.md`.

**Research needed.** A supply-side source for bonded or captive labour as a market (what a trained slave craftsman sold
for against an untrained one in the Roman or Atlantic market, and how owners chose to sell), to replace the typed sale share.
See also 648, which needs the same supply side.

## Built (one line each)

1. `sim/labour/trade_formation.py`: task shares per trade from the hours recipes book to it; distance is the cosine angle
   between shares; `first_people_plan` orders migration, conversion and bonded purchase; `train` and `train_check` pick the
   nearest practised trade as source and take time and teacher hours from the uncovered share. The three flat teaching
   constants are retired. Tests: `test_trade_formation.py`.
2. `sim/labour/market/formation.py` runs after migration each year for every (area, trade) with vacancies and no one of the
   trade: migrants from areas with a route in, then bonded people where the area allows. Teachers are any actor that holds
   the knowledge (`teachers_of`, `teacher_present`). Tests: `test_trade_formation_routes.py`.
3. Bonded purchase is wired into a game (`sim/agents/bonded_sale.py`, `sim/engine/economy_port_bondage.py`,
   `sim/economy/bonded_purchase.py`). Tests: `test_bonded_purchase.py`.
4. A conversion cohort is written as two training records (`sim/labour/trade_first_hands.py`): an early slice equal to the
   covered share of the new trade's tasks joins after the floor share of a full apprenticeship, the rest at the end, so a
   founder can start such work inside the stall window (`STALL_YEARS_BEFORE_ABANDONMENT`). Tests: `test_trade_first_hands.py`,
   `test_trade_first_hands_scenario.py`.
