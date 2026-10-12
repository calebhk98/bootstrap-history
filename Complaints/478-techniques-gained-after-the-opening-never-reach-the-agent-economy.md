# Techniques and goods gained after the opening never reach the agent economy

**Status:** open

The agent economy's recipe set is fixed when it opens (`opening_values` and `allowed_entries` in
`sim/engine/economy_port_setup.py`). A technique the society gains later reaches no agent-economy
producer through `requires_node`, and a good introduced after opening (cement in `test_concern_volume.py`)
has no market entry at all.

Evidence: in `test_real_output.py`, a halved-labour technique held and run leaves price, traded tonnes
and real output identical to its twin after a closed year; four checks that a cheaper technique lowers
the price and raises real output were dropped for this reason and should come back with the fix.
`test_concern_volume.py` "...counts in real output once the market sells it" still fails on it.
This undercuts the project's premise: a founder's new technique should change what the economy makes.
