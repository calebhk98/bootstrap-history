# `available` mixes a topic with paging and filter words unpredictably, and `all:true` ignores `limit`

**Status:** closed

The documented forms and the forms a player types do not compose. Help advertises
`available state:blocked tag:<topic>` and `offset`/`limit` paging, but:

- `available metallurgy limit 80` and `available metallurgy limit:80` both answer
  "nothing in 'metallurgy limit 80'": the option words are swallowed into the subject.
- `available subject metallurgy offset 3` answers "nothing in 'metallurgy offset 3'". The tester found
  that `available offset 30 subject metallurgy` (options first) pages correctly, so the grammar
  depends on word order and nothing says so.
- `available all:true limit:3` prints the whole startable list (hundreds of rows); `all` silently beats `limit`.
- Tester, not replayed: `available tag:optics` is refused ("optics is not a valid tag") although `available optics` is a
  valid subject; the subject list and the tag list are different vocabularies with no hint which is which.
- Tester, not replayed here: an offset past the end of a shrinking list says "nothing matches, try a shorter
  word" instead of "page past the end; N available".

Reproduces on the current branch (first three bullets):

    printf 'available metallurgy limit 80\navailable subject metallurgy offset 3\navailable all:true limit:3\nquit\n' | python3 sim/simulator.py play --civ han_china_100ad --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

What it would take: parse `offset`, `limit`, `sort`, `reverse`, `all` and `key:value` words out of the
line before treating the rest as the subject; let `limit` win over `all`; list the valid subjects and tags on a
refusal; say "past the end" when an offset is beyond the list; add one composed example to `help available`.
Related: 196 (natural topic words return nothing), 197 (`find` matches knowledge-file names), closed 74 and 146.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 27, 51, 52, 81, 83, 98, 147, 192, 216). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.
