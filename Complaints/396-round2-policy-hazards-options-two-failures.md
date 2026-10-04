# round2_policy_hazards_options: two checks fail

**Status:** partly

Two checks in `round2_policy_hazards_options` fail:

- "on a rich one it actually hires": the rich founder ends with no staff (staff 0.00, capital 2770693), so the auto-hire policy hires nobody.
- "england_1300: state full stays readable": the check on the full state screen for England fails (why was not read; the screen is the same size before and after the labour split).

Resolved: "on a rich one it actually hires". `staff_wage_reference()` averaged the opening wage schedule (then converted it again with `in_current_money`), while hiring is paid at the labour market's quote, which on the agent economy is far lower. The affordability scale in `staff_capacity()` was therefore tiny and auto_hire's headroom rounded to nobody. The reference now reads the market's unscarce annual wage in current money. Regression: `sim/tests/test_auto_hire_rich_founder.py` (`python3 -m sim.tests --only auto_hire_rich_founder`).

Still open: "england_1300: state full stays readable". The check wants the `state full` reply under 9000 bytes; England's is a little over (measure with the `state full` command on `england_1300` with fog on; the largest part is `knowledge_risk`). Not a labour matter: it belongs to the state screen in `sim/ui/proto/`.
