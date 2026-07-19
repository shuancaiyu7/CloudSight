import unittest

from services.documents import Chunk
from services.orchestrator import build_fallback_report, choose_scenario


class OrchestratorTests(unittest.TestCase):
    def test_choose_scenario_matches_port_unreachable_language(self):
        scenario_id = choose_scenario(
            "HTTPS 网站连接超时，443 端口没有监听，Nginx 可能未启动。"
        )

        self.assertEqual("web_port_unreachable", scenario_id)

    def test_fallback_report_keeps_evidence_when_model_is_unavailable(self):
        chunks = [
            Chunk(
                source="04_port.md",
                title="端口不可达排查手册",
                content="检查服务是否运行和端口是否监听。",
            )
        ]

        report = build_fallback_report(
            question="网站无法访问",
            evidence=chunks,
            tool_result={"name": "Web 服务端口不可达", "logs": "bind failed"},
        )

        self.assertTrue(report["human_handoff"])
        self.assertEqual("高", report["risk_level"])
        self.assertEqual("04_port.md", report["citations"][0]["source"])
        self.assertGreaterEqual(len(report["steps"]), 2)

    def test_fallback_report_includes_safe_solutions(self):
        report = build_fallback_report(
            question="网站无法访问",
            evidence=[],
            tool_result={"name": "Web 服务端口不可达", "logs": "bind failed"},
        )

        self.assertGreaterEqual(len(report["solutions"]), 2)
        self.assertTrue(any("人工" in item for item in report["solutions"]))


if __name__ == "__main__":
    unittest.main()
