# Difficulty curve: simple rules, difficult interactions, strong snowball

**Source:** playtest findings document, BAL-001, evidenced by section 6's
Rome and Mexica playtest narratives. **Status:** Balance observation.

## The player's reasoning

The game is not mechanically simple as a whole, even though individual
equations are individually understandable. Observed pattern across both
playtests: new or goal-focused play (beelining a hard research target) can
be brutally inefficient, while broad civilisation-first play compounds far
faster; catastrophes usually cost time rather than ending the run outright;
and once the positive loops are understood, late-game money can become
nearly irrelevant. Their recommendation: do not raise early difficulty.
Instead, let success create new late-game constraints (management,
politics, independent competitors, state extraction, urbanisation,
international logistics, capital allocation), which keeps the snowball
satisfying without making the rest of the game trivial.

## The evidence from section 6

The Rome hard-goal run (junction transistor, no save-scumming, completed
around year 483/484) is described by the player as "intentionally
inefficient in retrospect": direct goal-beelining performed much worse than
civilisation-wide development would have, and by the run's end the founder
had far less organisational throughput than an optimised civilisation-wide
strategy could plausibly achieve. The Mexica non-research run (75% general
literacy, fog on) shows the other side of the same pattern: broad
development across agriculture, institutions, public health, finance,
printing and industrial power eventually produced strong economic
compounding and much better resilience to the invasion/epidemic stress test
it went through. Both playthroughs support the same conclusion independently.

## How this sits against CLAUDE.md

This is not a §3.1/§3.4 finding; it does not propose deriving something
currently hardcoded. It is closer to §3.2: the recommendation is explicitly
about which late-game constraints to add, and every one of them (management
hierarchy, competitors, state extraction, urbanisation, international
logistics, capital allocation) is already filed separately in this batch
(`Complaints/107` through `Complaints/113`). This finding's role is to state
the balance principle that ties them together: the goal is new constraints
at scale, not higher early difficulty and not revenue suppression (the same
point `Complaints/105`, ECON-003, makes from the wealth angle specifically).

## Size

Not implementation work by itself. This is a design principle to check
future balance changes against, and it is already, in effect, satisfied by
how `Complaints/107` through `Complaints/114` are framed (each adds a new
late-game constraint rather than nerfing something that already works).

## Cross-references

`Complaints/105` (ECON-003, extreme wealth is not a bug) makes the parallel
argument for wealth specifically. `Complaints/107` through `Complaints/114`
(the LATE- findings) are the concrete mechanisms this principle argues for.
