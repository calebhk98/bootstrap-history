# Staged adoption, awareness, contact triggers and subsidy levers are missing from research and diffusion

**Status:** partly (awareness, staged adoption, technique levers, own stock, contact events and share-weighted plants are built and tested; the remainder is at the end)

What is wrong now:

- **Two stages, not a ladder.** A technique is known, built or operating; `adopt_yrs` is folded into `yrs`
  at load (`sim/engine/tree_merge.py`, `sim/engine/mods.py`). No per-country adoption share, so "this country has
  aircraft, but only a few" is not state.
- **Diffusion has one carrier.** Exposure is visibility by distance (`sim/agents/country_view.py`,
  `exposure`). No carrying by trade, espionage or battlefield contact, and no "knows it exists" state that
  cuts the search without granting the skill to make it.
- **Contact triggers are thin.** Expedition `returns` exist (`sim/engine/action_results.py`) and only route
  nodes use them; no node requires samples brought back from a region (rubber, latex).
- **No state subsidy or mandate.** Governments copy what they value (`sim/agents/government.py`), but cannot
  pay or order firms and mines to adopt a technique that does not pay.
- A firm's or state's materials are checked against the market only (an actor's own stock is not counted).
- Related: Complaint 478 (closed; techniques gained after the opening reach the agent economy).

Why it matters: all three reports separate discovery from deployment and diffusion, and want a state to
push a technology that the market would not adopt.

What it would take: an awareness state and contact events that discount search; per-actor adoption stage and
unit count; subsidy and mandate levers on the government (481).

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
- Left: the gaps listed at the top; a state's research choice is only as good as the node `gains` and `traits` data it weighs.
- Done: awareness (`sim/agents/awareness.py`). An actor that takes part in knowledge spreading may take up a node
  someone has shown only once it is aware of it (`knows_it_exists`; imitation candidates, the research gate's
  `unaware` cause and `research.diffuse` all read it). Awareness comes yearly with chance `hazard(volume)` from the
  contact volume with the holders (`world.contact_volume`: neighbours by observation range plus tonnes carried
  between the places, `sim/engine/agents_port_research.py`), recorded contact events (`record_contact`, fading) and a
  founder's demonstration (`world.exposure`). It gives no skill. Test: `--only staged_adoption`.
- Done: staged adoption (`sim/agents/adoption.py`): aware, trying (pilot share), adopted; the share follows
  share' = speed * gap * share * (1 - share) with the gap the relative margin over the actor's other concerns
  (Griliches 1957 logistic, slope tied to profitability; the speed constant is a labelled heuristic). A technique
  that does not pay is dropped after the trial.
- Done: levers `trial_subsidy` and `tech_mandate` (`sim/agents/government_levers.py`), paid from the state's treasury
  in `adoption.advance_actor` (subsidy per trying actor; the state makes a mandated actor whole for realised losses).
- Done: the start gate counts the actor's own stock (`research_gate.materials_short_of_stock`, `Actor.held_tonnes`
  from the record's `stores`).
- Done: the share reaches production. `adoption.plant_weight` weights a plant of the technique by the owner's share
  (1.0 when the owner has no record), and `business_books.operate` and `business_crew.staff` run the plant at
  size times weight, so crew, takings and wages follow the share; `adoption.observed_gap` reads the plant's margin per
  unit of share. Test: `--only adoption_reaches_production`.
- Done: the engine records contact on a conquest (`campaign_year._take` calls `contact_events.after_conquest`) and on a
  migration (`regional_people.step_regions_of_people` calls `contact_events.after_migration` from `migrant_pairs`).
- Done: purchases a buyer that `keeps_purchases` (a firm) makes at the market are delivered to its `stores`
  (`economy_port_actors.close` returns the delivery by good; `stock_keeping.add_delivery`).
- Remainder: (3) no node requires samples brought back from a region (expedition `returns`, rubber and latex);
  (4) the contact and speed constants are heuristics (`sim/agents/tuning_adoption.py`): contact would be retired by a
  measured carrier (tonnes, migrants, routes) and the logistic speed by a curve fitted to Griliches-style adoption
  data, neither of which has a source opened yet; (5) no firm calls `market_purchase` yet (a plant's inputs are
  costed in its books, not bought as goods), so firm stores fill only once a firm buys inputs or research materials as
  goods; (6) the effect of the share on a whole game is unmeasured (needs the slow suite and a baseline run).
