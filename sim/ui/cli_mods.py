"""`mod-allow`, and the mod findings `validate` reports (code mods, command declarations)."""
from sim.engine.ui_port import MODDIR, code_report, get_ordered_mods
from sim.engine import ui_port

from .proto import mod_commands


def cmd_mod_allow(args):
    """Print the code files a mod would run, then record the player's consent to exactly those bytes."""
    manifest = next((found for found in get_ordered_mods(MODDIR) if found.id == args.mod_id), None)
    if manifest is None or not manifest.code:
        print("mod %s is not installed or ships no code." % args.mod_id)
        return 1
    digests = ui_port.allow_mod_code(MODDIR, args.mod_id)
    print("Allowed mod %s to run Python with your full permissions (files, network, credentials)." % args.mod_id)
    print("This is trust in the author, not a sandbox. A changed file needs consent again. Files and sha256:")
    for name, digest in sorted(digests.items()):
        print("  %s  %s" % (digest, name))
    return 0


def mod_findings():
    """Errors for validate: lines for each code-shipping mod are printed as warnings, bad command data is an error."""
    for line in code_report(MODDIR):
        print("WARNING: " + line)
    try:
        mod_commands.load_mod_commands()
    except ValueError as error:
        return ["mods: %s" % error]
    return []
