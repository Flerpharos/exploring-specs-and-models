import math
import unittest
from typing import Protocol, runtime_checkable, Callable


@runtime_checkable
class UnitCliAdapter(Protocol):
    def run(self, command: str) -> str | None:
        ...


class UnitAwareSpecContractTests(unittest.TestCase):
    create_adapter: Callable[[], UnitCliAdapter] | None = None

    def setUp(self):
        if self.create_adapter is None:
            self.skipTest("Set create_adapter on subclass to run contract tests")
        self.cli = self.create_adapter()

    def ok(self, cmd: str):
        self.assertIn(self.cli.run(cmd) or "", ["", None], f"expected success: {cmd}")

    def err(self, cmd: str, expected: str):
        self.assertEqual(self.cli.run(cmd), expected, cmd)

    def value(self, cmd: str, magnitude: float, unit: str):
        line = self.cli.run(cmd)
        self.assertIsInstance(line, str, cmd)
        parts = line.rsplit(" ", 1)
        self.assertEqual(len(parts), 2, f"expected '<magnitude> <unit>' output for {cmd}: got {line!r}")
        got_mag, got_unit = parts
        self.assertEqual(got_unit, unit, cmd)
        self.assertTrue(math.isfinite(float(got_mag)), cmd)
        self.assertTrue(math.isclose(float(got_mag), magnitude, rel_tol=1e-12, abs_tol=1e-12), cmd)

    def test_identifier_and_command_syntax(self):
        self.err("unit:M", "Error: invalid unit name.")
        self.err("unit:m2", "Error: invalid unit name.")
        self.ok("unit:meters_per_second")
        self.err("set:x:1", "Error: invalid variable name.")
        self.err("set:X2:1", "Error: invalid variable name.")
        self.err("set:X", "Error: invalid command syntax.")
        self.err("evaluate:", "Error: invalid command syntax.")
        self.err("noop:1", "Error: unknown command.")

    def test_value_literals_and_unit_section(self):
        self.ok("unit:m"); self.ok("unit:s"); self.ok("unit:kg")
        self.value("evaluate:2+3", 5, "1")
        self.value("evaluate:2 m/s", 2, "m/s")
        self.value("evaluate:3 (m/s)^2", 3, "m^2/s^2")
        self.value("evaluate:4 kg*m/s^2", 4, "kg*m/s^2")
        self.value("evaluate:3 1/s", 3, "1/s")
        self.err("evaluate:2 m x", "Error: invalid formula.")

    def test_value_context_resolution(self):
        self.ok("unit:m")
        self.ok("set:X:3 m")
        self.value("evaluate:X", 3, "m")
        self.err("evaluate:Y", "Error: unknown variable Y.")
        self.value("evaluate:m", 1, "m")
        self.err("evaluate:s", "Error: unknown unit s.")

    def test_operator_precedence_and_errors(self):
        self.value("evaluate:-2^2", 4, "1")
        self.value("evaluate:-(2^2)", -4, "1")
        self.value("evaluate:2^3^2", 512, "1")
        self.value("evaluate:8/2*3", 12, "1")
        self.value("evaluate:]0", 1, "1")
        self.value("evaluate:[ ]1", 1, "1")
        self.err("evaluate:1/0", "Error: division by zero.")
        self.ok("unit:m")
        self.err("evaluate:2^1 m", "Error: exponent must be scalar.")
        self.err("evaluate:[2 m", "Error: log argument must be scalar.")
        self.err("evaluate:[0", "Error: log argument must be positive.")
        self.err("evaluate:]1 m", "Error: exp argument must be scalar.")

    def test_add_sub_unit_unification(self):
        self.ok("unit:m"); self.ok("unit:cm")
        self.ok("relate:cm:m:0.01 m")
        self.value("evaluate:1 m + 50 cm", 1.5, "m")
        self.value("evaluate:1 m - 50 cm", 0.5, "m")
        self.ok("unit:s")
        self.err("evaluate:1 m + 1 s", "Error: cannot convert s to m.")

    def test_relate_source_list_and_context_rules(self):
        self.ok("unit:m"); self.ok("unit:cm"); self.ok("unit:s")
        self.err("relate:cm:m,m:1 m", "Error: invalid unit list.")
        self.err("relate:cm:cm:1 cm", "Error: invalid unit list.")
        self.err("relate:cm:s:1 s", "Error: invalid unit list.")
        self.err("relate:cm:m:m+m", "Error: invalid formula.")
        self.err("relate:cm:m:[m", "Error: invalid formula.")
        self.err("relate:cm:m:1 s", "Error: unknown unit s.")
        self.ok("set:Z:7")
        self.err("relate:cm:m:Z", "Error: unknown unit Z.")

    def test_relate_replaces_existing(self):
        self.ok("unit:m"); self.ok("unit:cm")
        self.ok("relate:cm:m:0.01 m")
        self.ok("relate:cm:m:0.02 m")
        self.value("evaluate:1 m:cm", 50, "cm")

    def test_output_unit_context_and_precedence(self):
        self.ok("unit:m")
        self.err("evaluate:UNKNOWN_VAR:m/)", "Error: invalid output unit.")
        self.err("evaluate:1/0:m/)", "Error: invalid output unit.")
        self.err("evaluate:1 m:s", "Error: unknown unit s.")
        self.err("evaluate:1 m:", "Error: invalid command syntax.")
        self.err("evaluate:1 m:2 m", "Error: invalid output unit.")

    def test_conversion_and_shortest_path(self):
        self.ok("unit:m"); self.ok("unit:cm"); self.ok("unit:s")
        self.ok("relate:cm:m:0.01 m")
        self.value("evaluate:1 m:cm", 100, "cm")
        self.value("evaluate:1 cm:m", 0.01, "m")
        self.err("evaluate:1 m:s", "Error: cannot convert m to s.")
        self.ok("relate:m:cm:101 cm")
        self.value("evaluate:1 m:cm", 100, "cm")

    def test_conversion_applies_to_powers(self):
        self.ok("unit:m"); self.ok("unit:cm")
        self.ok("relate:cm:m:0.01 m")
        self.value("evaluate:1 m^2:cm^2", 10000, "cm^2")
        self.value("evaluate:1/cm:m^-1", 100, "m^-1")

    def test_relationship_invalid_factor(self):
        self.ok("unit:m")
        self.err("relate:cm:m:0 m", "Error: invalid relationship.")

    def test_evaluate_parsing_last_colon_split(self):
        self.ok("unit:m")
        self.value("evaluate:1 m:m", 1, "m")

    def test_failed_commands_do_not_mutate(self):
        self.ok("set:X:3")
        self.err("set:X:1/0", "Error: division by zero.")
        self.value("evaluate:X", 3, "1")


if __name__ == "__main__":
    unittest.main()
