# Plague and famine event: "2,336 gone with the trade that stopped" has no unit

**Status:** open

The household hit line for a staff-loss hazard reads "staff -8%, 2,336 gone with the trade that stopped". The number is cash lost (`lose_capital`), but it prints as a bare figure beside a percentage, so it reads as people, labour-hours or money. The tester spent a note on it.

Reproduces by code reading: `sim/engine/society_hazards.py` builds it with `"%s gone with the trade that stopped" % "{:,.0f}".format(cash)` and no currency. Seeing it live needs a famine or plague to land on the household.

What it would take: append the currency name and say what it is ("2,336 pence of takings lost while the trade stood idle"). While there, check the rest of that message (the empire-wide clause) for other unlabelled numbers. Related: 202.

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.
