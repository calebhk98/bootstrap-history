# `population` shows identical placeholder counts and a code reference to players

**Status:** partly - player text no longer names source files; the per-trade counts are still placeholders

`population` at 130 AD: artisan, carpenter, furnaceman, labourer, miner, potter and smith all 54,693 in the country; mason, plumber and sailor all 109,385. The note tells the player to "see labour.py's TRADE_DENSITY for what is cited and what is a placeholder".

What it would take: per-trade estimates or a visible "placeholder" marker; no source-file references on player screens.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.

Also reported (England 1300 fog playtest): the tester saw the same screen telling them to "see labour.py's TRADE_DENSITY" (their build was older than the fix) and called it developer language leaking into the player UI. On the current branch (`population` at the start of England 1300) the source-file reference is gone, confirming the "partly" note. The trade table still gives no per-row marker for which counts are documented and which are placeholders (many trades share one identical figure in the country column), only a general sentence that "some are rough placeholders". Report: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`.
