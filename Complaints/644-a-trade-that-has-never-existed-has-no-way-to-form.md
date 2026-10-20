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
