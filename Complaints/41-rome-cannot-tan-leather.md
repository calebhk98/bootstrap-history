# Rome cannot tan leather or full cloth, and both are wrong

Found by the technique-to-node join (`requires_node`, Complaints/39), within
an hour of the first two slices landing, and worth recording for the method
as much as the finding.

## The finding

With 83 of 196 recipes labelled, exactly 12 are blocked for `rome_100ad`.
Sorted by how long the tree says the gating node takes to research:

    yrs=0.15  soap_kg                 ch2_rxn_saponification
    yrs=0.3   cloth_kg                tx2_fulling
    yrs=1.0   essential_oil_kg        distillation_alcohol
    yrs=1.0   paper_kg                prn_hand_papermaking
    yrs=1.0   silk_kg                 tx2_sericulture
    yrs=1.2   leather_kg              tex_vegetable_tanning
    yrs=2.0   porcelain_kg            mat_porcelain
    yrs=2.0   wood_pulp_kg            ch2_process_kraft_pulping
    yrs=3.0   carbon_kg               coal_coke
    yrs=3.0   concrete_reinforced_kg  mat_concrete_reinforced
    yrs=3.0   petroleum_refined_kg    mat_petroleum_refined
    yrs=3.0   quartz_tube_kg          cap_heat_2000

Nine of those are right. Paper is Chinese and reaches the Mediterranean
centuries later - Rome holds `mat_papyrus` and `prn_papyrus_sheets` instead,
which is the correct distinction. Sericulture stays a Chinese secret until
Byzantium around 550; Rome holds `mat_silk` and `tex_silk_trade`, so Rome can
BUY silk and not make it, again correct. Distilled spirits are medieval.
Coke, refined petroleum, reinforced concrete, porcelain and kraft pulping are
all plainly later.

Two are wrong.

**`tx2_fulling` - fulling.** The fullonicae of Pompeii are among the best
attested industrial installations in the Roman world; the Fullonica of
Stephanus survives with its treading stalls intact, the fullers had their own
collegium, and Pliny devotes passages to fuller's earth. A Roman fuller is
not a speculative reconstruction, it is a building you can walk through.

**`tex_vegetable_tanning` - tanning.** Roman tanneries are likewise
excavated and attested, and vegetable tanning with oak bark and sumac was the
standard method. Leather was a bulk military material: tents, shield covers,
boots, armour backing.

One is contested rather than clearly wrong. **`ch2_rxn_saponification`** -
Pliny (NH 28.51) describes *sapo* as a Gaulish invention used on the hair,
and Romans washed with oil and a strigil rather than soap. Marginal is a
defensible reading; so is "they knew how". Left alone pending someone who
wants to argue it.

## Why this is a finding about METHOD, not just about Rome

"Rome knew how to tan leather" was previously an assertion nobody could
check, because nothing connected a civilisation's technology list to anything
physical. `starting_techs` was 223 opaque ids. Now a recipe names the node it
needs, so the question becomes a script: which recipes can this civilisation
actually run, and does that list look like the society we know?

That check found a 2-in-12 error rate on its first run, over the small subset
of nodes that happen to be gates. It says nothing about the other 211 ids in
Rome's list, which remain unchecked because nothing points at them yet.

`Complaints/COMBINED_TECH_TREE_REALISM_REVIEW_part_01.md` already reached the
same class of conclusion qualitatively, with verdicts like MOVE TO START and
ALREADY ROMAN ("Rome should not research low-fired earthenware in 100 AD").
So the problem was known. What is new is that it is now MEASURABLE, and
measurable per civilisation rather than only for Rome.

## Deliberately not fixed here

CORRECTION, and it changes what this complaint is asking for. An earlier
draft of this section said the realism review's verdicts should be
cross-checked against `starting_techs` "when someone takes it". That job was
already taken and done - `aa5253a Make civilization tech starts explicit` and
`2435ece Resolve part 02 tech-tree realism findings`, before which every
civilisation held the same technologies give or take about five. The
stakeholder pointed this out; the git history confirms it.

