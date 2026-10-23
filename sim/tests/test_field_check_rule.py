"""Complaint 574: a field no command reads is refused with `unknown_field`, and each command takes the fields its own handler
reads. The rule is called on commands built in the test; no game."""

QUICK_TOPIC = True

import unittest

from sim.ui.proto import command_registry, field_check


def cause_of_refusal(refusal):
    return getattr(refusal["error"], "cause", None)


class UnknownFieldRefusalTests(unittest.TestCase):
    def test_policy_given_a_switch_name_instead_of_set_is_refused_naming_the_field_and_the_accepted_ones(self):
        refusal = field_check.unknown_field_refusal({"cmd": "policy", "auto_hire": "on"})
        self.assertIs(refusal["ok"], False)
        self.assertEqual(cause_of_refusal(refusal), "unknown_field")
        self.assertEqual(refusal["field"], "auto_hire")
        self.assertIn("set", refusal["accepted_fields"])

    def test_help_given_command_is_refused_naming_topic_as_the_accepted_field(self):
        refusal = field_check.unknown_field_refusal({"cmd": "help", "command": "sell"})
        self.assertEqual(cause_of_refusal(refusal), "unknown_field")
        self.assertEqual(refusal["field"], "command")
        self.assertIn("topic", refusal["accepted_fields"])

    def test_a_field_another_command_reads_is_refused_naming_the_fields_policy_takes(self):
        refusal = field_check.unknown_field_refusal({"cmd": "policy", "id": "x"})
        self.assertEqual(cause_of_refusal(refusal), "unknown_field")
        self.assertEqual(refusal["field"], "id")
        self.assertEqual(refusal["accepted_fields"], ["set"])

    def test_a_command_that_reads_no_field_refuses_any_other_commands_field(self):
        refusal = field_check.unknown_field_refusal({"cmd": "state", "id": "x"})
        self.assertEqual(refusal["field"], "id")

    def test_declared_fields_are_not_refused(self):
        self.assertIsNone(field_check.unknown_field_refusal({"cmd": "help", "topic": "sell"}))
        self.assertIsNone(field_check.unknown_field_refusal({"cmd": "policy", "set": {}}))
        self.assertIsNone(field_check.unknown_field_refusal({"cmd": "why", "id": "x"}))

    def test_the_shared_output_flag_is_not_refused(self):
        self.assertIsNone(field_check.unknown_field_refusal({"cmd": "state", "compact": True}))

    def test_the_accepted_fields_of_a_command_come_from_its_handler(self):
        self.assertEqual(field_check.accepted_fields(command_registry.resolve("policy")) - field_check.common_fields(), {"set"})
        self.assertIn("id", field_check.accepted_fields(command_registry.resolve("why")))
