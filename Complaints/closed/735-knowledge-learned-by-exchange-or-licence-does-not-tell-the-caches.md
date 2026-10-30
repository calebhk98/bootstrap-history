# Knowledge a seat receives by exchange or licence does not tell the held-set caches

**Status:** closed - exchange and licence now go through the knowledge module's one add path (ReceiveTechniques), which tells the caches and bumps the version; the held containers refuse any other write.

`HouseholdParty.learn` and `HouseholdParty.accept_licence` (`sim/agents/household_party.py:104-113`) put the received
chain into the seat's `done` (and `granted`) with `done.update(chain)`. Every other write to the held set calls
`_done_changed()` (now the `LearnTechnique` command), which clears `household._done_seq` (the tree-ordered list
`done_in_order()` serves), `household._cap_factor` and bumps `done_version`. The caches that key on `done_version`
(`techniques_in_use.py`, `held_works.py`, `economy_goods.py`, `economy_materials.py`, `economy_production.py`,
`economy_mining.py`, `legitimacy.py`, `view_share.py`) and `done_in_order()` itself therefore keep the answer for the
old set until something else changes it. The callers are an exchange to a seat (`sim/agents/exchange.py:183`) and a
licence (`sim/agents/licence.py:41`).

The knowledge module kept the behaviour (a move does not fix bugs). Reproduced: on a built Han China game,
`game.seat_party(game.state.acting_seat).learn([node], None)` holds the node (`node in game.state.projects.done`) while
`node in game.done_in_order()` is False and `game.household.done_version` has not moved. What it would take: the
agents package cannot send commands, so the party's `learn` needs a hook to the engine (an extension point of the
knowledge module, or the exchange reply carrying the node ids for the engine to send `LearnTechnique`).
