# Every hired and trained hand leaves within a few decades

**Status:** closed (staff-retention): the unconditional yearly loss, most of it labelled better offers whatever the pay, is replaced by deaths at the working-age mortality rate plus better offers at the rate the labour market moves workers off a lower payer (none when paid the going wage); the policy `keep_pay_at_market` (on by default) keeps pay at the going wage, off freezes it at the last settled figure; `auto_hire replace` brings back the lost. Test: `python3 -m sim.tests --only complaint_585_staff_pay_retention`.

Found by an agent playtest (`Complaints/reports/playtest-rome-seed11-agent-to-221.md`, 138 to 173 AD): every hired or trained staff member left for better offers or died,
leaving the founder with no employees; wages for scholars rose many times over in the same years. 579 made the
departures visible; this is about whether they are right.

What it would take: trace why staff leave (the wage the founder pays against the market's offer each year, whether
the founder's wage follows the market), let the founder's pay policy keep staff at the going wage (auto-raise, as
`auto_hire` exists), and replace the dead from apprentices; a test that staff paid the going wage stay.
