# `population` shows identical placeholder counts and a code reference to players

**Status:** closed - each placeholder trade density now shows an asterisk marker with a legend explaining it

`population` at 130 AD: artisan, carpenter, furnaceman, labourer, miner, potter and smith all 54,693 in the country; mason, plumber and sailor all 109,385. The note tells the player to "see labour.py's TRADE_DENSITY for what is cited and what is a placeholder".

What it would take: per-trade estimates or a visible "placeholder" marker; no source-file references on player screens.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.

Also reported (England 1300 fog playtest): the tester saw the same screen telling them to "see labour.py's TRADE_DENSITY" (their build was older than the fix) and called it developer language leaking into the player UI. On the current branch (`population` at the start of England 1300) the source-file reference is gone, confirming the "partly" note. The trade table still gives no per-row marker for which counts are documented and which are placeholders (many trades share one identical figure in the country column), only a general sentence that "some are rough placeholders". Report: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`.

Also reported (Han China 100 AD fog playtest, tester item(s) 124, 178; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): `population` for a country of tens or hundreds of millions listed three to six of each advanced trade (chemist, electrician, engineer, machinist, optician), all within reach, and "employed" shares that let the tester's own hires dominate; the screen labels them estimates and placeholders but prints them as counts. Reproduces: yes (`population` at the start prints `engraver 5,800 ... 2.9 in reach`, `machinist 0`).
