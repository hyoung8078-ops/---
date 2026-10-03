# ============================================================
# 건축기사 기출문제 Streamlit 앱
# 파일명: app.py
# ============================================================

import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="건축기사 기출문제",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_data():
    file_path = Path(__file__).parent / "건축기사_745문항_최종데이터_동일문제그룹확정.xlsx"
    df = pd.read_excel(file_path, sheet_name="최종데이터")
    df.columns = df.columns.str.strip()
    df["동일문제그룹ID"] = df["동일문제그룹ID"].fillna("단독")
    df["문제_짧은"] = df["문제내용"].astype(str).str[:70] + "..."
    df["선택라벨"] = (
        df["년도"].astype(str) + " " + 
        df["회차"].astype(str) + " | " + 
        df["문제_짧은"]
    )
    return df

df = load_data()

if "selected_qid" not in st.session_state:
    st.session_state.selected_qid = None
if "page" not in st.session_state:
    st.session_state.page = "기출 열람"

st.sidebar.title("🏗️ 건축기사 기출")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "메뉴 선택",
    ["기출 열람", "자주 나온 문제", "문제 풀이"],
    index=["기출 열람", "자주 나온 문제", "문제 풀이"].index(st.session_state.page)
)
st.session_state.page = page

st.sidebar.markdown("---")
st.sidebar.info(
    """
    **사용 방법**
    1. 기출 열람 또는 자주 나온 문제에서 문제 선택
    2. 문제 풀이 화면에서 답 입력 후 채점
    3. 동일문제 목록 확인
    """
)

# ============================================================
# 1. 기출 열람
# ============================================================
if page == "기출 열람":
    st.title("📖 기출 열람")
    st.caption("년도 · 회차 · 단원으로 문제를 찾아보세요.")

    col1, col2, col3 = st.columns(3)
    
    with col1:
        years = sorted(df["년도"].unique().tolist())
        selected_years = st.multiselect("년도", years, default=years[-3:] if len(years) >= 3 else years)
    
    with col2:
        rounds = sorted(df["회차"].unique().tolist())
        selected_rounds = st.multiselect("회차", rounds, default=rounds)
    
    with col3:
        units = sorted(df["단원"].unique().tolist())
        selected_units = st.multiselect("단원", units, default=units)
    
    keyword = st.text_input("🔍 문제 내용 검색 (키워드)", placeholder="예: BOT, 폭렬, 어스앵커")

    filtered = df.copy()
    if selected_years:
        filtered = filtered[filtered["년도"].isin(selected_years)]
    if selected_rounds:
        filtered = filtered[filtered["회차"].isin(selected_rounds)]
    if selected_units:
        filtered = filtered[filtered["단원"].isin(selected_units)]
    if keyword:
        filtered = filtered[filtered["문제내용"].str.contains(keyword, case=False, na=False)]

    st.markdown(f"**총 {len(filtered)}문항**")

    if len(filtered) == 0:
        st.warning("조건에 맞는 문제가 없습니다. 필터를 조정해 보세요.")
    else:
        options = filtered["선택라벨"].tolist()
        qids = filtered["문항 ID"].tolist()
        
        selected_label = st.selectbox(
            "문제를 선택하세요",
            options,
            index=None,
            placeholder="여기를 클릭해서 문제를 고르세요..."
        )
        
        if selected_label:
            idx = options.index(selected_label)
            st.session_state.selected_qid = qids[idx]
            st.success(f"선택됨 → 왼쪽 메뉴에서 **문제 풀이**로 이동하세요!")
            if st.button("➡️ 이 문제 풀기", type="primary"):
                st.session_state.page = "문제 풀이"
                st.rerun()

