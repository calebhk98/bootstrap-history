# The formal credit ceiling looks reassuring when the sustainable debt is much smaller

**Status:** partly - `money` and the start forecast now show the sustainable debt and interest as a share of the recurring surplus (sim/tests/test_spending_previews.py); `state` does not, and the 'pay down by how much' refusal text (265) is separate

The project-start warning shows the single-project bill, total outstanding commitments, the expected credit draw and the formal credit ceiling (praised). But with arrears interest near 19 percent a year, a debt far below the ceiling can already exceed the recurring surplus: in 1333 to 1334 the tester had a ceiling of about 216 thousand pence, used about 1 percent of it, and was still about to have interest close to the surplus. They ask for a debt-service forecast that separates "formal credit ceiling" from "sustainable debt at the current recurring surplus" (interest cost against net recurring income, years to clear).

Checked: no existing complaint covers this (16 and 61, closed, were about the ceilings disagreeing, not about whether the ceiling is a safe level). Not replayed; the warning text is in the project-start path.

What it would take: one more line on the start warning and on `money`/`state` when in arrears: interest per year at the projected draw, as a share of recurring net, and the largest draw whose interest stays under a chosen share of surplus. Related: 95 (funding concepts), 16 and 61 (closed).

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.

Also reported (final playtests, C; `Complaints/reports/final-playtests-triage.md`): debt after smallpox is a trap with no exit: hiring is refused 'past half your line', the population is gone and concerns close for want of hands; the refusal should state how much to pay down (filed with the other refusal texts as 265).


What remains: the `state` screen carries no sustainable-debt line, and the threshold share is a labelled heuristic rather than derived from a lender model.
