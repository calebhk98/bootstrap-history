# Agricultural mechanisation frees a literacy ceiling and no farmhands

## What the player saw

Broad agricultural research raised the Mexica literacy ceiling from roughly
35% into the 60-70% range - the `agricultural mechanisation -> agrarian_slack()
-> higher literacy ceiling` chain worked exactly as advertised in play. But
the live demographic path that decides how many people must actually farm
never receives any of that same mechanisation. The engine appears to hold
two separate definitions of "farm labour freed": an abstract mechanisation
score that unlocks literacy, and a physical worker count that governs the
real economy, and they do not talk to each other.

## Verified against current code

Confirmed. `agrarian_slack()` moved from `society.py` to
`sim/engine/society_adoption.py:238`. It counts completed mechanisation
nodes from a cached id list built once from the tree
(`self._agri_mechanisation_ids`) and returns a square-rooted, capped 0..1
score, used only to widen the literacy ceiling
(`LITERACY_ROOM_WITHOUT_MECHANISATION` 0.35 up to
`LITERACY_ROOM_WITHOUT_MECHANISATION + LITERACY_MECHANISATION_ROOM` = 0.90,
`society_adoption.py:288-306`).

The live agricultural-demography path lives in `core.py`'s
`_demographic_recovery()` and now calls into
`sim/world/agriculture_labour.py` (the module the player's notes still call
`agriculture.py`, since split into `agriculture_yield.py`,
`agriculture_storage.py` and `agriculture_labour.py`):

    adult_equivalent_population = self._adult_equivalent_population(self.population)
    farm_workers_fte = agriculture.farm_workers_fte_for_population(
        adult_equivalent_population)

No `toolkit` argument is passed. `farm_workers_fte_for_population()`
(`agriculture_labour.py:216-243`) accepts an optional `toolkit` parameter and
forwards it to `fraction_of_population_that_must_farm()`
(`agriculture_labour.py:129-176`), which defaults to `DEFAULT_TOOLKIT` (the
"ard-and-sickle" reference technique, per its own docstring: "`crop`, `soil`,
`rotation`, `toolkit` and `storage_technique` each default to the original
wheat/ordinary-loam/two-field/ard-and-sickle/pit-silo combination"). Calling
`farm_workers_fte_for_population()` with no arguments, as the live path does,
reproduces the pinned reference-technique calibration figure every year of
every run, mechanised or not.

The mechanised toolkits genuinely exist as data - `HORSE_COLLAR_AND_MOULDBOARD`,
`SCYTHE_AND_CRADLE`, `MECHANICAL_REAPER` (`sim/world/agriculture.py:1297-1312`)
- but nothing in the live call path selects one of them from
`self.household.done`, the way `agrarian_slack()` itself already does for its
own, separate, literacy-only purpose. So the tree's own labour-saving
agricultural technologies exist twice in this engine: once as data the
literacy system reads, and once as data nothing reads at all.

Status: **confirmed in current code** - both functions read directly, `grep`
confirms `farm_workers_fte_for_population` has exactly one production call
site (`core.py`'s `_demographic_recovery`), and that call site passes no
toolkit.

    grep -rn "farm_workers_fte_for_population(" sim/engine sim/world --include=*.py
    sim/engine/core.py:1429:        farm_workers_fte = agriculture.farm_workers_fte_for_population(
    sim/world/agriculture_labour.py:216:def farm_workers_fte_for_population(

## Whether this is a bug or a design decision

The player's own framing is right to hedge here, and CLAUDE.md SS3.1 is
directly relevant: a *literacy* ceiling that moves with a square-rooted count
of completed mechanisation nodes is already a heuristic
(`agrarian_slack()`'s own docstring calls the exponent tuning "the fifth
mechanised technique matters far more than the fifteenth"), not a claim about
physical farm output. It would be legitimate for this project to decide the
two are deliberately different things - "agrarian_slack measures social
readiness to spare a child for school, not a measured change in farm
productivity" - and document that split explicitly. What is not legitimate,
per CLAUDE.md SS3.1's own farm-labour example almost verbatim ("the same
applies to... adoption timing and industrial output"), is leaving the
physical side silently un-derived while the literacy side visibly responds,
because a player (correctly, per this playtest) reads the literacy movement
as evidence the mechanisation "did something real" to the economy, when the
one physical channel this engine has for that claim - fewer required farm
workers - never moved.

## Cross-references

No existing open complaint names this specific gap. Adjacent to
`Complaints/48-technology-cannot-stop-people-dying-young.md` in spirit (a
tree-authored effect with no live physical consequence) and to `59` in this
same batch (`_pop_scale_base`, a different case of the same shape: a real
number the tree computes that a different, live system does not read).

## What would resolve it

The player's suggested fix - "create a single derived 'effective agricultural
production system' from researched/diffused farming technologies and feed it
into the physical agricultural model" - is the right shape and fits CLAUDE.md
SS3.1: `farm_workers_fte_for_population()` already has the exact seam for
this (its own `toolkit` parameter), so the work is choosing which of a
civilisation's completed technologies constitute the `Toolkit` to pass, not
inventing a new mechanism. The most direct route: derive a `Toolkit` from
`self.household.done` the same way `agrarian_slack()` already scans it for
mechanisation ids, and pass it into the `_demographic_recovery()` call site.
That is a real yield/labour-hours claim (CLAUDE.md SS4's production-data
discipline: "a yield is a physical fact... NEVER derived from what the
material sells for"), not a literacy-shaped heuristic, so it should be held
to `data/production/`'s standard, not `agrarian_slack()`'s.

At minimum, per the player's own suggested test:

> Completing major labour-saving agricultural technologies should measurably
> reduce the fraction of the population required in agriculture, not only
> raise the literacy ceiling.

## The invariant

    fraction_of_population_that_must_farm() computed with a civilisation's
    own completed toolkit-relevant technologies should differ measurably
    from the reference-technique figure, once such technologies are done -
    i.e. the two "farm labour freed" numbers (agrarian_slack's mechanisation
    score, and the live farm_workers_fte calculation) should move together,
    not independently.
