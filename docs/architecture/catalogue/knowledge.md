# Module `knowledge`

What each seat knows and can see: techniques held, forgotten, revealed (fog), and the tree itself.

**Status:** moved in part (branch `mr/knowledge`). The package is `sim/knowledge/`; this file describes what shipped and
what is left, not the draft proposal. The held, granted, done-year and heard-of records and the tree itself are still
stored where the engine keeps them and are read and written through `legacy_*` views (section "Debts"); what a seat has
forgotten is the module's own state. Counts come from the module spec
(`python3 -c "import sys; sys.path.insert(0,'.'); from sim.knowledge.module_spec import MODULE_SPECS as s; print(len(s[0].publishes), len(s[0].applies))"`).

## What changed from the draft

- **Views: 14 instead of 3.** The draft folded eleven fog methods into one keyed `visibility` and the held set into one
  `techniques_held` table. Callers ask separate questions with separate shapes (a yes-or-no with a shared memo, a sentence
  from a list of ids, a scrubbed text, a one-sentence summary), so each is a view. Names kept from the bridge, shapes
  unchanged, bridge entries deleted: `tree`, `tree_nodes`, `techniques_held`, `techniques_granted`, `done_year`,
  `earliest_done_year`, `visibility`, `visible_to_player`, `prerequisite_message`. `techniques_done` (living stock's bridge)
  was a second view of the same set as `techniques_held`; defence stores now reads `techniques_held` and the entry is gone.
  New: `techniques_forgotten`, `corpus_hedge`, `fog_scrub`, `fog_summary`, `never_abandon`.
- **`visibility` is a quote, not keyed.** It takes the shared memo of one recursive descent (the start test asks it of each
  missing prerequisite, which asks the start test of its own), and a keyed view would key on the memo too.
- **Commands: 4 applied and 1 sent, not 3.** `LearnTechnique(node_id, year, granted)`, `ForgetTechnique(node_ids, year)`,
  `RevealNodes(node_ids)` and `RevealFrom(node_id)`. The draft's `RevealNodes` covered both hearing of another seat's work
  and finishing a node; they differ (one computes its targets from the tree, under fog only), so they are two. The draft's
  `seat` and `cause` fields are dropped: a command is for the acting seat, and nothing reads a cause. `via` is `granted`.
  No refusals: learning what is held and forgetting what is not are no-ops that still tell the caches, exactly as the old
  inline writes did. `RefreshDoneCaches` (sent, applied by the bridge) is the engine's `_done_changed`.
- **Moved to `rules.py` / `fog_words.py`** as functions of plain values: `in_tree_order`, `reveal_targets`,
  `earliest_done_year`, `corpus_hedge`, `never_abandon`, and the fog words (`prerequisite_label`, `prerequisite_names`,
  `strip_self_play_advice`, `scrub_hidden_ids`, `summary_sentence`, `hidden_prerequisite_kinds`, `free_prereq_hint`,
  `missing_prereq_message`). `starting_techs.py` and `save_fog.py` moved in as they were; `grant_starting_techs` is gone
  (the opening sends `LearnTechnique(granted=True)` once per technique).
- **Not knowledge's, left where they are.** `visibility.py` (how much of an invention an onlooker sees) belongs to diffusion
  and the seats' sight; `node_rederive.py` is production's (it prices the tree); `knowledge_risk` and `_epidemic_risk` in
  `FogMixin` are hazards' (a report on sack hazards that happens to read the forgotten record); `on_road_to_goal` stays in
  `FogMixin` because the goal-closure cache it fills is shared with `labour_port.py` and `society_hazards.py`, so it is
  seats' and reaches this module as the `on_road_to_goal` view (bridge). `knowledge_warning.py` is knowledge's by the
  catalogue but is a screen over `knowledge_risk`; it reads `has`, `is_visible` and `corpus_hedge_tiers` through the
  forwarders and did not need to change.
- **`done_in_order` and `_done_changed` stay in `economy.py`.** They are the engine's caches over the held set
  (`household._done_seq`, `_cap_factor`, `done_version`), read by production, materials, markets and legitimacy. The module
  bumps its own `done` channel on every write and tells the engine through `RefreshDoneCaches`; the hand-made counter goes
  only when its readers move, and every view here is uncached until then (the writers listed below bypass the commands).
- **The three-caller floor** is moot for `tree`: it has the readers of every module (`grep -rn '"tree"' sim --include=module_spec.py`).
- **Fog is not per seat.** The mode of the game (`state._fog`, `_fuzzy_estimates`, `_fuzzy_salt`) is read by the module through
  `legacy_fog`; it is set at the game's start and by a load, and has no module owner yet.

## Mixin classes and files absorbed

| Old | Now |
|---|---|
| `FogMixin` (`sim/engine/fog.py`) | `is_visible`, `missing_prereq_message`, `fog_scrub`, `fog_summary`, `never_abandon`, `reveal_from` and the free functions moved to `sim/knowledge/`; `knowledge_risk`, `_epidemic_risk`, `on_road_to_goal` stay (see above) |
| `Sim.has`, `Sim.corpus_hedge`, `CORPUS_HEDGE_*` (`core.py`) | `sim/knowledge/module.py`, `rules.py`, `constants.py` |
| `starting_techs.py`, `save_fog.py` | `sim/knowledge/` (same functions; `grant_starting_techs` replaced by the command) |
| `ForwardingPropertiesMixin.forgotten` | the `techniques_forgotten` view; the field left `ProjectsState` |

## State owned

`KnowledgeSeat.forgotten` (node id to the year a sacking took it). Relocated in `sim/tests/equiv_fields.py`:
`/seats/*/modules/knowledge/forgotten` was `/seats/*/projects/forgotten`.

## Views published

| View | Kind | Seat | Answers |
|---|---|---|---|
| `tree`, `tree_nodes` | keyed / table | no | the tech tree, by id and whole |
| `techniques_held`, `techniques_granted`, `techniques_forgotten`, `done_year` | table | yes | the live sets and records of the acting seat |
| `earliest_done_year` | quote | no | the year the first seat to hold a node finished it |
| `corpus_hedge` | table | yes | (loss chance, fraction lost, hedge node) a sacking faces |
| `visibility`, `visible_to_player`, `prerequisite_message`, `fog_scrub`, `fog_summary` | quote | yes / no | what fog lets the acting seat see, in words |
| `never_abandon` | keyed | yes | whether letting a node go costs what cannot be rebuilt |

None is cached: see "Debts".

## Reads

All through the bridge (`sim/engine/bridge_knowledge.py`) until their owners move: `legacy_tree`, `legacy_fog`,
`legacy_seats`, `category_trait`, `relied_on_running` (projects' running gates, keyed), `on_road_to_goal` (seats), plus
`legacy_projects` (existing, projects') and `start_check` (projects, published). Mechanics' `corpus_hedge_tiers` is a real
module view. `relied_on_running` is named for what it answers; the catalogue called the projects topic `running_gates`.

## Debts: state still shared with the engine, and every outside writer

Each goes when the field moves. A write that is not through a command is a reason a view cannot be cached.

- `projects.done`: `sim/agents/household_party.py:106,112` (`learn`, `accept_licence` of a seat as an actor: also does not
  tell the caches, Complaint 735), `sim/agents/household.py:347` (facade setter), `sim/engine/seat_handover.py:48` (merge),
  the `done` setter of `core_properties.py`.
- `projects.granted`: `sim/agents/household_party.py:113`, `sim/engine/seat_handover.py:49`.
- `projects.done_year`: `sim/engine/core.py` (`run` starts it empty), `sim/engine/baseline_game.py:31`,
  `sim/engine/opening_checks_run.py:76`, `sim/ui/cli_interactive.py:256`, `cli_agent.py:66`, `cli_economy_check.py:43`,
  `cli_economy_accounts.py:56` (each starts it empty).
- `projects.revealed`: `sim/ui/replay.py:57`, `cli_interactive.py:264`, `cli_agent.py:70` (through the `revealed` setter,
  which only grows), `sim/agents/household.py:402`, `sim/engine/core_properties.py:438`, `sim/engine/saveload.py:372`
  (a load keeps what the running game had heard). Readers: `sim.revealed` in `sim/ui/proto`, `seat_sight.py`.
- The tree: `sim.nodes` is replaced by `node_rederive.refresh_derived_nodes` and `opening_money.reprice_tree`, and built in
  `Sim.__init__`; 263 read sites in `sim/engine` (`grep -rnE '(self|sim)\.nodes\b' sim/engine --include=*.py | wc -l`).
- The fog switch: `core_properties.py` (`fog`, `fuzzy_estimates` setters), `saveload.py`.
- The engine's caches over the held set, which nothing but `RefreshDoneCaches` tells: `household._done_seq`,
  `household._cap_factor`, `done_version` (read by `techniques_in_use.py`, `held_works.py`, `economy_goods.py`,
  `economy_materials.py`, `economy_production.py`, `economy_mining.py`, `legitimacy.py`, `view_share.py`).
- `_done_changed` is also called for a changed tree (`node_rederive.py`, `opening_money.py`), after the economy opens
  (`core.py`) and on a load (`economy.py`): not knowledge events.

## Forwarders left (`sim/engine/forward_knowledge.py`)

`has`, `corpus_hedge`, `is_visible`, `missing_prereq_message`, `fog_scrub`, `fog_summary`, `never_abandon`, `reveal_from`.
The properties `done`, `granted`, `done_year`, `revealed`, `fog`, `fuzzy_estimates` of `core_properties.py` stay as aliases
of the legacy state; `forgotten` reads the view.

## Year phases

None.

## Hard spots

- Sums over the held set must go in tree order (`done_in_order`, still in `economy.py`; `rules.in_tree_order` is its rule).
- `LearnTechnique` from a completed project records the year before the project's stock grants and transfers run (they
  read neither the year record nor the held set's order). Everything else keeps its old order.
- The goal closure cache (`_goal_closure`) is never invalidated when the goal changes and is shared by three callers;
  `on_road_to_goal` keeps that behaviour.
