from __future__ import annotations


def evaluate_report(report: dict, required_keywords: list[str]) -> dict:
    failed_checks: list[str] = []
    citations = report.get("citations", [])
    steps = report.get("steps", [])
    searchable_text = " ".join(
        [report.get("summary", ""), *report.get("possible_causes", []), *steps]
    ).lower()

    if not citations:
        failed_checks.append("缺少资料来源")
    if not steps:
        failed_checks.append("缺少排查步骤")
    for keyword in required_keywords:
        if keyword.lower() not in searchable_text:
            failed_checks.append(f"未覆盖关键排查词：{keyword}")

    return {"passed": not failed_checks, "failed_checks": failed_checks}
