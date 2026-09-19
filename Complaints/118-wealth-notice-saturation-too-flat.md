# Wealth/state-notice saturation may be too flat at extreme fortunes

**Source:** playtest findings document, BAL-002. **Status:** Design review,
not a confirmed defect, confirmed accurately described against the current
code.

## The player's reasoning

The current state-notice system is better than no political response at
all and explicitly addresses billion-denarii play, but prominence wealth
contribution saturates at a relatively low "visibly rich" threshold, and
household-scale wealth contribution saturates at a larger but still finite
threshold. Past that, 20 million, 200 million and 2 billion denarii can
become similar or identical in some visibility calculations. Their
recommendation: this may be fine for bounded gameplay, but if extreme
fortunes remain common, consider whether requisition scale, political
bargaining power, confiscation stakes or state dependency should keep
changing past the point where notice probability itself saturates, rather
than raising hazard probability without bound.

## Checked against the current code

Both thresholds the player describes exist and are both hard caps at 1.0,
confirmed by reading `sim/engine/society_state_pressure.py` directly:

    EMINENCE_WEALTH_VISIBLE_THRESHOLD = declare(
        "EMINENCE_WEALTH_VISIBLE_THRESHOLD", 250000.0, ...)
    ...
    wealth = min(1.0, max(0.0, self.household.capital) / self.EMINENCE_WEALTH_VISIBLE_THRESHOLD)

and, separately, `household_scale()`:

    HOUSEHOLD_WEALTH_SATURATES_AT = declare(
        "HOUSEHOLD_WEALTH_SATURATES_AT", 10000000.0, ...)
    ...
    wealth_s = min(1.0, max(0.0, self.household.capital) / self.HOUSEHOLD_WEALTH_SATURATES_AT)

Both are `min(1.0, capital / threshold)`, a straight linear ramp that is
fully flat above the threshold. So capital at 20M, 200M and 2B denarii do
give the identical wealth term to `household_scale()` (all at 1.0), exactly
as the player describes.

This is not an oversight; the surrounding comment (also read directly)
records that the 10,000,000-denarii threshold was "chosen to fit the
measured trajectories of two dice-free trials," one of them reaching 4,213
employees and 1.77 billion denarii while eminence itself never once crossed
its own danger line - which means the code's own calibration trial already
ran a household at roughly 177x the saturation threshold and used that run
to confirm the mechanic behaves sensibly, not to extend the ramp further.
The saturation is a deliberate design choice, already correctly labelled
`kind="temporary_heuristic"` with `confidence="D"` on every constant
involved.

## How this sits against CLAUDE.md

§3.1 is not violated here (a saturating cap is not a hardcoded historical
outcome), but the player's proposed direction - let requisition scale,
bargaining power and confiscation stakes keep moving past the point where
detection probability saturates - would need those follow-on quantities
derived from wealth directly (a confiscation of a fixed fraction of a much
larger sum is already proportional without needing a new mechanism) rather
than a new escalating penalty invented from scratch.

## Size

Small to medium if scoped as "extend the consequences of an already-
saturated notice, not the saturation curve itself" (the player's own
preferred framing); larger if it turns into a genuinely unbounded political-
consequence system, which starts to overlap `LATE-008`'s interest-group
work (`Complaints/114`).

## Cross-references

`Complaints/105` (ECON-003) and `Complaints/117` (BAL-001) both argue the
same general point from different angles: do not solve a scale problem by
capping the underlying quantity, solve it with new proportional
consequences. `Complaints/114` (LATE-008) is the natural place for "state
dependency" or "political bargaining power" to eventually live if this
grows into a real system rather than a formula tweak.
