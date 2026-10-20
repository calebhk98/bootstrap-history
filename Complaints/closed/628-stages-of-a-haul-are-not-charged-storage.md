# Storage at stages of a haul is not charged

**Status:** closed - `merchants_transit.storage_per_unit` charges the storage of each year a haul is held beyond the first (`STORE_STORAGE_COST_PER_KG_YEAR` by the kilogram) in the route search, `gap_cost_per_unit` and the break-even price; tested in `StorageAtStagesTests` (`test_merchant_travel_time.py`). It is a route-choice cost, like interest on the extra years; no cash is paid to a storekeeper.

Part of Complaint 552 (Carriage pays the poor without using their hours or any carriers).

**What is wrong.** Travel time, spoilage and interest are covered; storage at stages is not charged.

**Evidence.** `sim/economy/merchants_transit.py`; `test_merchant_travel_time.py`.

**Why it matters.** Goods held at stages cost the merchant; the effect is small.

**What it would take.** Charge storage per stage with the existing transit timing.

**Test.** A test: a longer-staged haul costs more than a direct one by the storage charge.
