from __future__ import annotations

import json
from pathlib import Path


SCENARIO_PATH = Path(__file__).resolve().parents[1] / "data" / "scenarios.json"


class DiagnosticTools:
    """只读取预设演示数据，绝不执行系统命令或访问真实云资源。"""

    def __init__(self) -> None:
        self._scenarios = {
            scenario["id"]: scenario
            for scenario in json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
        }

    def list_scenarios(self) -> list[dict]:
        return list(self._scenarios.values())

    def inspect(self, scenario_id: str) -> dict:
        scenario = self._scenarios.get(scenario_id)
        if scenario is None:
            return {
                "error": "unknown_scenario",
                "message": "只支持预设演示场景，不会连接或操作真实服务器。",
            }
        return {
            "scenario_id": scenario["id"],
            "name": scenario["name"],
            "service_status": scenario["service_status"],
            "network_summary": scenario["network_summary"],
            "configuration_summary": scenario["configuration_summary"],
            "logs": scenario["logs"],
        }
