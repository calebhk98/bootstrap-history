# Hiring a large crew of master craftsmen takes one year and no search

**Status:** open

Source: `Complaints/reports/playthrough-review-han-china-100-to-400ad.md`, item 3 (instantaneous hiring pools).

## What is wrong

With cash and household room, one `hire` command brings in a large number of master craftsmen at once, paid from the next year. The review's example is a metalworking crew of two dozen. In antiquity this meant agents across provinces and guild networks. Reach limits (`sim/engine/labour_capacity.py`) cap the pool but no rule makes a big hire slower, dearer or riskier than a small one. Reproduce: `quote hire <trade> <n>` with growing n in a game with cash; in a new Han game one smith and twenty smiths quote the same price per head (the refusal to hire twenty is only for want of cash).

## Why it matters

Instant hiring removes one of the main reasons a skilled workforce takes decades to assemble, so the baseline of how fast capability grows is optimistic. `Complaints/closed/34` fixed the opposite problem (scholar hours that could not be bought); this is the same root seen from the other side.

## What it would take

A recruitment rule that depends on how scarce the skill is in reach (`population` already prints per-trade reach, see 172), so a large hire draws wages up, takes years, or pulls trainees from other employers. It must come from labour-market state, not a number tuned to a result, and apply to any actor. Test: the same hire quoted for a common and a rare trade differs in time or price.

Owner decision (2026-10-02): delay; low priority.
