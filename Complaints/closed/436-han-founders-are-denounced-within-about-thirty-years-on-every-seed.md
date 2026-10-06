# Han founders are denounced within about thirty years on every seed

**Status:** closed - interest groups blamed the founder for all of a goods category's price fall, though firms sell into it too; `agents_group_sources` checks the founder's share

Every han_china_100ad scenario in the behaviour fingerprint ends with the founder dead within about 24-34
years, on main (`bcd8b65`) and on the labour branch alike:
- seed 1 ends in year 28 on main and 34 on the branch, "denounced: as a subversive";
- seed 2 ends in year 24 on both.

The other four civilisations run their full 100 or 200 years except for an occasional random event.
Measured with `python3 -m sim.tests.fingerprint check <baseline>` (run lengths), and with a 100-year scratch
run of seed 1 printing `sim.dead_reason`.

Why it matters: when one hazard ends every game for one civilisation within a generation, the hazard is
tuned against it, or it reads a quantity that is out of scale for Han. Complaint 435 shows Han wages two
orders of magnitude apart, so a wealth or visibility measure could be inflated. Either way, the Han
baseline cannot be validated past thirty years.

What it would take: read what drives the denunciation hazard's yearly chance for the Han founder (wealth,
visibility, office?) and compare it with the same quantity in Rome. File the measured cause, or fix it in
the hazard's own package.

Resolution (measured with a scratch run of seeds 1 and 2 printing scandal each year): the scandal was not a
wage-scale or wealth input. In Han the agent economy's firms copy the founder's profitable concerns, so
the sellers in a category are mostly firms, and the category's price falls on supply from all of them.
`goods_sectors` (`sim/agents/group_goods.py`) blamed the founder for the whole fall (blame share one), so the
producers' petitions fed scandal past the denunciation line. The blame share is now the founder's concerns
over every seller's (`founder_share` from `goods_categories`, `sim/engine/agents_port_groups.py`). Both Han
seeds now pass thirty years with scandal well under the line. A fingerprint run will move wherever firms
share a category with the founder.
