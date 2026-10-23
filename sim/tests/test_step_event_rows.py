"""event_rows: the step reply's events carry the year of the log row each came from, for every year the log holds."""
from sim.refusal import LogLine
from sim.ui.proto.refusal_cause import event_rows

from .harness import *  # noqa: F401,F403

QUICK_TOPIC = True

second_year_line = LogLine("interest_group_petitions", "a petition", group="merchants")
rows = event_rows([(1300, "a plain line"), (1301, second_year_line), (1301, "another")])
check("one row per log row, in log order", [row["message"] for row in rows] == ["a plain line", second_year_line, "another"], rows)
check("each row keeps the year of its own log row, so a second year is reported as that year",
      [row["year"] for row in rows] == [1300, 1301, 1301], rows)
check("a plain line carries no event kind", "event_kind" not in rows[0] and "facts" not in rows[0], rows[0])
check("a coded line carries its kind and facts", rows[1]["event_kind"] == "interest_group_petitions"
      and rows[1]["facts"] == {"group": "merchants"}, rows[1])
check("no log rows give no events", event_rows([]) == [])
