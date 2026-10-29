# Endemic death rates read the civilisation's starting tiles, the epidemic step reads the tiles held now

**Status:** closed - fixed: `Burden.endemic_death_rates` reads `home_tiles_held`, like the epidemic step. Test: `sim/tests/test_map_reads_by_views.py` `test_the_endemic_death_rates_are_those_of_the_tiles_the_nation_holds` (a held tile the civilisation file does not list is counted). Numbers change only once land has changed hands.

Two parts of the disease module disagree about which tiles a society lives on. The endemic death rates
(`sim/disease/burden.py`, `endemic_death_rates`) take `tiles_held(civilisation, world_map)`, the tiles the
civilisation's data declares at the start. The epidemic step (`sim/disease/people.py`) takes the `home_tiles_held`
view, the tiles the owner map gives the society now. After a conquest or a loss of land the endemic rates still describe
the old territory while epidemics run over the new one.

The move into the module kept both readings as they were (the equivalence check compares the deaths). The fix reads
`home_tiles_held` in both; the reproducing case is a world map where the society holds a tile its civilisation data does
not list, whose endemic loss is then left out.
