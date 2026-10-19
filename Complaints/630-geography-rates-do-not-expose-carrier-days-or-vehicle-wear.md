# Geography's `Rate` does not expose carrier-days, animals per carrier or vehicle wear

**Status:** open

Part of Complaint 552 (Carriage pays the poor without using their hours or any carriers).

Depends on 629.

**What is wrong.** Carrier needs are not threaded through the crew hours.

**Evidence.** `sim/geography/` (`Rate`), `carriage_crew`.

**Why it matters.** A fleet cannot be sized without them.

**What it would take.** Expose carrier-days, animals per carrier and vehicle wear on `Rate` and thread them through `carriage_crew`.

**Test.** A test: a route's rate reports carrier-days and wear per tonne-km.
