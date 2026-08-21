"""4. 뉴스·여론 분석 — 정책 보도의 감정 분포와 기사 원문 탐색."""
import plotly.express as px
import streamlit as st

from lib import load, sentiment, theme

st.set_page_config(page_title="뉴스·여론 분석 · 맛동산", page_icon="🏠", layout="wide")
theme.inject_css()
theme.render_logo()

if load.data_files_missing():
    st.error("data/ 폴더에 필요한 CSV가 없습니다. 메인 화면에서 안내를 확인해 주세요.")
    st.stop()

st.title("뉴스 · 여론 분석")

news_all = load.load_news("category")
total_collected = len(news_all)

st.caption(f"정책 보도 {total_collected:,}건의 감정 분포와 기사 원문 탐색")

CATEGORY_OPTIONS = sorted(news_all["카테고리"].unique())
GOV_OPTIONS = ["박근혜", "문재인", "윤석열", "이재명"]
POLICY_OPTIONS = ["6·27", "9·7", "10·15", "8·13"]
PHASE_OPTIONS = ["시행 전", "시행일", "초기 반응", "체감 반응"]

with st.sidebar:
    target_policy = st.radio("대상 정책", ["전체"] + POLICY_OPTIONS, horizontal=False)
    phase_filter = st.selectbox("정책 시점", ["전체 시점"] + PHASE_OPTIONS)
    category_filter = st.multiselect("정책 카테고리", CATEGORY_OPTIONS)
    gov_filter = st.multiselect("표시 정부", GOV_OPTIONS, default=GOV_OPTIONS)
    min_prob = st.slider("확률 필터", 0.5, 0.99, 0.9, step=0.01)
    st.caption(f"확률 {min_prob:.2f} 이상만 표시")

news = news_all.copy()
if target_policy != "전체" and "정책" in news.columns:
    news = news[news["정책"] == target_policy]
if phase_filter != "전체 시점":
    news = news[news["시기"] == phase_filter]
if category_filter:
    news = news[news["카테고리"].isin(category_filter)]
if gov_filter:
    news = news[news["정부"].isin(gov_filter)]
news = news[news["수치"] >= min_prob]

k1, k2 = st.columns(2)
k1.metric("수집 기사", f"{total_collected:,}건", "부동산 정책 보도 · 4개 카테고리 (임시 데이터)")
k2.metric("감정 분석 완료", f"{len(news_all):,}건", "4개 정부 비교 세트")

st.divider()

# ---------------------------------------------------------------- 기사 수집 구성
st.subheader("기사 수집 구성")
st.caption("네이버 뉴스 · 정책 카테고리 × 시점 교차 분류")

cat_counts = news_all["카테고리"].value_counts().reindex(CATEGORY_OPTIONS).fillna(0)
for cat, count in cat_counts.items():
    ratio = count / len(news_all)
    st.markdown(f"**{cat}** &nbsp; {int(count)}건 · {ratio:.1%}")
    st.progress(ratio)

post_ratio = news_all[news_all["시기"] != "체감 반응"].shape[0] / len(news_all)
st.caption(
    f"보도량은 발표 후 · 시행 전 구간에 {post_ratio:.0%}({news_all[news_all['시기'] != '체감 반응'].shape[0]}건) 몰립니다. "
    f"시행 후 기사는 {news_all[news_all['시기'] == '체감 반응'].shape[0]}건뿐이라 \"시행 후 여론\"을 논할 때는 표본이 얇다는 점을 함께 밝혀야 한다."
)

st.divider()

# ---------------------------------------------------------------- 시점별 감정 분포
col_left, col_right = st.columns([3, 2])
with col_left:
    st.subheader("시점별 감정 분포")
    st.caption("기사 수 · 현재 필터 기준")
    tab = news.groupby(["시기", "감정"]).size().unstack(fill_value=0).reindex(PHASE_OPTIONS).reindex(columns=sentiment.EMOTIONS_7, fill_value=0)
    st.dataframe(tab, use_container_width=True)

with col_right:
    st.subheader("세부 감정 분포")
    emo_counts = news["감정"].value_counts().reindex(sentiment.EMOTIONS_7).fillna(0)
    fig_emo = px.bar(x=emo_counts.index, y=emo_counts.values, color=emo_counts.index, color_discrete_sequence=theme.SERIES + [theme.SERIES_OTHER])
    fig_emo.update_layout(**theme.plotly_layout(height=340, showlegend=False, xaxis_title=None, yaxis_title="건수"))
    st.plotly_chart(fig_emo, use_container_width=True)

st.divider()

# ---------------------------------------------------------------- 감정 극성 교차 (정부 x 카테고리)
st.subheader("정부별 감정 극성")
ratio = sentiment.group_ratio(news, by=["정부"])
fig_gov = px.bar(
    ratio, x="정부", y="비율", color="감정그룹", barmode="stack",
    category_orders={"정부": GOV_OPTIONS, "감정그룹": sentiment.GROUP_ORDER},
    color_discrete_map={"긍정": theme.COLOR["sentiment_pos"], "중립": theme.COLOR["sentiment_neu"], "부정": theme.COLOR["sentiment_neg"]},
)
fig_gov.update_layout(**theme.plotly_layout(height=340))
fig_gov.update_yaxes(tickformat=".0%")
st.plotly_chart(fig_gov, use_container_width=True)

st.divider()

# ---------------------------------------------------------------- 감정별 기사 탐색
st.subheader("감정별 기사 탐색")
st.caption("막대 클릭 대신 감정 탭 + 표로 확인합니다.")

emo = st.segmented_control("감정", ["전체"] + sentiment.EMOTIONS_7, default="전체")
order = st.radio("정렬", ["확률 높은 순", "최신순"], horizontal=True, label_visibility="collapsed")

view = news if emo in (None, "전체") else news[news["감정"] == emo]
view = view.sort_values("수치", ascending=False) if order == "확률 높은 순" else view.sort_values("날짜", ascending=False)

if st.button("랜덤 5건 뽑기"):
    view = view.sample(min(5, len(view))) if len(view) else view

display_cols = ["감정", "기사제목", "시기", "날짜", "수치", "url"]
st.dataframe(
    view[display_cols] if len(view) else view.reindex(columns=display_cols),
    column_config={
        "url": st.column_config.LinkColumn("원문", display_text="원문 ↗"),
        "수치": st.column_config.NumberColumn("확률", format="%.3f"),
        "날짜": st.column_config.DateColumn("날짜", format="YYYY-MM-DD"),
    },
    hide_index=True, use_container_width=True,
)
st.caption(f"조건에 맞는 기사 {len(view):,}건")

st.divider()
st.subheader("댓글 감정 분석")
st.info("예정 — 댓글 수집·분석 파이프라인이 확정되면 이 절에 추가합니다.")

st.caption("데이터: news_titles_category.csv (현재는 화면 검증용 임시 데이터, 컬럼 구성은 확정 전).")
