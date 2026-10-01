# Fire-setting share for medium rock and the mining shift length are unsourced

**Status:** partly - shift is now Agricola Book II (seven hours, 348); medium-rock fire-setting share still unsourced

`sim/world/mine_fire_setting.py` charges fire-setting wood to hard rock only (`FIRE_SET_SHARE_OF_ROCK_BY_HARDNESS`, conf D) and converts man-days to hours with an eight-hour shift (`MINING_SHIFT_HOURS`, conf D). Ordinary vein rock (Laurion, Mendip, Noricum) is broken by hammer and wedge with fire-setting where it helps; the share is unknown. The shift length is not from a source read for this work. A source for either moves lead, copper, iron and mercury (medium rock) and every man-day-to-hours conversion. The wood is charged at its delivery labour only; the wood's land claim is in the price solver's wood recipe and is not added to deposit cost.

Related: 139, 284, 291, 305, 333, 342, 343, 349.
