# Coal may stand in for charcoal where it cannot: smelting iron before coke

**Status:** closed

Once iron bar became makeable from a bloomery (complaint 127), coal's shaft-capital price fell far below charcoal's, and the Rome and England price solves now pick coal as their thermal fuel. As generic process heat that is physically defensible where pits are open: both societies burned coal locally. Raw coal cannot smelt iron, though: its sulphur makes the iron brittle, and coal only enters smelting once it is coked.

Check whether any recipe that reduces ore (bloomery, blast furnace, copper and lead smelting) accepts coal as its fuel option without a coking step. Where it does, that recipe's fuel choice should be charcoal or coke, with coke gated on a coking technique. Generic heat (lime burning, smithing, salt boiling, brewing) may keep coal.

    python3 sim/validate_production.py --todo
    grep -n "coal" data/production/*.json

Found while merging the bloomery recipe (branch `bloomery-iron-and-furnaces`), whose two `test_temperature_caps.py` assertions were widened to accept coal as well as charcoal.
