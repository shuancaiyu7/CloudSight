from __future__ import annotations

from services.documents import Chunk, Document, chunk_documents, load_builtin_documents
from services.llm import LLMSettings, generate_report
from services.retrieval import SemanticRetriever
from services.tools import DiagnosticTools


SCENARIO_HINTS = {
    "web_port_unreachable": ("端口", "443", "https", "nginx", "连接超时", "无法访问"),
    "disk_full": ("磁盘", "空间", "no space", "写入", "500"),
    "dns_failure": ("dns", "解析", "域名", "resolv", "name resolution"),
    "cpu_spike": ("cpu", "负载", "响应变慢", "队列", "100%"),
    "nginx_config_error": ("nginx", "502", "配置", "重新加载", "发布后"),
    "app_service_crash": ("503", "重启", "内存", "应用服务", "异常退出"),
    "network_latency": ("延迟", "p99", "丢包", "跨可用区", "调用变慢"),
    "tls_certificate_expired": ("证书", "过期", "https", "ssl", "tls"),
}


def choose_scenario(question: str) -> str | None:
    text = question.lower()
    scored = [
        (sum(hint in text for hint in hints), scenario_id)
        for scenario_id, hints in SCENARIO_HINTS.items()
    ]
    score, scenario_id = max(scored, default=(0, ""))
    return scenario_id if score else None


def build_fallback_report(question: str, evidence: list[Chunk], tool_result: dict) -> dict:
    citations = [
        {"source": chunk.source, "excerpt": chunk.content[:140].replace("\n", " ")}
        for chunk in evidence[:3]
    ]
    finding = tool_result.get("name") or "未匹配预设模拟场景"
    return {
        "summary": f"初步判断：{finding}。模型接口未配置或暂不可用，以下建议仅基于检索资料与模拟数据。",
        "risk_level": "高"
        if tool_result.get("scenario_id") or tool_result.get("name")
        else "中",
        "possible_causes": [
            tool_result.get("logs", "资料不足，暂无法确认具体原因。"),
            tool_result.get("configuration_summary", "建议补充服务状态和网络信息。"),
        ],
        "steps": [
            "先保存当前日志和监控截图，避免直接重启或删除数据。",
            "对照资料确认服务状态、端口监听和相关配置。",
            "涉及生产配置修改、数据清理或服务重启时，交由人工复核。",
        ],
        "solutions": [
            "先依据资料和日志确认问题范围，保留现场信息并记录变更时间。",
            "在测试环境或维护窗口验证配置、服务状态和依赖关系，再制定恢复方案。",
            "涉及重启服务、修改生产配置或清理数据时，必须由人工确认后执行。",
        ],
        "human_handoff": True,
        "citations": citations,
        "question": question,
    }


def run_diagnosis(
    question: str,
    uploaded_documents: list[Document],
    settings: LLMSettings,
    forced_scenario: str | None = None,
) -> dict:
    documents = [*load_builtin_documents(), *uploaded_documents]
    retriever = SemanticRetriever(chunk_documents(documents))
    retrieved = retriever.search(question)
    evidence = [item.chunk for item in retrieved]
    scenario_id = forced_scenario or choose_scenario(question)
    tools = DiagnosticTools()
    tool_result = tools.inspect(scenario_id) if scenario_id else {
        "message": "未调用模拟工具：问题未匹配预设场景。"
    }
    evidence_payload = [
        {"source": chunk.source, "title": chunk.title, "content": chunk.content}
        for chunk in evidence
    ]
    trace = [
        f"资料库：内置 {len(load_builtin_documents())} 份，临时上传 {len(uploaded_documents)} 份。",
        f"检索方式：{retriever.mode}，命中 {len(evidence)} 个片段。",
        "模拟工具：" + (tool_result.get("name") or "未调用"),
    ]
    try:
        report = generate_report(settings, question, evidence_payload, tool_result)
        trace.append(f"模型：{settings.model} 已生成结构化报告。")
    except Exception as error:  # noqa: BLE001
        report = build_fallback_report(question, evidence, tool_result)
        trace.append(f"模型降级：{str(error)}")
    fallback_report = build_fallback_report(question, evidence, tool_result)
    report.setdefault("citations", fallback_report["citations"])
    report.setdefault("solutions", fallback_report["solutions"])
    report.setdefault("human_handoff", True)
    return {"report": report, "trace": trace, "scenario_id": scenario_id}
