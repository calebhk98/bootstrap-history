"""Complaint 87: `state` lists the shut, profitable concerns held shut by a missing specialist, with what is missing and
what to type to fix it, biggest earners first. The rows are built from a stub game (`done`, `operating`, the staffing
shortfall of each concern) and the lines rendered from rows."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.ui.proto.state_shut_staffing import render_shut_for_want_of_staff, shut_for_want_of_staff

NODES = {
    "glass": {"name": "Mirror works", "rev": 900.0, "up": 400.0},
    "loom": {"name": "Weaving shed", "rev": 700.0, "up": 100.0},
    "mill": {"name": "Flour mill", "rev": 500.0, "up": 450.0},
    "mint": {"name": "Mint", "rev": 300.0, "up": 400.0},     # loses money: not worth listing
    "forge": {"name": "Forge", "rev": 800.0, "up": 100.0},   # already running
    "school": {"name": "School", "rev": 800.0, "up": 100.0},  # not a concern
}


def stub_game(missing_by_node, operating=("forge",)):
    return SimpleNamespace(
        done=set(NODES), operating=set(operating), staffing_held_totals=lambda: {},
        is_venture=lambda node_id: node_id != "school",
        staffing_missing_to_open=lambda node_id, held: missing_by_node.get(node_id, {}))


game = stub_game({"glass": {"glassblower": 0.25}, "loom": {"scholars": 1.2, "craftsmen": 2.0}, "mill": {"miller": 1.0},
                  "mint": {"smith": 1.0}, "forge": {"smith": 1.0}, "school": {"scholars": 1.0}})
rows = shut_for_want_of_staff(game, NODES)
check("a shut, profitable concern short of a foreman is listed with the trade and the full-time equivalent missing",
      next(row for row in rows if row["id"] == "glass")["missing"] == {"glassblower": 0.25}, rows)
check("...and what to type to fix it", next(row for row in rows if row["id"] == "glass")["fix"] == "hire glassblower 1", rows)
check("scholars and craftsmen are hired as scholar and artisan, a fraction rounded up",
      next(row for row in rows if row["id"] == "loom")["fix"] == "hire scholar 2; hire artisan 2", rows)
check("a concern that loses money, one already running and a non-concern are not listed",
      {row["id"] for row in rows} == {"glass", "loom", "mill"}, [row["id"] for row in rows])
check("the biggest earners come first", [row["id"] for row in rows] == ["loom", "glass", "mill"], [row["id"] for row in rows])
check("what a concern would earn is revenue less running cost", rows[0]["would_earn_a_year"] == 600, rows[0])
check("once the specialist is no longer missing the concern is no longer listed",
      all(row["id"] != "glass" for row in shut_for_want_of_staff(stub_game({"loom": {"scholars": 1.0}}), NODES)))
check("with nothing short there is no list", shut_for_want_of_staff(stub_game({}), NODES) is None)

lines = render_shut_for_want_of_staff(rows)
# presentation: the state screen's wording and money format
check("the rendered state names the concern and what it lacks",
      len(lines) == 3 and "Mirror works" in "\n".join(lines) and "missing 0.25 glassblower" in "\n".join(lines), lines)
many = [dict(rows[0], id="c%d" % number) for number in range(8)]
check("the screen shows the first few and counts the rest",
      len(render_shut_for_want_of_staff(many)) == 6 and "3 more" in render_shut_for_want_of_staff(many)[-1])
