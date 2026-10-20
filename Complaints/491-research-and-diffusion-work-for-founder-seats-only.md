# Research, staged adoption and diffusion work for founder seats only; a country's own discoveries are invisible

**Status:** open (partly done: one research path and actor-to-actor diffusion exist; see Progress)

- **Only seat inventions can be seen or copied.** `demonstrated()` is `founder_inventions()`
  (`sim/engine/agents_port.py`). A `Player`'s or a country's own research never becomes visible to anyone.
- **Actor research skips the tree's gates.** `Player.start_research` (`sim/agents/player.py`) checks
  prerequisites and money only, not materials, staff, scholars or the start checks the founder passes
  (`sim/engine/projects_starting.py`). Research speed and odds take no scholar count, literacy or printing.
- **Two stages, not a ladder.** A technique is known, built or operating; `adopt_yrs` is folded into `yrs`
  and read nowhere else (`sim/engine/tree_merge.py`). No per-country adoption share, so "this country has
  aircraft, but only a few" is not state.
- **Diffusion has one carrier.** Exposure is visibility by distance (`sim/agents/country_view.py`,
  `exposure`). No carrying by trade, espionage or battlefield contact, and no "knows it exists" state that
  cuts the search without granting the skill to make it.
- **Contact triggers are thin.** Expedition `returns` exist (`sim/engine/action_results.py`) and only route
  nodes use them; no node requires samples brought back from a region (rubber, latex).
- **Substitutes are seat-only.** `req_any` quality factors (a bronze or copper boiler for an atmospheric
  engine) are read from the seat's done set (`projects_starting.py`); actors cannot use them.
- **No state subsidy or mandate.** Governments copy what they value (`sim/agents/government.py`), but cannot
  pay or order firms and mines to adopt a technique that does not pay.
- Related: Complaint 478 (techniques gained after the opening never reach the agent economy).

Why it matters: all three reports separate discovery from deployment and diffusion, and want a state to
push a technology that the market would not adopt.

What it would take: one research path for every actor through the founder's start gates; a register of
every actor's non-baseline knowledge for `demonstrated`; an awareness state and contact events that
discount search; per-actor adoption stage and unit count; subsidy and mandate levers on the government (481).

## Progress

- Done: `sim/agents/research.py` is one research path for every actor that has `researches = True` (a player,
  a firm, a government): `begin`, `plan`, `work_year`, `diffuse`. `Actor.start_research` and
  `Actor.work_on_research` call it, and `Actor.act` advances research for firms and states. The same node costs
  the same through the labour market and purse; progress scales with `research_productivity()` of the actor's
  country; completion adds the node to the actor's own `knowledge`. A research project is a `works` entry
  with `research: True`, which `work_on_copies` skips.
- Done: knowledge spreads between actors once a year (`ActorRegistry.advance` calls `research.diffuse`): an
  actor that knows what a node rests on learns it at the half-life the founder's venture diffusion uses
  (`Sim.knowledge_half_life_years`), scaled by the node's visibility at the distance between the two actors.
  Test: `python3 -m sim.tests --only research_every_actor`.
- Left: the founder's own research (`projects_starting.py`) is still its own path, not a caller of
  `research.begin`; actors still skip the start gates (materials, staff, scholars, `req_any` substitutes);
  no AI choice of research for firms and states (only a `Player` with an AI controller chooses);
  `demonstrated()` still reads seat builds only, so actor-known nodes are not copyable through
  `imitation.missing_chain`; the staged-adoption, awareness, contact-trigger and subsidy sub-gaps are untouched.
