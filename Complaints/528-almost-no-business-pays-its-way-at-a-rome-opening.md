# Almost no business pays its way at a Rome opening

**Status:** open

After 507 Stage 3 (actors pay the economy's prices), a scan of every node at a default Rome opening found one
concern whose takings exceed its wages and rent (`fin_lottery`); coking, which paid before, now takes in about half
its costs because carbon is bought at the economy's price (found fixing `firm_entry_default_game`; no committed
command lists the scan). The state's revenue also fell by about a third. With almost nothing profitable, firms do not
enter, the founder has few ways to earn, and the opening is a stagnant economy.

Likely causes, to measure: input prices far above making cost (519: sited ores and metals open at many times their
cost), the opening's low wages and income (526), and node takings that still come from node fields rather than the
plant's own output at market prices (510/514). What it would take: a committed command (or `opening-checks` row)
that counts the concerns whose takings at opening prices exceed their running cost, per civilisation, and a
relationship check that a plausible share of the technologies a society already holds pay their way at its opening.
