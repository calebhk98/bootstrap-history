# A resumed game rebuilds market memory that the unbroken game carries over

**Status:** open

Found during 507 Stage 7: when a good's market areas are re-partitioned, the unbroken game carries each market's
memory (remembered price, usual volume) into the new areas with `market_areas_follow`, while a game saved and
loaded rebuilds the areas and their memory from scratch. The two then disagree in those markets. With `--session`
every command is a save then a load (CLAUDE.md 4.6), so a player on `--session` and one in an interactive game
play different economies. It surfaced once through the save round-trip topic.

What it would take: save what `market_areas_follow` needs (or the followed memory itself) so a load reproduces it,
and extend the round-trip topic with a case that re-partitions a good's areas between the save and the next year
and asserts identical prices and volumes in the unbroken and resumed games.