# ============================================================
# 2. 자주 나온 문제
# ============================================================
elif page == "자주 나온 문제":
    st.title("🔥 자주 나온 문제")
    st.caption("동일문제그룹 기준으로 출제빈도가 높은 문제만 모았습니다.")

    group_df = df[df["동일문제그룹ID"] != "단독"].copy()
    
    freq = (
        group_df.groupby("동일문제그룹ID")
        .agg(
            출제빈도=("문항 ID", "count"),
            대표문제=("문제내용", "first"),
            단원=("단원", "first")
        )
        .reset_index()
        .sort_values("출제빈도", ascending=False)
    )

    min_freq = st.slider("최소 출제빈도", min_value=2, max_value=5, value=2)
    freq = freq[freq["출제빈도"] >= min_freq]

    st.markdown(f"**출제빈도 {min_freq}회 이상 문제: {len(freq)}개 그룹**")

    for _, row in freq.iterrows():
        gid = row["동일문제그룹ID"]
        with st.expander(f"【{row['출제빈도']}회】 {row['대표문제'][:60]}...  ({row['단원']})"):
            same = df[df["동일문제그룹ID"] == gid][["년도", "회차", "문제내용", "문항 ID"]].sort_values(["년도", "회차"])
            
            st.write("**출제 이력**")
            for _, s in same.iterrows():
                st.markdown(f"- {s['년도']} {s['회차']}")
            
            st.write("**문제 선택**")
            for _, s in same.iterrows():
                label = f"{s['년도']} {s['회차']} | {str(s['문제내용'])[:50]}..."
                if st.button(label, key=f"freq_{s['문항 ID']}"):
                    st.session_state.selected_qid = s["문항 ID"]
                    st.session_state.page = "문제 풀이"
                    st.rerun()

# ============================================================
# 3. 문제 풀이
# ============================================================
elif page == "문제 풀이":
    st.title("✍️ 문제 풀이")

    if st.session_state.selected_qid is None:
        st.info("👈 왼쪽 메뉴에서 **기출 열람** 또는 **자주 나온 문제**로 가서 문제를 먼저 선택해 주세요.")
        st.stop()

    q = df[df["문항 ID"] == st.session_state.selected_qid].iloc[0]
    gid = q["동일문제그룹ID"]

    st.subheader(f"{q['년도']} {q['회차']}  ·  {q['단원']}")
    st.markdown("---")
    st.markdown(f"### {q['문제내용']}")
    st.markdown("---")

    user_answer = st.text_area(
        "답을 입력하세요",
        height=150,
        placeholder="여기에 답을 적어 주세요..."
    )

    if st.button("채점하기", type="primary"):
        correct = str(q["모범답안"]).strip()
        user = user_answer.strip()

        if user == "":
            st.warning("답을 입력해 주세요.")
        elif user == correct:
            st.success("✅ 정답입니다!")
            st.balloons()
        else:
            st.error("❌ 오답입니다.")
            st.markdown("**모범답안**")
            st.info(correct)

    st.markdown("---")
    st.subheader("📌 동일문제 정보")

    if gid == "단독":
        st.write("이 문제는 단독 출제되었습니다. (동일문제 없음)")
    else:
        same_group = df[df["동일문제그룹ID"] == gid].sort_values(["년도", "회차"])
        freq_count = len(same_group)

        st.markdown(f"**동일문제그룹: `{gid}`**  ·  총 **{freq_count}회** 출제")

        st.write("**출제 이력**")
        history = " → ".join(
            f"{row['년도']} {row['회차']}" for _, row in same_group.iterrows()
        )
        st.write(history)

        st.write("**동일문제 목록**")
        for _, row in same_group.iterrows():
            is_current = row["문항 ID"] == st.session_state.selected_qid
            prefix = "👉 " if is_current else ""
            label = f"{prefix}{row['년도']} {row['회차']} | {str(row['문제내용'])[:55]}..."
            
            if is_current:
                st.markdown(f"**{label}** (현재 문제)")
            else:
                if st.button(label, key=f"same_{row['문항 ID']}"):
                    st.session_state.selected_qid = row["문항 ID"]
                    st.rerun()

    st.markdown("---")
    st.subheader("🤖 AI 해설")
    st.info("AI 해설 준비 중입니다. (Qwen 연동 예정)\n\n나중에 이 자리에 자동 해설이 표시됩니다.")

    st.markdown("---")
    if st.button("← 다른 문제 선택하기"):
        st.session_state.selected_qid = None
        st.session_state.page = "기출 열람"
        st.rerun()