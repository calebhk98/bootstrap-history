# Government and Firm actors run every year but nothing reads their results

**Status:** closed - increments 1-6 of docs/architecture/ACTORS_NEXT.md are built and read by the engine; other countries as actors are 113

`sim/engine/core_step_phases.py:493` calls `self.advance_actors(...)` each year. The code inventory found no reader of their results outside `society_actors.py`: they do not affect the founder's revenue, prices, or any player screen.

Why it matters: it costs step time (see 185) and gives the impression, in code, of multi-actor economics that play does not have. CLAUDE.md's direction ("every mechanism the founder uses must be usable by any actor") needs these wired or clearly marked as scaffolding.

What it would take: either wire one consumer (e.g. state demand feeding requisitions or goods demand), or skip the phase and label it experimental.

Found by a code inventory made for the new-player playtest (`playtest_notes/code_systems_inventory.md`); each claim below was re-checked by grep.

Stakeholder decision: no quick fix (do not just skip the phase or wire a token consumer). Actors are being added slowly so they are done correctly. Even a single-player game is meant to be multiplayer: the country itself (Rome, China, ...) is another player, without the founder's future knowledge and with very different economics. Work on this is welcome, in properly designed increments (see 107 and docs/architecture/ACTORS.md).

Update: `docs/architecture/ACTORS_NEXT.md` sequences the work. Increment 1 is built: every actor purse change goes through a ledger by purpose, and requisition, the pressed office, military supply and confiscation are received by the government actor instead of vanishing (`python3 sim/actor_ledger.py` measures it). Nothing outside the actors reads the government's results yet; the measured reason is that the state's purse only accumulates, so the consumers (3 to 6 in the note) wait for a state that spends and has needs.

Update: firms are now read from outside the actors. The founder's labour market counts their staff (`Sim.actor_staff_fte`), the founder's goods market counts their concerns as sellers, and `Sim.actor_supply(material)` is the one function the market reads for their physical output. The state assesses a firm by the same rule as the founder's household (`Sim.visible_scale`, `Sim.levy_shares`, `Government.assess`), and the levy goes into the treasury. Measured: in a 125-year Rome run firms never grew large enough to cross the notice line, so their levy is zero in practice; the state's endogenous revenue from firms stays negligible until firms are big (`python3 sim/actor_ledger.py` measures it). Still open: the state's adoption (3), its demand and labour (5), the need-driven levy (6).

Update: the government keeps a budget (Complaint 109). Its spending is read from outside: staff in the founder's labour pool (`Sim.actor_staff_fte` counts the government's), iron purchases in the goods market (`Sim.actor_demand`), and the levy on every visible actor follows the state's unfunded need (`Government.seek_shortfall`, `Sim.levy_shares`). Measured: with only an army and officials as spending, every state runs a surplus and the levy is zero in a baseline run (Complaint 300). Still open: 3, patron funding (301).
