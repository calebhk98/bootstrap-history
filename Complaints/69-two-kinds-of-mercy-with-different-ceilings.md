# Household epidemic mitigation and national mortality diverge because one is uncapped and the other is capped at 85%

## What the player saw

Broad health/public-infrastructure development reduced household staff-loss
severity dramatically (roughly 64-80% down to roughly 14%), while some
national epidemic waves still removed around 40% or more of the country. The
player rightly notes the code intentionally distinguishes personal/household
hedges from empire-wide diffusion, so some divergence is expected - the
concern is that it grew large enough for the household to be comparatively
protected while the surrounding society repeatedly approached extinction,
which then collided with the local labour-floor bug (`Complaints/58`).

## Verified against current code

Confirmed as a real, deliberate asymmetry between the two mitigation
channels, both still live in `sim/engine/society_hazards.py` and
`sim/engine/society_diffusion.py`.

**Household relief is a product of independent shares, with no ceiling of
its own.** `hazard_relief()` (`society_hazards.py:29-71`):

    mult, why = 1.0, []
    for node, share, label in self.HAZARD_COUNTERS.get(kind, ()):
        ...
        if got:
            mult *= (1.0 - share)
            why.append(label)

Each completed, `has()`-gated private mitigation multiplies a fraction off
what is *left* - diminishing, but with enough independent counters this
product can get arbitrarily close to zero (100% relief) with no explicit
floor stopping it. Nothing in this function caps the final `mult`.

**National/diffusion relief is explicitly capped at 0.85, and depends on a
slow diffusion index rather than on simply having the technology.**
`medical_diffusion_relief()` (`society_diffusion.py:507-518`):

    MEDICAL_DIFFUSION_RELIEF_CAP = declare(
        "MEDICAL_DIFFUSION_RELIEF_CAP", 0.85, ...
        why="Ceiling on how much the country's own absorbed medicine can "
            "soften an empire-wide epidemic's raw historical rate, "
            "leaving a residual so no cure ever reduces a historical "
            "pandemic to literally nothing.")

    def medical_diffusion_relief(self):
        return min(self.MEDICAL_DIFFUSION_RELIEF_CAP, self.medical_diffusion_index())

`_shock_staff_loss()` (`society_hazards.py:633-767`) applies the two
mitigations to two different figures, exactly as the player's own document
describes, and says so in its own comments: `loss` (household, from
`hazard_relief("staff_loss")`, private and immediate the moment the founder
personally has the relevant technology) reduces the household's own staff
and cash; `raw = historical * (1.0 - med_relief)` (national, from
`medical_diffusion_relief()`, gated on the *empire's* diffusion progress,
not on what the founder alone knows) reduces the empire-wide population hit
via `_apply_population_mortality_shock(raw)`.

This is a genuinely intentional design, not an oversight - the comment block
above `medical_diffusion_relief` narrates exactly the feature it was built
to answer ("invent the cure or the vaccine for a pandemic and the Black
Death becomes a minor period of some sickness rather than a catastrophe")
and explicitly limits it to 85% "so no cure ever reduces a historical
pandemic to literally nothing." The household side has no equivalent
residual floor because it was never framed as one - it is a sum of
independent, tuned, `has()`-gated hedges, most of them declared
`kind="temporary_heuristic"` and none of them declared with an eye toward
their *product's* combined ceiling.

Status: **confirmed as designed**, per the player's own framing (a design
review, not necessarily a code bug). What I can add beyond the player's
observation: the asymmetry is not merely "household reacts faster than
national diffusion" (expected, and fine) but specifically that one channel
(household) is architecturally uncapped while the other (national) is
capped and gated on a slower-moving index - so the GAP BETWEEN THEM is
unbounded in principle, not merely large in this one run. A civilisation
that completes every `HAZARD_COUNTERS["staff_loss"]` technology can, by
construction, drive household relief toward 100% while national relief can
never exceed 85% of the historical rate even at full diffusion, and in
practice sits well below that while diffusion is still spreading.

## Cross-references

`Complaints/17-plague-wage-feedback-missing.md` (closed) is adjacent
subject matter - an announced plague's wage shock not reaching the economy
- but is a different mechanism (feedback into wages, not the relief-channel
asymmetry itself) and was already resolved. No open complaint names this
specific two-channel divergence. Also worth reading alongside
`Complaints/58` in this batch, as the player's own document does: this
finding explains *why* a household can be comparatively untouched while the
nation collapses (a real, intended design), and `58` explains why the
game's *labour-market display* then fails to reflect that collapse once it
happens - two separate, real findings that compound in the same run rather
than one causing the other.

## What would resolve it

The player is right that the fix is not "force the two percentages to be
equal" - that would defeat the entire point of having a private,
immediately-actable hedge distinct from a slow, society-wide one, and would
arguably violate CLAUDE.md SS3.1 in the other direction (removing a real
mechanism - personal hedges genuinely working better than a whole empire's
slower uptake - in favour of a hardcoded equalisation). The player's own
suggested work is right: audit which mitigations affect which figure (some
technologies plausibly belong in both `HAZARD_COUNTERS` and the diffusion
index that feeds `medical_diffusion_index()`, and a quick read of
`HAZARD_COUNTERS["staff_loss"]`'s membership against the disease-diffusion
technology list was not done this session and would be worth doing), and
surface the distinction on the `risk`/health screens rather than changing
the mechanism. This is squarely a UX/legibility recommendation, not a
CLAUDE.md SS3.1/SS3.2 conflict either way.

One concrete, low-risk piece of the player's own suggestion that is worth
doing regardless of the audit above: giving household relief an explicit,
declared, tuned ceiling of its own (even a generous one, well above 85%)
would at least make the two mechanisms' *shapes* match - both "the harm
never quite reaches zero" - even while their magnitudes are allowed to
differ, which is closer to what `MEDICAL_DIFFUSION_RELIEF_CAP`'s own
justification argues for and currently only implements on one side.

## The invariant

Not a single-line bound the way most of this batch's findings are - the
player's own framing (a design review) is the right register for this one.
The closest testable property, if the audit above finds mitigations wrongly
scoped to only one channel: a technology whose note or tree category claims
a *national/public* effect (sanitation infrastructure, quarantine
institutions, vaccination campaigns) should register in
`medical_diffusion_index()`'s inputs; a technology whose note claims a
*personal/household* effect should register in `HAZARD_COUNTERS`. A
technology in neither, or wrongly in only the household list despite being
framed as a public-health institution in its own note, would be the kind of
mis-scoping worth a regression test once found.
