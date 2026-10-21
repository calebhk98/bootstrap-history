"""keep_staffed: complaint 126 (name the concerns that must stay staffed through attrition). Complaint 640: the
typed command is parsed here; the yearly hire, the closure rule and the save are in test_keep_staffed_scenario."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.ui.proto.typed import parse_typed

check("'keep <id> staffed' sets the flag", parse_typed("keep mirror_amalgam staffed") == (
    {"cmd": "keep", "id": "mirror_amalgam", "staffed": True}, None), parse_typed("keep mirror_amalgam staffed"))
check("'keep <id>' alone also sets the flag", parse_typed("keep mirror_amalgam")[0]["staffed"] is True)
check("'keep <id> off' clears the flag", parse_typed("keep mirror_amalgam off") == (
    {"cmd": "keep", "id": "mirror_amalgam", "staffed": False}, None), parse_typed("keep mirror_amalgam off"))
check("bare 'keep' lists what is flagged", parse_typed("keep") == ({"cmd": "keep"}, None), parse_typed("keep"))
