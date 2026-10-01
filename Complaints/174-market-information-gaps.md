# Market information: what a player cannot see, and how many commands it takes

**Status:** partly - `market` shows saturation per category, every priceable material and all wages; `why` names the goods category. Per-good sale price and demand, and `economy full` are not done

- Sale price of what concerns sell, and demand for it: no command.
- Material price: `materials` lists only materials already tracked (charcoal and firewood appeared only after I bought some); no `quote material`.
- Competition before building: none (`why` shows only the category, e.g. "textiles"); after building, only once saturated, via `money`/`economy`.
- Wages: `labour <trade>`, one call per trade (22 trades); `labour` shows wages only for trades employed; `population` has counts but no wages.
- `economy full` shows nothing beyond `economy` except materials above book price.

What it would take: a market screen (goods, price, demand, your share, saturation), all wages on one screen, `quote material`, and the saturation a new concern would face shown on `why`.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.

Merged from 147: to learn charcoal's market price I had to `buy material charcoal_kg 1` and watch capital change. Project-side material prices are a separate defect (151).

Also reported (England 1300 fog playtest): the tester found the market-saturation explanation in `money`/`ventures` excellent, but only after opening (a loom plus a rope walk sharing the textiles market; the loom earned about a third of its tree quote). They wanted the collision visible before buying: the market bucket, remaining demand and expected cannibalisation, and a pre-opening demand view by category. On the current branch `why` already prints "Sells into the textiles market, where N other concerns of yours also sell; it would earn about X% of its quoted figure there. 'market' shows every category." (checked with `why tex_horizontal_loom` at the start, where N is 0 and X is 98), so the first-order request appears done. Whether X accounts for saturation by concerns already open, and how it reads with several, was not tested; the tester's build may predate the line. Report: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`.

Also reported (Han China 100 AD fog playtest, tester item(s) 109, 150, 209, 215, 219; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): opening a small concern changed total revenue by millions (opening `four_stroke_engine` moved total revenue down 27 million before any step; restoring twelve public services lowered it 32.8 to 32.5 billion; `open junction_transistor` dropped it 4.9 billion and upkeep rose 45 million), with no line saying which existing concerns moved or why; three separate mechanisms (general absorption, category saturation, ramp reset) are shown on `money` without a prospective preview. Reproduces: untested (late game).
