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

Adding two ids to `rome_100ad`'s `starting_techs` would take a minute, and
that is exactly why it is the wrong move on its own. A realism review already
exists listing dozens of verdicts of this kind across the whole tree, and
hand-patching the two that this week's labelling happened to illuminate would
leave the other dozens untouched while making the list look tended.

The right job, when someone takes it: cross-check every MOVE TO START and
ALREADY ROMAN verdict in the review documents against each civilisation's
`starting_techs`, fix them together, and re-run the blocked-recipe sweep for
all five civilisations as the acceptance test. The sweep is four lines of
script and belongs in the suite once the labelling is complete, so that a
civilisation which cannot make something it historically made fails a test
rather than waiting for someone to notice.

Note also that this only checks what a civilisation can PRODUCE. Silk shows
why that is not the same as what it can OBTAIN: Rome trades for silk it
cannot make, and `data/production/` has no way to say so. Availability by
trade is a separate mechanism and this complaint does not cover it.
