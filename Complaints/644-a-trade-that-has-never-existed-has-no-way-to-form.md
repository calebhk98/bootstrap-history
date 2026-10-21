# A trade that has never existed has no way to form

**Status:** open

When a technique needs a trade nobody in the world practises (the first engine fitters, machinists, printers), the
labour model has no rule for where its first people come from. `data/world/trades.json` links a trade to the trade it
is taught from in a few rows only (`taught_from`; count with a `python3 -c` over the file), and teaching is flat
constants (`TEACHING_HOURS_PER_PERSON`, `TEACHING_MATURATION_YEARS`, `TEACHING_FEE_MULTIPLIER`,
`sim/labour/labour_training.py`). PR #60's held question ("trades with demand but no workers") is this gap.

Sources (`Complaints/reports/research-how-a-brand-new-trade-forms.md`): the first hands of a new trade came from the
nearest trades (Boulton and Watt's from millwrights, smiths and instrument makers); they were trained inside the
inventor's firm, on narrow tasks; it was slow ("the slow process of breeding them") and early work was poor. Skill
distance between occupations is measured from task content (Gathmann and Schonberg); learning curves follow Wright 1936
with quality change and spillovers (Thompson; Thornton and Thompson). How an existing trade spreads (migration,
apprenticeship) is in `research-how-trades-spread-and-skill-premia.md`.

What it would take, general for any actor and trade: a task description per trade and per technique, derived where
possible from the hours recipes book to each trade rather than typed; a new trade's first cohort drawn from the nearest
trades at a training time set by the uncovered share of tasks; taught only by an actor that holds the knowledge, a
trainee starting no better than the teacher; output and error following a learning curve with a physical floor. The
three flat teaching constants retire. Tests call the training functions: a trade with no teacher stays empty; a nearer
source trade trains faster.

## Progress (first stage)

Done: `sim/labour/trade_formation.py` derives each trade task shares from the hours recipes book to it, by recipe and input material; distance is the cosine angle between shares; `first_people_plan` orders migration (limited to spare hands), conversion (time from the uncovered share of tasks, needs a teacher) and bonded purchase, and leaves a trade with none of them empty. `train` and `train_check` now pick the nearest practised trade as source (a registry `taught_from` still overrides), take their time and teacher hours from the uncovered share, and charge the source wage for the years. The three flat constants are retired; two labelled heuristics replace them (`SOURCE_TASK_FLOOR_FRACTION`, `TEACHER_ATTENTION_SHARE`, retire: this complaint). Tests: `sim/tests/test_trade_formation.py`.

## Progress (second stage)

Done: the labour core's yearly step (`sim/labour/market/year.py`) now runs `market/formation.py` after migration: for every (area, trade) where any employer has vacancies and no one of the trade works or trains, migrants come from areas with a route in, up to their spare hands (workers less what their own employers still bid for), then bonded people are bought where the area is in `YearInputs.bondage_allowed`, up to `bonded_for_sale`; the year's report carries `formed` by route. Teachers: `trade_formation.teachers_of` and `teacher_present` read the knowledge any actor holds (a trade's gating nodes are the `requires_node` of the recipes that book hours to it; the society's baseline and demonstrated techniques count), and `train_check` charges the founder's hours only when no other actor holds the knowledge, else pays that teacher's hours at the source wage. Tests: `sim/tests/test_trade_formation_routes.py`.

## Progress (third stage)

Done: bonded purchase is wired into a game. `sim/agents/bonded_sale.py` gives the tiles of countries whose profile has bondage (`has_bondage`), the bonded strata's people by trade on offer there (a labelled share, `BONDED_SALE_SHARE_PER_YEAR`, retire: owners' sale rule) and `buy_bonded`, which moves people out of the bonded stratum and pays its owner through the ledger. `sim/engine/economy_port_bondage.py` hands tiles and offer to the economy in `YearInputs.bondage_tiles` and `bonded_for_sale`; `labour_context` turns them into `bondage_allowed` and `bonded_for_sale` areas. The economy charges the employers bidding for the trade (`sim/economy/bonded_purchase.py`, price a labelled number of years of the area's ask floor) over the exchange edge, reports `YearOutcome.bonded_bought` and `bonded_paid`, and the port pays the owners from the economy edge. Tests: `sim/tests/test_bonded_purchase.py`.

Still open: the owners' sale rule and a price from the person's remaining service; people bought arrive with the bonded stratum's trade only, and are not held bonded in the economy's workforce (they work as free hands); a country without home tiles offers none; conversion is still carried out only through `train`; a learning curve on output (Wright) with an error rate and a floor is a later stage.
