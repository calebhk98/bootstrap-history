# Dispersing an insolvent household's dependants raises its artisans when they were below the floor

**Status:** fixed (`sim/workforce/applying_hours.py` `disperse_dependants` uses `rules.count_after_bleed`; regression test
`sim/tests/test_disperse_dependants.py`)

When a household is judged insolvent, the finance module sends `DisperseDependants`: its freedmen leave and its artisans fall by
a share, stopping at a floor. The handler set the artisans to `max(floor, artisans * retention)`, so a household that already had
fewer artisans than the floor gained artisans, hired by its own insolvency. The same flaw as Complaint 763 (the staff bleed),
found while fixing that one. A count below the floor now stays as it is.
