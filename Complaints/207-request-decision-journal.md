# Request: a decision journal ("why did I build this forty years ago?")

**Status:** open

Requested three times by the tester (around 1320, 1335 and the 1350 retrospective): an in-game founder journal that auto-records starts, failures, openings and closures, staffing changes and major events, with optional player notes, plus a generated yearly retrospective. By 1335 there were enough overlapping projects that remembering why a five-year project was started was nontrivial. `log` and `recap` exist and were praised, but they record what happened, not what the player intended.

Checked: no complaint asks for intent notes (95 is a "why did this number change" inspector; 177, closed, is a `step N` summary). Not a defect.

What it would take: a `note <text>` command (stored in the save, attached to the year and optionally to a project id) and a `journal` view that merges notes with the existing log entries; `why <project>` could show the note made at start. Related: 95, 177.

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.
