# Typed `state_capacity` still drives enforcement, theft, mining ceilings and diffusion

**Status:** open

620 replaced typed `state_capacity` for tax collection with a share that follows the officials a state pays and the
travel time from its seat. The same typed number is still read by other systems as if it were a measured fact:
theft exposure and charges, mining and forest ceilings, state demand answers, technique diffusion and adoption,
the economy's tax forms and tax farming, state pressure, and the cause book. List the readers:

    grep -rn "state_capacity" sim --include=*.py | grep -v tests

Why it matters (CLAUDE.md 4.1): a state's reach over theft, mines and the spread of techniques should follow from
what it employs and how far its tiles are, as collection now does; one typed figure makes all of them inputs.

What it would take: for each reader, use the collectible-share machinery of 620 (`sim/agents/collection.py`) or the
specific staff that system needs (guards, mine inspectors), or say why the reader is a true initial condition.
Tests: each reader, given a built state with more officials or a nearer tile, moves the way the rule says.
