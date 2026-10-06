# The founder is not a `Player` actor: the founder and a second player run on two different rule sets

**Status:** closed - folded into 382

A second player (`sim/agents/player.py`) researches, runs concerns, hires from the shared pool and
pays through `ledger.transfer` (`sim/agents/concern_ops.py` is shared with firms). The founder does
the same things through the engine's own project, household and economy code (`sim/engine/`), which
`Household` (`sim/agents/household.py`) only fronts. As a result:

- **Research.** A player's research is copy-style work (hours, money and years from the node). The
  founder's research is the engine's project system.
- **Shared market.** The founder's concerns count as one rival in `ActorRegistry.rivals_of` through
  `world.is_public`. A player's concerns count through the registry's concern index.
- **Competitor entry.** Entrants follow any player's proven concern
  (`ActorRegistry.proven_concerns`). The founder's proven concerns come from the engine's own
  `proven_concerns`, with a different proof rule.

What it would take: Complaint 382's step 3 (per-actor household, project and knowledge state). The
founder then becomes a `Player` whose orders are the existing commands, and the two rule sets become
one.
