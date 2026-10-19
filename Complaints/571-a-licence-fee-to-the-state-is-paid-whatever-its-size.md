# A licence fee to the state is paid whatever its size

**Status:** open

Found by an agent playtest (`Complaints/reports/playtest-rome-seed7-agent-100-years-log.md`, Rome, seed 7). The
`disclose` command with `"mode": "license"` and a government licensee credits the founder the fee asked, at once,
however large: a fee of a hundred thousand and later a million were paid in the opening decades, when the founder's
whole yearly income was a few denarii. Nothing compares the fee with what the knowledge is worth to the licensee or
with what its treasury holds.

Reproduce: in a fresh `rome_100ad` game, `{"cmd":"disclose","id":"scientific_method","mode":"license","licensee":"government:rome_100ad","fee":100000,"royalty":0.0}`
through `python3 sim/simulator.py agent --session FILE`, then `state`.

Why it matters: it is an unlimited money source, so any agent that finds it plays a different game; the release
criterion (an agent plays the whole game) is meaningless while it exists. CLAUDE.md "general actors": a licence is a
trade between two actors, and the buyer must decide and pay from its own purse.

What it would take: the licensee accepts or refuses by its own valuation (the value of the technique to it, as
governments already value techniques they copy, `sim/agents/government.py`) and pays through the ledger from its
treasury, which can refuse for lack of money; a refusal carries a `cause`. Test: a fee above the licensee's valuation
or its treasury is refused with a cause, and a fair fee moves money from its treasury to the founder.
