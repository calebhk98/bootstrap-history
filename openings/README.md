# Shipped openings

Cache entries a new game's opening uses (the agent economy's hidden spin-up and the opening price solves),
compressed, so a player's first game of each civilisation skips them. `sim/engine/shipped_openings.py` reads
them; an entry is used only when its key (inputs, data files and source) matches, so after a change to the
economy or engine source they go stale and the game computes its own as before.

Regenerate before handing a build to players, and drop the stale ones:

    python3 sim/simulator.py openings --prune
