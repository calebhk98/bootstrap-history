# The save listing's reputation, scholars and artisans come from sections that no longer hold them

**Status:** open

`sim/engine/settings.py` (`list_saves`, the row built from each save) fills `reputation`, `scholars` and `artisans` with
`household.get(...)`, the acting seat's `household` section. None of the three is a household field any more (standing is
the polity module's, the people are the workforce module's seat state), so each row says `None` for them and the save
browser (`sim/ui/cli_interactive_saveload.py`, the `rep ...` fragment) never shows a standing. The row's `done` list had the
same defect after the knowledge state moved; it now reads the knowledge module's slot (found while the projects record
was removed), and a test lists a save whose seat holds nodes.

Evidence: `grep -n 'household.get' sim/engine/settings.py`; the owners' saved fields are in the `modules` section of any
save (a `--session` run writes one).

Fix: read each from the module slot that holds it (the way `founder_alive` is read from `modules.seats`) and add a listing
test for each. Complaint 865 is the same defect for `goal_year`.