So this is not an un-started job. It is a finished one with a residue, which
is a different and more useful thing to know: the differentiation pass got
the civilisations genuinely apart from each other, and what it missed is a
specific, small and now-measurable set. Tanning and fulling being held by
NOBODY is the signature of a pass that worked civilisation by civilisation
and never asked "is there a technology every single one of these societies
should have and none does".

Adding two ids to Rome would still be the wrong move on its own, for a
different reason than the draft gave: the gap is not Rome-shaped. It is five
civilisations wide, and the fix is one edit applied to all of them plus a
check that stops the class recurring. The sweep is four lines of
script and belongs in the suite once the labelling is complete, so that a
civilisation which cannot make something it historically made fails a test
rather than waiting for someone to notice.

Note also that this only checks what a civilisation can PRODUCE. Silk shows
why that is not the same as what it can OBTAIN: Rome trades for silk it
cannot make, and `data/production/` has no way to say so. Availability by
trade is a separate mechanism and this complaint does not cover it.

## It is not Rome. Nobody can tan leather.

The chemicals slice landed next and prompted the same sweep across all five
civilisations, which is where this stops being a Rome problem:

    england_1300     year=1300   starting_techs=202
    rome_100ad       year=100    starting_techs=223
    norse_900ad      year=900    starting_techs=148
    han_china_100ad  year=100    starting_techs=107
    mexica_1500      year=1500   starting_techs=34

    tex_vegetable_tanning   held by: NOBODY
    tx2_fulling             held by: NOBODY
    distillation_alcohol    held by: NOBODY
    prn_hand_papermaking    held by: NOBODY
    coal_coke               held by: NOBODY
    mat_paper               held by: england_1300, han_china_100ad

Tanning and fulling are held by NO civilisation in the game. Every one of
these five societies tanned hides and finished cloth; Han China in 100 AD had
a textile industry good enough that Rome bought its output. A technology that
every modelled society demonstrably had, and that none of them starts with,
is not a judgement call about Rome - it is a hole.

**England 1300 makes the fulling case worse, not better.** England in 1300 is
the fulling economy. Carus-Wilson's "An Industrial Revolution of the
Thirteenth Century" (1941) is specifically about English water-powered
fulling mills, of which there were hundreds by that date, and the tree even
has `tex_fulling_water` for exactly that. An England-1300 start that must
research fulling is wrong in the most documented direction available.

**Distillation is the same shape.** `distillation_alcohol` is held by nobody,
which is right for Rome and Han in 100 AD and defensible for Norse 900, and
wrong for England 1300: aqua vitae was medical currency by then, with Taddeo
Alderotti describing fractional distillation of wine around 1280.

The chemicals agent reported the identical availability pattern for England
1300 and Rome 100 AD across all 39 of its entries and read that as design
intent - industrial chemistry postdating even a 1300 start. That reasoning is
sound for Leblanc (1791) and the lead chamber (1746) and wrong for
distillation, which is medieval. An identical pattern between two
civilisations 1200 years apart should have read as a symptom, not a design.

**What is correctly modelled, and worth preserving in any fix:** paper. Both
England 1300 and Han China hold `mat_paper` while nobody holds
`prn_hand_papermaking`, so those two societies HAVE paper without being able
to make it. That is the same production-versus-trade distinction Roman silk
gets right, and it is the shape the tanning and fulling fix should NOT take -
those two are things these societies made, not things they bought.

**Unresolved, flagged not fixed:** `mexica_1500` holds 34 starting
technologies against Rome's 223. Some of that gap is real - no iron, no
wheeled transport, no draft animals - but 34 looks thin for a society with
chinampa agriculture, monumental stone construction, cotton textiles,
obsidian blade production and goldwork. Somebody who knows the period should
look; this complaint only observes the number.

## The tree is also missing nodes, not only the civilisations

