"""AI 서버 로직 단독 검증용 Streamlit MVP. 실행: streamlit run streamlit_app.py"""

import streamlit as st

from app.agents.graph import graph
from app.schemas import Requirements

PRESETS = {
    "게이밍": 1500000,
    "영상편집": 2500000,
    "개발": 1500000,
    "AI 학습": 3000000,
    "사무": 800000,
}
CONDITIONS = {"mixed": "신품 + 중고", "new": "신품만", "used": "중고만"}

st.set_page_config(page_title="PCForge MVP")
st.title("PCForge 에이전트 MVP")
st.caption("현재 결과는 목업 데이터입니다. 실제 상품과 가격이 아닙니다.")

purpose = st.selectbox("용도", list(PRESETS))
budget = st.number_input("예산 (원)", min_value=1, value=PRESETS[purpose], step=100000)
condition = st.radio("상태", list(CONDITIONS), format_func=CONDITIONS.get, horizontal=True)

if st.button("에이전트 실행", type="primary"):
    requirements = Requirements(purpose=purpose, budget_krw=int(budget), condition=condition)
    result = {}
    with st.status("에이전트 실행 중", expanded=True) as status:
        for update in graph.stream({"requirements": requirements, "steps": []}):
            for node_output in update.values():
                result.update({k: v for k, v in node_output.items() if k != "steps"})
                for step in node_output.get("steps", []):
                    st.write(step)
        status.update(label="완료", state="complete")

    st.info(result["explanation"])
    for warning in result["warnings"]:
        st.warning(warning)
    for rec in result["recommendations"]:
        with st.container(border=True):
            label = "중고" if rec.is_used else "신품"
            st.subheader(rec.product_name)
            st.write(f"{rec.price:,}원 · {rec.site} · {label} · 점수 {rec.score}")
            st.caption(rec.reason)
