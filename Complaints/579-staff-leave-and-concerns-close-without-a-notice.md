# Staff leave and concerns close without a notice

**Status:** open

Found by both agent playtests (`Complaints/reports/playtest-rome-seed11-agent-legitimate-log.md` around 133 AD; `Complaints/reports/playtest-rome-seed7-agent-100-years-log.md`).
Hired masons and scholars left for better offers and concerns closed ("nobody left to keep an eye on") with no event
in the step's reply that a player would act on; auto-hire is off unless set by hand.

What it would take: each departure and each closure is a reply event with a `kind`, the cause and what it stops
(`sim/ui/proto/event_kinds.py`), and a step that loses staff a running concern needs stops early as other warnings
do; test that a departure that closes a concern shows in the step's events.
