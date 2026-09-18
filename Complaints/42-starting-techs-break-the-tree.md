# Every civilisation holds a technology whose prerequisites it lacks

Found by the technique-to-node join, and cheap to find once anything pointed
at the tree at all: `starting_techs` has never been checked against the
prerequisite graph it draws its ids from.

    england_1300     holds 202  violations 4
    han_china_100ad  holds 107  violations 6
    mexica_1500      holds  34  violations 3
    norse_900ad      holds 148  violations 3
    rome_100ad       holds 223  violations 1

Seventeen in total, and no civilisation is clean. A violation is a node in
`starting_techs` one of whose own `pre` entries is not in `starting_techs`.

This is a different defect from `Complaints/41`, and the two point in
opposite directions. There, a civilisation lacked a technology it plainly
had. Here, it holds one it cannot have reached, because the thing that node
is built on is missing. Both come from the same cause: the civilisation
files and the tech tree were authored separately and nothing ever compared
them.

## Three of them are substantive, not bookkeeping

**`mexica_1500` holds `fud_maize`, `fud_chinampa` and `fud_cacao`, each of
which requires `exp_americas_factory`.** The Mexica are gated on European
contact for maize, chinampa agriculture and cacao - three things they
themselves developed, and two of which the tree is presumably modelling as
things Europeans ENCOUNTER. That is a defensible prerequisite for a European
civilisation and an incoherent one for this civilisation, and it is not a
typo: it is the prerequisite direction being written from one point of view
and then reused from another.

**`norse_900ad` holds `exp_openocean_navigation`, which requires a pendulum
clock, a sextant, a magnetic compass and a world map.** The Norse reached
Greenland and Vinland with none of those. The node's prerequisites encode one
specific method - instrumental European navigation - as though it were the
only one, when latitude sailing, a sun compass, known bird and whale
behaviour and landmark knowledge got the same job done. The right fix is
probably a second node for the non-instrumental method rather than loosening
this one, since the two really are different capabilities.

**`rome_100ad` holds `civ_dome_roman` without `mat_pozzolana`** - while
`rome_100ad.json`'s own prose says Rome "has pozzolana, which nobody else
will have for 1,[400 years]". The civilisation file states in words the thing
its technology list omits. Same failure as `Complaints/41`'s node notes, in
the other file.

The rest are more ordinary but still wrong: `han_china_100ad` holds
`blast_furnace` without `charcoal_industrial` (Han China genuinely had blast
furnaces from about the 5th century BC, so the holding is right and the
prerequisite is unmet), `cap_heat_1300` without `cap_heat_1100`,
`bellows_water_blown` without `water_power_scale`; `england_1300` holds
`mat_paper` without `rag_paper` and `water_power_scale` without
`crank_conrod`.

## Why this is worth a test rather than a fix list

Each one is individually arguable - some want the prerequisite added to the
civilisation, some want the tree's `pre` corrected, and `fud_maize` wants a
rethink of which direction the dependency runs. Somebody has to decide each,
and this complaint deliberately decides none of them.

What it does instead is stop the number growing.
`sim/tests/test_civilisation_prerequisites.py` pins the count at exactly the
seventeen that exist today, listed by name. Adding an eighteenth fails the
suite. Fixing one also fails the suite, with a message saying to lower the
pin - which is the right kind of failure, because it makes the fix visible
instead of letting the count drift quietly in either direction.

That is the same pattern `sim/tests/test_price_solver_cycles.py` used while
`Complaints/31` was open: a green suite pinning a known defect gets acted on,
a red one gets ignored.

## What it does NOT check

Only the first level - a held node's immediate `pre`. It does not check that
a civilisation's holdings are closed under the full transitive prerequisite
chain, and it says nothing about whether a civilisation SHOULD hold a node it
does not, which is `Complaints/41`'s question and needs a historian rather
than a graph walk.
