# Eighty-three technologies make glass out of nothing

`treetool.py merge` dropped anything it could not resolve and wrote the tree
anyway. It printed a warning per drop, the warnings scrolled past, and the
merge reported success. Nobody counted them until the merge was made to
refuse, at which point the count was 1,235.

    python3 sim/treetool.py merge --dry-run

    category                         events    nodes   distinct names
    unpriced material                   664      551      209
    unknown trade                       153      148       35
    unresolvable prerequisite           418      365      302
    technology used as material           0        0        0
    dependency cycle                      0        0        0
    TOTAL                              1235      859

859 of 2,864 nodes, 30.0% of the tree, lost at least one requirement a
branch author wrote down. Those requirements were never priced into
anything, so every affected technology has been cheaper to build than its
own source data says.

The worst single case is soda glass:

    mat_glass_soda               83   unpriced material
    mat_steel                    60   unresolvable prerequisite
    mat_glass_labware            45   unpriced material
    mat_glass_boro               36   unpriced material
    master_screw                 35   unknown trade
    parchment                    32   unpriced material
    mathematician                22   unknown trade
    mat_brick                    21   unpriced material
    vacuum_tube                  21   unpriced material
    mat_glass_lead               18   unpriced material
    mat_spring_steel             16   unpriced material
    glass_blower                 12   unknown trade

Eighty-three nodes declare that they need soda glass. `data/prices.json` has
no entry for it under any spelling `data/branches/ALIASES.json` maps, so the
merge deleted the requirement from all eighty-three and priced each of them
as though glass were not involved. A laboratory that needs glassware, a tube
that needs a sealed envelope and a window that needs a pane have all been
free of their glass since whenever this started.

## This is a costing bug wearing a tooling bug's clothes

It was found while making the build stop failing open, which is a
maintainability job. It is not a maintainability bug. Every one of those
1,235 deletions removed a cost, an hour or a dependency from a node that the
person who wrote the node said it needed, and the simulation has been
answering questions about feasibility and timing with those requirements
missing. A technology whose glass, steel and screw-cutting labour have all
been silently removed is not a cheaper technology, it is a different one.

The `mat_steel` row deserves its own note because it is the largest single
entry and it is NOT an unpriced material. It is an unresolvable
prerequisite: sixty nodes name `mat_steel` as a thing they depend on, no
node by that name exists, and the merge removed the edge. Those sixty nodes
have been reachable without steel.

## How much of it is real, and how much is spelling

Not all 1,235 are the same kind of problem, and the distinction decides how
expensive this is to fix.

Some are a missing character. `data/prices.json` prices a `glassblower` in
`wage_rates_denarii_per_hour`. The branch files ask for a `glass_blower`.
One underscore, twelve deleted labour requirements, and the trade is right
there in the file the merge was reading.

Some are a missing family. `purchase_prices_denarii` holds exactly one glass
entry, `glass_raw_kg`, and the tree asks for soda, borosilicate, lead and
labware glass as four separate materials with four different difficulties,
which is correct of the tree and is the whole reason the capability rungs
exist. `ALIASES.json` already does this job for steel, mapping
`mat_bulk_steel`, `mat_steel_plate_kg`, `steel_bar_kg` and `steel_ball_kg`
onto `steel_plate_kg`. Nothing does it for glass.

Some are a genuinely absent node. 302 distinct prerequisite ids name nothing
in the tree. `wood_construction` is asked for seven times, `newtons_laws`
six, `internal_combustion_engine` five. Those are not typos, they are
technologies the branch authors expected to exist.

So the 1,235 events are roughly 550 distinct names, and the names are what
has to be fixed rather than the events. That is a smaller job than the
headline number suggests, and it is still a real one.

## Why it went unseen this long

The merge printed every drop. It printed them as warnings, among other
warnings, and then said it had succeeded, so the only signal that a
technology had quietly lost its steel was a line in a log nobody reads after
a command that told them it worked. CLAUDE.md §3.4 requires that a heuristic
you cannot yet derive be labelled. A deletion is not a heuristic and there
was nowhere for it to be labelled, because the node that came out the other
side carried no record that anything had been removed from it.

`data/tech_tree.json` being both the merge's input and its output made this
durable rather than transient. A requirement deleted once does not come back
on the next merge, because the next merge reads the tree it already wrote.
The branch file still says the technology needs soda glass. The tree has not
said so for a long time.

## What has been done, and what has not

DONE: the merge now collects every such event, prints them grouped by
category, and exits without writing. `--accept-data-loss` overrides it and
still prints the full list, so a deliberate loss is recorded rather than
hidden. The dedup mapping moved to `data/branches/_MERGED_DUPLICATE_IDS.json`
so it stops living only in generated output.

NOT DONE, deliberately: none of the 1,235 are fixed. No material was priced,
no alias added, no missing node written. That is data work with real
judgement in it. Pricing soda glass sets what eighty-three technologies
cost, and guessing it to make a build pass would be the invention CLAUDE.md
§3.1 exists to prevent. Every number should come from the same place the
production data does, which is a physical fact rather than a figure chosen
to clear an error.

Removing `data/tech_tree.json` from git is blocked on this. A rebuild from
`data/branches/` alone is only lossless once the merge stops refusing, and
today it refuses.

## How to see it

    python3 sim/treetool.py merge --dry-run          # refuses, lists all 1,235
    python3 -c "import json; p=json.load(open('data/prices.json')); \
      print([k for k in p['purchase_prices_denarii'] if 'glass' in k]); \
      print([k for k in p['wage_rates_denarii_per_hour'] if 'glass' in k])"

The second command prints `['glass_raw_kg']` and `['glassblower']`, which is
the whole of what this project can price about glass, against a tree that
names five kinds of it.
