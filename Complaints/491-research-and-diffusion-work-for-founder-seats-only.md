# Research, staged adoption and diffusion work for founder seats only; a country's own discoveries are invisible

**Status:** open

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
