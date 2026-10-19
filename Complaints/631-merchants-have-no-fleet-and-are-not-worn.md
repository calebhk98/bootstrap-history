# Merchants have no fleet: dispatch is limited by cash, not by carriers

**Status:** open

Part of Complaint 552 (Carriage pays the poor without using their hours or any carriers).

Depends on 629 and 630.

**What is wrong.** A merchant's dispatch is cut by hours hired but not by carts, ships or animals it owns. Merchants are not worn.

**Evidence.** `inventory.wear_moves` wears cohort holdings only; `sim/economy/merchants.py`.

**Why it matters.** Trade can be paid for and still be physically impossible.

**What it would take.** A per-merchant fleet whose yearly capacity follows from its carriers and the route's days, bids or hire for more, wear booked from the service life, and an opening endowment of fleets.

**Test.** A test: a merchant without a fleet ships only what its hired capacity allows; wear reduces the fleet.
