"""Provided Streamlit view; run with python -m streamlit run from project root."""

import httpx
import streamlit as st

from Week4.day26.code.ui_client import DemoError, build_payload, submit_batch


def render_report(body: dict) -> None:
    """The server response is the trusted Day24 API contract, not arbitrary JSON."""
    summary = body["summary"]
    st.subheader("実行結果")
    st.caption(f"モード: {body['mode']}")
    st.write(f"タスク {summary['requests']} 件 / 成功 {summary['succeeded']} 件 / 失敗 {summary['failed']} 件")
    st.write(f"呼び出し {summary['attempts']} 回 / リトライ {summary['retries']} 回")
    for row in body["tasks"]:
        result = row["report"]["result"]
        st.subheader(f"タスク {row['task_id']}")
        if result["ok"]:
            st.success("呼び出し成功")
            st.text(result["raw"])
        else:
            st.warning(f"呼び出し失敗: {result['error']} / 上流ステータス: {result['status_code']}")
    with st.expander("レスポンス JSON"):
        st.json(body)


def main() -> None:
    st.set_page_config(page_title="日文需求 Demo", layout="centered")
    st.title("日文需求・実行デモ")
    st.info("模拟模式不会调用 AI；真实模式会发送输入到 Gemini API，可能产生费用。仅使用自制或脱敏内容。")
    with st.form("requirements", enter_to_submit=False):
        text_a = st.text_area("需求 A（必填）", value="一覧をCSVで出力する。", key="text_a")
        text_b = st.text_area("需求 B（可选）", value="", key="text_b")
        max_attempts = st.selectbox("最多调用次数", options=[1, 2, 3], index=2)
        mode = st.selectbox("运行模式", options=["simulated", "live"], index=0)
        submitted = st.form_submit_button("提交需求")
    if submitted:
        try:
            payload = build_payload(text_a, text_b, max_attempts)
            with st.spinner("実行中…"):
                with httpx.Client(base_url="http://127.0.0.1:8026", trust_env=False) as client:
                    body = submit_batch(client, payload, mode=mode)
            render_report(body)
        except DemoError as exc:
            st.error(str(exc))


if __name__ == "__main__":
    main()