Two chemicals entries were left deliberately unlabelled because no node in
the tree describes the process the recipe actually uses:

  - `citric_acid_kg` is the pre-1919 route, lemon juice to lime precipitate
    to sulfuric-acid regeneration. The tree's only citric node forces a
    choice between chemical synthesis and mould fermentation, both later and
    neither this.
  - `chrome_salts_kg` is sodium dichromate from roasted chromite, the early
    1800s chromate industry. The tree's chromium nodes are about
    aluminothermic reduction to the METAL, a different output by a later
    method.

That is the correct outcome under the schema - an absent field is a counted
gap, a wrong one is invisible - and it says the tree has holes of its own
that only became visible once something tried to point at it.

## The tree's own notes say these civilisations have them

The nonferrous slice found two more, and these are the clearest cases yet,
because the contradiction is inside a single data file rather than between
two of them. Both node notes are quoted verbatim:

**`cap_heat_1100`** - "Sustained 1100 C (hand-blown charcoal)":

> Already reached wherever bloomery iron, bronze casting and glass melting
> are practised. A man on a bellows tops out near here.

Rome practises all three. `rome_100ad` does not hold `cap_heat_1100`. The
consequence is that `antimony_kg` computes as unavailable to Rome, for a
metal worked since antiquity.

**`lead_metallurgy`** - "Lead sheet, pipe, litharge and cupellation control":

> This is already done, and done well, wherever there is a developed
> lead-mining and -working tradition (Rome is the best-documented case).

The node names Rome as its own exemplar. `rome_100ad` does not hold it.

So this is not a matter of taste about what a society knew. The tech tree
states which civilisations already have a node, in prose, in the node, and
nothing has ever checked that prose against `starting_techs`. The two files
were authored independently and never reconciled.

That suggests the fix is more tractable than a general realism audit: the
notes are already the answer for a large share of these nodes. Somebody
should extract the claims, check them against every civilisation, and turn
the survivors into a test. Prose is not machine-readable in general, but
"already reached wherever" and "Rome is the best-documented case" are not
subtle.

## A duplicate node pair, found the same way

The tree carries two nodes for one technique, from different branch files:

    zinc_metal          pre=[cementation_steel, refractory_fireclay]
    mt2_zinc_by_retort  pre=[cap_heat_1100, mat_charcoal]

Both are downward/retort distillation of calamine. They have different
prerequisite chains, so which one a recipe points at changes when zinc
becomes available. `data/branches/_SCHEMA.md` already warns that ids
duplicated across branch files make the merge fight itself; this is the same
failure in the node vocabulary rather than the material one. Flagged, not
resolved - picking a winner is a tree edit, and the labelling deliberately
does not make tree edits.

## Fixed

`tex_vegetable_tanning` added to all five civilisations, `tx2_fulling` to
four. Not to `mexica_1500`: fulling is wool finishing, and the Mexica worked
cotton and maguey. That distinction was the agent's own call and is the right
one - "every society had it" was the finding, and a technology for a fibre a
society did not use is not an instance of it.

    england_1300     204  tanning=yes  fulling=yes
    han_china_100ad  109  tanning=yes  fulling=yes
    mexica_1500       35  tanning=yes  fulling=no
    norse_900ad      150  tanning=yes  fulling=yes
    rome_100ad       225  tanning=yes  fulling=yes

No new prerequisite violation: `tex_vegetable_tanning` needs `mat_leather`,
which all five already held, and `tx2_fulling` has no prerequisites at all.
`Complaints/42`'s pin stays at exactly seventeen.

The acceptance test is that the materials now have a price where they had
none. They do, in both civilisations that were checked:

    leather_kg    9.175 labour-hours per kg
    cloth_kg     21.273 labour-hours per kg

Soap is deliberately still missing, as recorded above: contested rather than
wrong, and nobody has argued it either way yet.

What remains open from this complaint is the general question rather than
these two instances - whether any OTHER technology is missing from every
civilisation at once. The sweep that found these two is four lines and is not
yet in the suite, because it needs a judgement about what each society should
have rather than a graph walk. `Complaints/42`'s test covers the structural
half; this half still needs a historian.
