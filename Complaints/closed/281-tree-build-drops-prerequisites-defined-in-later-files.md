# Building the tree from its branch files dropped a prerequisite defined in a later file, and 13 nodes fell off the goal's path

**Status:** closed

When the tree began to be built from `data/branches/` at load (complaint 141), the repair that adds a file's own id prefix to an unprefixed prerequisite ran one file at a time without knowing the ids later files define. `cap_power_grid` (in `00_capabilities.json`) asks for `power_grid`, defined in a file that sorts after it; the repair rewrote the prerequisite to `cap_power_grid` itself, the cycle breaker removed the self-edge, and the edge was then also deleted from the branch file to quiet the warning. The goal's required closure fell from 160 nodes to 147: the national grid and its whole chain stopped being needed for MW-scale power.

Fixed: the build collects every branch id before repairing, never rewires a node onto itself, and the edge is restored. Regression tests: `sim/tests/test_generated_tech_tree.py` (`LaterFilePrerequisites`), and `test_round8g_display.py`'s closure-size check, which caught it.
