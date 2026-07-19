import unittest

from services.tools import DiagnosticTools


class DiagnosticToolTests(unittest.TestCase):
    def setUp(self):
        self.tools = DiagnosticTools()

    def test_builtin_scenarios_cover_eight_fault_types(self):
        self.assertEqual(8, len(self.tools.list_scenarios()))

    def test_known_scenario_returns_only_safe_read_only_results(self):
        result = self.tools.inspect("web_port_unreachable")

        self.assertEqual("web_port_unreachable", result["scenario_id"])
        self.assertIn("service_status", result)
        self.assertIn("network_summary", result)
        self.assertNotIn("command", result)

    def test_unknown_scenario_returns_a_safe_error(self):
        result = self.tools.inspect("unknown-production-server")

        self.assertEqual("unknown_scenario", result["error"])
        self.assertIn("只支持预设演示场景", result["message"])


if __name__ == "__main__":
    unittest.main()
