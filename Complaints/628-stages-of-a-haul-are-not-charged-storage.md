# Storage at stages of a haul is not charged

**Status:** open

Part of Complaint 552 (Carriage pays the poor without using their hours or any carriers).

**What is wrong.** Travel time, spoilage and interest are covered; storage at stages is not charged.

**Evidence.** `sim/economy/merchants_transit.py`; `test_merchant_travel_time.py`.

**Why it matters.** Goods held at stages cost the merchant; the effect is small.

**What it would take.** Charge storage per stage with the existing transit timing.

**Test.** A test: a longer-staged haul costs more than a direct one by the storage charge.
