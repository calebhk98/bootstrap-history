# Carriage hours count sea and river hauls at the land mode's hours, skip port handling, and use one national wage

**Status:** open

Part of Complaint 552 (Carriage pays the poor without using their hours or any carriers).

Builds on `sim/economy/carriage_hours.py`.

**What is wrong.** Hired hours use the cheapest land mode's crew hours for sea and river hauls; handling hours are not counted; the rates are priced at one wage averaged nationally; the other modes' labour parts follow the cheapest mode's share.

**Evidence.** `sim/economy/carriage_hours.py`; `CarriageTable.set_scale`; the "Done" section of 552.

**Why it matters.** The labour market sees the wrong demand for sailors and porters (530).

**What it would take.** Use each mode's own crew hours, count port handling hours, and bid wages by area.

**Test.** A test: a sea haul hires sailor hours, a handled port adds handling hours, and a tile's wage is its area's.
