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
- Done: one gate function (`sim/agents/research_gate.py`) serves the founder and every actor: unmet prerequisites,
  `req_any` substitutes, scholar and craftsmen hands, materials someone sells. `research.begin` refuses with the
  first failing gate, as a `Refusal` carrying its `cause` (`scholar_staff`, `craft_staff`, `no_substitute`,
  `materials_unsold`, `prerequisites_unknown`, `cannot_afford`). Test: `--only research_start_gates`.
- Done: the founder's start (`start_project` in `sim/engine/projects_starting.py`) calls `research.begin` with the seat
  as researcher (`sim/engine/seat_researcher.py`); the seat answers hands, held stock and bill from its own books, and
  the founder's other gates (win condition, social approval, credit) still run first in `start_reason`. With the staff
  in place the founder's bill and an actor's plan for the same node are equal (`--only founder_research_shared_path`).
  Difference: an actor with no staff of a trade pays the hiring premium on that trade's hours; the founder's bill
  does not.
- Done: firms, AI players and states choose research through their decision policy (`sim/agents/research_choice.py`):
  a firm or player takes a node whose concern's takings at the economy's prices repay its cost over the valuing
  horizon; a state takes nodes its weighted gains value (`imitation_worth`). One programme at a time
  (`RESEARCH_PROGRAMMES_AT_ONCE`, a labelled heuristic). An actor reviews what to research only every
  `RESEARCH_REVIEW_YEARS` (its own year of the cycle), prices at most a few plans per review, drops candidates whose
  labour alone outruns their worth, and reuses a node's pioneer cost for that long (`SimWorld.research_cost`). Test: `--only research_chosen_by_actors`. Cost in a default
  game: `python3 sim/simulator.py` has no command for it; time `advance_actors` over a few years with and without.
- Done: `demonstrated()` is the seats' builds plus every active actor's own knowledge beyond the baseline, and
  `exposure` reads the holders' distance for those nodes, so imitation can copy from any actor
  (`--only demonstrated_reads_actor_knowledge`).
- Left: the staged-adoption, awareness, contact-trigger and subsidy sub-gaps are untouched; a firm's or state's
  materials are checked against the market only (an actor's own stock is not counted); a state's research choice
  is only as good as the node `gains` and `traits` data it weighs.
