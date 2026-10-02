# Design principles

Decisions about what the model should and should not do, kept here because
they are not defects: there is nothing to fix, and each exists to stop a
future change from "fixing realism" with something that would make it worse.
Defects live in `Complaints/`; this file is for reasoning that should outlive
any one issue. Add a principle when an issue turns out to be a warning rather
than a bug.

## Researched is not manufactured, and the seam already exists

Do not add a blanket "years between research and deployment" delay.

A node already carries knowledge (`done`) separately from a running concern
(`operating`), and separate inputs for capital, founder and specialist hours,
materials, annual supply capacity and power. Construction and adoption run in
parallel (a node's `yrs` is the larger of `build_yrs` and `adopt_yrs`),
failure and retry risk are per node, and a newly opened concern ramps its
revenue rather than producing at once. Material consumption is spread over the
build. A player who holds the knowledge and is still slow is slow for physical
reasons the model already derives.

A universal delay would duplicate those mechanisms and would itself be a
hardcoded outcome (`CLAUDE.md` section 4.1). Real remaining gaps are specific:
sector-specific diffusion (`Complaints/112`), the growth curve
(`Complaints/101`) and supplier depth (`Complaints/111`), not the seam between
research and manufacture.

Verify the claim with `python3 sim/simulator.py why <node>` (build staff,
operating staff, floor, risk) and `sim/engine/economy_production.py`.

## Extreme late-game wealth is not, by itself, a bug

A founder who brings better metallurgy, guns, lenses, printing, food
production, machinery, medicine, finance and power to a preindustrial economy
should be able to become very rich. The realism gap is not that the founder
gets rich; it is that nothing yet captures who else shares the gains and what
new constraints appear at that scale.

So do not suppress wealth by crushing venture revenue, capping income or
scaling revenue down until the player stays poor. That is a hardcoded outcome
(`CLAUDE.md` section 4.1) and the wrong fix. The right fixes add mechanisms
that redistribute or constrain a growing economy: independent firms and
imitation competing margins away (`Complaints/103`), a state that taxes and
requisitions (`Complaints/105`), deeper capital markets (`Complaints/106`),
and political interest groups extracting concessions (`Complaints/110`). Any
of those will lower the founder's share as a side effect; that is the point,
and it is not a licence to shrink the economy directly.

Existing wealth-responsive mechanisms (state notice and prominence hazard in
`sim/engine/society_state_pressure.py`) already react to wealth; their
saturation at extreme fortunes is a separate defect (`Complaints/114`).
Read together with `Complaints/113` (snowball difficulty).
