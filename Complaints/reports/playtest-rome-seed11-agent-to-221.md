# Playtest 3 log (rome_100ad seed 11, commit 8996204c)
Raw per-command timing in raw.log (json lines: cmd, sec, reply).
- 100: first command (state) on a fresh game took 399.6s (game build), over the 4-minute batch rule; save 20 MB at once. Resume afterwards ~7s.
- 100: `ventures`/open said "every other trade counts as craft"; hired 2 labourers (74/yr) but labourer kind="labour" gives 0 craft supervision. Wasted year of wages; fire does not refund the advance. (misleading)
- 100-102: lottery (fin_lottery) start 106; identity_cover; patron_local; scientific_method.
- 105: opened lottery; why/ventures forecast 48-80 denarii/yr. Actual venture revenue: 106:1811 (yr 107), 4142 (yr 108), ~6900/yr by 108. 100x forecast gap.
- 125: wasted ~3 idle years: path said nothing startable (needed scholars); only stuck/nearest_blockers said hire.
- 133-141: lottery revenue swings; lead_metallurgy opened; money 120k at 141, projects idle (needed machinists, 2-yr train; 900 founder hours each pair).
- 138-169: every hired scholar/smith/mason/trained machinist etc. left ("better offers", death, Antonine plague 169): employees {} at 173. Turned on auto_hire/open/train/commission/mine.
- 148: blast_furnace quote 824k: lime 16444/t, iron ore; `buy mine` for ore/lime costs ~0 capital (3 yrs). Complaint 576/519.
- 158-221: step intermittently returned "internal error ... InsufficientFunds: pool:credit ... (interest on deposit)"; from ~164 every step errored once, retry worked (driver retries). 62 errors total.
- 185-194: money 400k -> 21M: lead_chamber/sulfuric_retort acid sales ~4M/yr. Legit production, unrealistic scale (labourer wage 37/yr).
- 221: stopped by target. 114/163 goal steps, 27 concerns running, 44 shut. Seconds per year ~10.6 avg (raw.log).
