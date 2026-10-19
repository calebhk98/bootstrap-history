# The lending pool grows to an absurd balance

**Status:** open

Found closing 582. In the agent playtest (`Complaints/reports/playtest-rome-seed11-agent-to-221.md`, Rome, seed 11, around 160 to 221 AD) the pooled lender
`pool:credit` (Complaint 580) held a balance many orders of magnitude above the economy's money stock. Something
keeps putting money into the pool without taking it out: savers' top-ups that are never repaid, deposits counted
twice, or interest credited to the pool and also to depositors.

Measure: load the playtest save at 221 AD and read the book's balance for `pool:credit` against the total money held
by households and firms (no committed command prints both).

What it would take: trace every edge into and out of the pool over a few years, find the one that does not balance,
fix it, and add a test that the pool's balance stays within the deposits it holds plus the year's interest, over
several stepped years.
