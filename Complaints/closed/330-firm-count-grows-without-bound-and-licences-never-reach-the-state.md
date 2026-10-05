# Firms multiply into the thousands over a Rome run (pre-existing), and the state's share of the founder's military work thins out

**Status:** closed - folded into 345

Two measurements from the disclosure work (`disclose`, `python3 sim/simulator.py agent`), taken with a driver that makes the same choice for every invention and prints a row per decade (firms, firm concerns, inventions the government holds, founder capital).

1. **Entry has no ceiling.** On the default choice the number of firms founded passes several thousand by the end of 150 years, and each runs a concern against the founder's goods market. Entry is limited only by `ENTREPRENEURIAL_CAPITAL_SHARE` against society output, which grows with the economy, so the count grows with it. Real markets have a finite number of operators per niche; here every proven concern keeps drawing entrants whenever the expected margin per operator stays positive. It also makes the yearly actor turn the dominant cost late in a run (see 181).
2. **The state's military adoption is a share of an ever larger set.** `state_military_diffusion` is the share of the founder's military nodes the government holds. The government copies at most a few inventions a year (`ATTENTION_SPAN`) and only those it values, so as the founder completes more military nodes the share falls even while the government keeps copying. Whether that is the right shape is a design question: the war relief caps (`STATE_MIL_RELIEF_CAP_OUTPUT`, `STATE_MIL_RELIEF_CAP_SACK`) multiply a share, where the military capability a state fields depends on which weapons it holds, not on what fraction of a tree it holds.

Fixing 2 means giving the relief a per-weapon basis (each held military node removes its own share of the harm, with diminishing returns as `hazard_relief` already does) instead of an average over everything the founder built.

Update (Complaint 331): incumbent firms now expand through normal rules before new ones are needed; Rome seed 1 reaches about 3100 firms at year 150 instead of about 7600. What still lets the count climb is in `345`.

Related: 341, 354.
