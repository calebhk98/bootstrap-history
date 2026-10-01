# `lens_grinding` says it is the best year-one product and buys a first patron, but it needs a workshop that needs a patron

**Status:** closed

`lens_grinding` has `pre: ['workshop_first']`, and `workshop_first` has `pre: ['patron_local']`. Its note says "This is your best year-one revenue product and it also buys you your first patron",
while `patron_local`'s note says the cheapest entry gift is a pair of reading lenses. A player cannot follow the advice in either direction: the patron needs the lenses and the lenses need the patron.
The tester spent decades looking for the missing step to case hardening (same chain: `case_hardening` needs `workshop_first`) and only found it by building a patron.

    python3 -c "import json;d={n['id']:n for n in json.load(open('data/tech_tree.json'))['nodes']};print(d['lens_grinding']['pre'],d['workshop_first']['pre'],d['patron_local']['pre'])"

What it would take: decide which order is intended; either add a small demonstration lens that does not need the workshop (the tester's suggestion), or rewrite the two notes. A cross-note check (a note that says "buys" node X must not sit behind X)
would be hard to automate, but this pair is cheap to fix. Related: 72 (fog gives no directional hint; the hidden gate here was social, not material).

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 39, 65, 66). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.

**Fixed:** notes rewritten: the lens says it needs the workshop and wins later patrons; the patron entry gift is lenses bought from a local grinder until you own a workshop.
