import unittest

from services.evaluator import evaluate_report


class EvaluatorTests(unittest.TestCase):
    def test_evaluation_accepts_a_safe_report_with_citations(self):
        report = {
            "summary": "Web 服务端口不可达。",
            "risk_level": "高",
            "possible_causes": ["Nginx 未运行"],
            "steps": ["确认 Nginx 服务状态", "确认 443 端口监听"],
            "human_handoff": True,
            "citations": [{"source": "端口不可达.md", "excerpt": "检查服务状态"}],
        }

        result = evaluate_report(report, required_keywords=["Nginx", "端口"])

        self.assertTrue(result["passed"])
        self.assertEqual([], result["failed_checks"])

    def test_evaluation_rejects_a_report_without_sources(self):
        result = evaluate_report(
            {"summary": "无法确定", "steps": [], "citations": []},
            required_keywords=[],
        )

        self.assertFalse(result["passed"])
        self.assertIn("缺少资料来源", result["failed_checks"])


if __name__ == "__main__":
    unittest.main()
