# Endemic death rates read the civilisation's starting tiles, the epidemic step reads the tiles held now

**Status:** open

Two parts of the disease module disagree about which tiles a society lives on. The endemic death rates
(`sim/disease/burden.py`, `endemic_death_rates`) take `tiles_held(civilisation, world_map)`, the tiles the
civilisation's data declares at the start. The epidemic step (`sim/disease/people.py`) takes the `home_tiles_held`
view, the tiles the owner map gives the society now. After a conquest or a loss of land the endemic rates still describe
the old territory while epidemics run over the new one.

The move into the module kept both readings as they were (the equivalence check compares the deaths). The fix reads
`home_tiles_held` in both; the reproducing case is a world map where the society holds a tile its civilisation data does
not list, whose endemic loss is then left out.
