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

Still open: migration and bonded routes are not yet called by the yearly step (only conversion is wired through `train`); the founder is always the teacher, so knowledge held by other actors is not yet read; a learning curve on output (Wright) with an error rate and a floor is a later stage.
