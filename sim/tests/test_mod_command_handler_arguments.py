"""A mod's command handler is called `(access, cmd, ended)`: the game's node table is read through the access, not handed in."""
import unittest
from types import SimpleNamespace

from sim.engine.mod_code import ModCodeApi

QUICK_TOPIC = True


class ModCommandHandlerArguments(unittest.TestCase):
    def test_handler_gets_access_command_and_ended_only(self):
        api = ModCodeApi("probe_mod")
        calls = []
        api.command("look", group="game", summary="s", usage=["look"], description="d")(
            lambda access, cmd, ended: calls.append((access, cmd, ended)) or {"ok": True})
        declaration = api.operations.provided["interface_commands"][0]()[0]
        game = SimpleNamespace(assembly=SimpleNamespace(mod_access={"probe_mod": "the access"}))
        reply = declaration.handler(game, {"unused": "node table"}, {"cmd": "look"}, None)
        self.assertEqual(reply, {"ok": True})
        self.assertEqual(calls, [("the access", {"cmd": "look"}, None)])


if __name__ == "__main__":
    unittest.main()
