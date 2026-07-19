from __future__ import annotations

from collections.abc import Iterable

import streamlit as st

from services.documents import Document, chunk_documents, load_builtin_documents, parse_uploaded_file
from services.evaluator import evaluate_report
from services.llm import load_settings
from services.orchestrator import build_fallback_report, run_diagnosis
from services.retrieval import SemanticRetriever
from services.settings import safe_secret_mapping
from services.tools import DiagnosticTools


st.set_page_config(page_title="CloudSight", page_icon="CS", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background: #F6F8FB; color: #15212D; }
    [data-testid="stSidebar"] { background: #15212D; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: #F6F8FB; }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] * { color: #C9D4E2; }
    [data-testid="stSidebar"] [data-baseweb="select"] > div,
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        background: #FFFFFF; border: 1px solid #A9B9CA;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] *,
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * { color: #15212D !important; }
    [data-testid="stSidebar"] button[kind="secondary"] {
        background: #FFFFFF; border: 1px solid #A9B9CA;
    }
    [data-testid="stSidebar"] button[kind="secondary"] * { color: #15212D !important; }
    .block-container { max-width: 1320px; padding-top: 1.25rem; }
    .title-row { display:flex; align-items:center; gap:12px; margin-bottom:14px; }
    .brand-mark { width:34px; height:34px; background:#165DFF; color:#fff; display:flex; align-items:center; justify-content:center; font-weight:700; border-radius:6px; }
    .title-row h1 { font-size:1.4rem; margin:0; letter-spacing:0; }
    .status-dot { color:#008A73; font-size:.85rem; margin-left:auto; }
    [data-testid="stMetric"] { background:#FFFFFF; border:1px solid #DCE3EC; border-radius:6px; padding:12px; }
    .report-label { color:#4B5B6B; font-size:.82rem; font-weight:600; margin:16px 0 5px; }
    .citation { border-left:3px solid #00A88F; padding:8px 10px; background:#F0FBF8; margin:7px 0; }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialize_state() -> None:
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("uploaded_documents", [])
    st.session_state.setdefault("upload_signature", "")
    st.session_state.setdefault("pending_question", "")


def load_uploads(files: Iterable) -> list[Document]:
    signature = "|".join(f"{file.name}:{file.size}" for file in files)
    if signature == st.session_state.upload_signature:
        return st.session_state.uploaded_documents
    documents: list[Document] = []
    for file in files:
        documents.append(parse_uploaded_file(file.name, file.getvalue()))
    st.session_state.upload_signature = signature
    st.session_state.uploaded_documents = documents
    return documents


def render_report(report: dict, trace: list[str]) -> None:
    risk = report.get("risk_level", "中")
    risk_label = {"高": "需要人工复核", "中": "建议持续观察", "低": "影响较低"}.get(risk, "建议人工复核")
    metrics = st.columns(3)
    metrics[0].metric("风险等级", risk)
    metrics[1].metric("人工处理", "需要" if report.get("human_handoff") else "暂不需要")
    metrics[2].metric("结论", risk_label)
    st.markdown(report.get("summary", "未返回诊断摘要。"))

    st.markdown('<p class="report-label">可能原因</p>', unsafe_allow_html=True)
    for cause in report.get("possible_causes", []):
        st.write(f"- {cause}")
    st.markdown('<p class="report-label">建议排查步骤</p>', unsafe_allow_html=True)
    for index, step in enumerate(report.get("steps", []), start=1):
        st.write(f"{index}. {step}")
    st.markdown('<p class="report-label">建议解决方案</p>', unsafe_allow_html=True)
    for index, solution in enumerate(report.get("solutions", []), start=1):
        st.write(f"{index}. {solution}")
    st.markdown('<p class="report-label">资料来源</p>', unsafe_allow_html=True)
    for citation in report.get("citations", []):
        source = citation.get("source", "未知资料")
        excerpt = citation.get("excerpt", "")
        with st.expander(f"资料来源：{source}"):
            st.caption(excerpt)
    with st.expander("执行轨迹"):
        for item in trace:
            st.write(f"- {item}")


def run_evaluation() -> list[dict]:
    builtin_documents = load_builtin_documents()
    retriever = SemanticRetriever(
        [
            chunk
            for document in builtin_documents
            for chunk in chunk_documents([document])
        ]
    )
    tools = DiagnosticTools()
    results = []
    for scenario in tools.list_scenarios():
        evidence = [result.chunk for result in retriever.search(scenario["question"], limit=3)]
        report = build_fallback_report(scenario["question"], evidence, tools.inspect(scenario["id"]))
        score = evaluate_report(report, required_keywords=[])
        results.append({"case": scenario["name"], **score})
    return results


initialize_state()
tools = DiagnosticTools()
scenarios = tools.list_scenarios()

with st.sidebar:
    st.markdown("### 资料与场景")
    st.caption(f"内置手册 {len(load_builtin_documents())} 份")
    uploaded_files = st.file_uploader(
        "上传资料", type=["pdf", "txt", "md"], accept_multiple_files=True
    )
    try:
        uploaded_documents = load_uploads(uploaded_files)
        st.caption(f"本次会话资料 {len(uploaded_documents)} 份")
    except ValueError as error:
        uploaded_documents = []
        st.error(str(error))
    selected_name = st.selectbox("预设故障案例", ["不使用预设案例", *[item["name"] for item in scenarios]])
    selected_scenario = next(
        (item for item in scenarios if item["name"] == selected_name), None
    )
    if selected_scenario and st.button("载入案例", use_container_width=True):
        st.session_state.pending_question = selected_scenario["question"]
        st.rerun()
    st.divider()
    st.caption("所有诊断工具仅查询预设演示数据。")

st.markdown(
    '<div class="title-row"><div class="brand-mark">CS</div><h1>CloudSight 故障初检</h1><span class="status-dot">演示环境 · 只读</span></div>',
    unsafe_allow_html=True,
)

chat_tab, evaluation_tab = st.tabs(["故障对话", "诊断评测"])

with chat_tab:
    if not st.session_state.history:
        with st.chat_message("assistant"):
            st.write("输入故障现象或粘贴日志，系统将检索资料并生成初检报告。")
    for message in st.session_state.history:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and "report" in message:
                render_report(message["report"], message["trace"])
            else:
                st.write(message["content"])

    question = st.chat_input("例如：HTTPS 网站连接超时，443 端口未监听")
    if st.session_state.pending_question:
        question = st.session_state.pending_question
        st.session_state.pending_question = ""
    if question:
        st.session_state.history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            with st.spinner("正在检索资料并进行安全初检..."):
                forced_scenario = selected_scenario["id"] if selected_scenario else None
                result = run_diagnosis(
                    question,
                    uploaded_documents,
                    load_settings(safe_secret_mapping(lambda: st.secrets)),
                    forced_scenario,
                )
            render_report(result["report"], result["trace"])
        st.session_state.history.append(
            {"role": "assistant", "report": result["report"], "trace": result["trace"]}
        )

with evaluation_tab:
    st.write("预设案例会检查资料来源和安全排查步骤是否完整。")
    if st.button("运行基础评测", type="primary"):
        with st.spinner("正在运行 8 个预设案例..."):
            results = run_evaluation()
        passed = sum(item["passed"] for item in results)
        st.metric("通过案例", f"{passed} / {len(results)}")
        for item in results:
            label = "通过" if item["passed"] else "待改进"
            st.write(f"**{item['case']}** · {label}")
            for detail in item["failed_checks"]:
                st.caption(detail)
