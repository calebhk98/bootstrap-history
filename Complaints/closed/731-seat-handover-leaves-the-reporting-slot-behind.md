# A seat handover does not carry the reporting module's seat state

**Status:** closed - the handover carries every module's seat slot (`MOVED_FIELDS` includes `modules`, `sim/engine/seat_handover.py`), from the diffusion module's merge

`move_seat_fields` (`sim/engine/seat_handover.py`) copies the fields of a seat record by name; the module seat slots
(`seat.modules`, sim/assembly) were not in `MOVED_FIELDS`. When the log and the automation audit moved from the household into
the reporting module's `ReportingSeat` the leaver's log stopped passing to the replacement (the household moved, the log is no
longer on it). The resources move added `MOVED_MODULE_STATE = ("resources",)` for its own slot only, so the reporting
behaviour stays as it was. Fix: list `reporting` there (and have `holds_that_would_be_lost` say whether the replacement already has a
log worth keeping), or move every slot; decide with the reporting owner.
