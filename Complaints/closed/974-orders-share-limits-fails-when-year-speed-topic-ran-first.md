# `orders_share_limits` failed in a full quick-tier run when two topics it borrows from had been loaded in a certain order

**Status:** closed - the need data is an argument of `random_world` and `year_world`, so no patch on a module attribute decides which baskets have limits

The topic patched `opening_tests.NEED_DATA` (a module attribute of `sim.tests.test_opening_demand_kernel`) and then called
`year_tests.year_world`, whose `random_world` reads `NEED_DATA` from the globals of the module object it was defined in.
`topic_import_guard.own_checks_only` drops a topic module that was loaded as another topic's helper and imports it afresh when
it runs as itself, so one process can hold two module objects of the same topic. When a worker ran `year_speed_cohort_orders`
(which holds the first copy of `random_world`), then `opening_demand_kernel` (the second copy replaces the first in
`sys.modules`), then `orders_share_limits`, the patch reached the second copy and the world was built from the first: no basket
had a share limit and `baskets with limits are exercised` failed (0 not greater than 20). The batches the runner makes depend on
recorded timings, so the order varied between runs. Reproduced with
`python3 sim/tests/__main__.py --worker year_speed_cohort_orders,opening_demand_kernel,orders_share_limits --worker-result <file> --worker-tag t --jobs 1`.

Fix: `random_world(rng, need_data=None)` and `year_world(rng, need_data=None)` take the data; the topic passes its limited data
and patches nothing. Regression test `NeedDataIsAnArgument` in `sim/tests/test_orders_share_limits.py` calls `year_world` with
the module attribute set to other data and asserts the limits come from the argument.
