# Staff leave and concerns close without a notice

**Status:** closed - departures and closures are reply events with cause and what they stop; a departure that closes a concern stops the step

Found by both agent playtests (`Complaints/reports/playtest-rome-seed11-agent-legitimate-log.md` around 133 AD; `Complaints/reports/playtest-rome-seed7-agent-100-years-log.md`).
Hired masons and scholars left for better offers and concerns closed ("nobody left to keep an eye on") with no event
in the step's reply that a player would act on; auto-hire is off unless set by hand.

What it would take: each departure and each closure is a reply event with a `kind`, the cause and what it stops
(`sim/ui/proto/event_kinds.py`), and a step that loses staff a running concern needs stops early as other warnings
do; test that a departure that closes a concern shows in the step's events.

## Resolution

A departure is a `staff_lost` event with `reason`, `trades`, `stops` (the running concerns the staffing rule is about
to shut, from `concerns_to_close_for_staffing`, the function the closure uses, read after the year's rehiring) and
`stops_earnings_per_year`. When `stops` is not empty the kind is `staff_lost_stops_concerns`, listed in
`sim/ui/proto/event_kinds.py` as a stop, so a multi-year step ends on it. Payroll shedding, plague and sack losses go
through the same `log_staff_lost`. The closure event `concerns_closed_unstaffed` now carries `closed_because`, the
`short` resources and `stops_earnings_per_year`. Test: `sim/tests/test_complaint_579_staff_loss_events.py`.
