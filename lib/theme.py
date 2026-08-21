"""디자인 토큰. README.md의 '디자인 토큰' 절과 1:1로 대응한다."""
from pathlib import Path

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo1.png"

COLOR = {
    "bg": "#F9F9F7",
    "card": "#FCFCFB",
    "sidebar": "#F1F1EE",
    "text": "#0B0B0B",
    "text_muted": "#52514E",
    "text_faint": "#898781",
    "border": "#E1E0D9",
    "brand": "#EB6834",
    "policy_before": "#86B6EF",
    "policy_after": "#1C5CAB",
    "up": "#D03B3B",
    "down": "#2A78D6",
    "sentiment_pos": "#1BAF7A",
    "sentiment_neu": "#C3C2B7",
    "sentiment_neg": "#E34948",
}

# 카테고리 구분용 (권역, 정부 등 순서가 바뀌면 안 되는 계열색). 6개 이상이면 '기타'로 묶는다.
SERIES = ["#2A78D6", "#EB6834", "#1BAF7A", "#EDA100", "#E87BA4"]
SERIES_OTHER = "#B9B8B1"

FONT_FAMILY = "'Noto Sans KR', sans-serif"

# 정책 시행일 마커 (README '계산 규칙' 절 고정값)
POLICY_MARKERS = {
    "6·27 (2025)": "2025-06-27",
    "9·7 (2025)": "2025-09-07",
    "10·15 (2025)": "2025-10-15",
    "8·13 (2026)": "2026-08-13",
}

REGION_GROUPS = {
    "강남3구": ["강남구", "서초구", "송파구"],
    "마용성": ["마포구", "용산구", "성동구"],
    "노도강": ["노원구", "도봉구", "강북구"],
    "금관구": ["금천구", "관악구", "구로구"],
}
REGION_COLOR = {
    "강남3구": SERIES[0],
    "마용성": SERIES[1],
    "노도강": SERIES[2],
    "금관구": SERIES[3],
    "기타": SERIES_OTHER,
}


def region_of(gu: str) -> str:
    for region, gus in REGION_GROUPS.items():
        if gu in gus:
            return region
    return "기타"


def plotly_layout(**overrides):
    """차트 전반에 공통으로 얹는 레이아웃. 그리드 흐리게, 범례 상단(README 체크리스트 고정 규칙)."""
    layout = dict(
        font=dict(family=FONT_FAMILY, color=COLOR["text"], size=13),
        paper_bgcolor=COLOR["card"],
        plot_bgcolor=COLOR["card"],
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(gridcolor=COLOR["border"], zeroline=False),
        yaxis=dict(gridcolor=COLOR["border"], zeroline=False),
        hoverlabel=dict(bgcolor=COLOR["card"], font_family=FONT_FAMILY),
    )
    layout.update(overrides)
    return layout


def inject_css():
    """색·배경은 .streamlit/config.toml [theme]이 담당한다(버전에 안 흔들리는 방식).
    여기서는 config.toml이 못 건드리는 부분(구글 폰트, 메트릭 카드 테두리)만 보정한다.
    """
    import streamlit as st

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
        /* [data-testid="stIconMaterial"]는 제외 — 사이드바 접기 화살표 같은 아이콘 글리프라서
           폭넓게 폰트를 덮어쓰면 아이콘 폰트가 깨져 "keyboard_double_arrow_left" 같은 원본 텍스트가 보인다 */
        html, body,
        [class*="css"]:not([data-testid="stIconMaterial"]),
        [class*="st-emotion"]:not([data-testid="stIconMaterial"]) {{ font-family: {FONT_FAMILY} !important; }}
        div[data-testid="stMetric"] {{
            background-color: {COLOR["card"]} !important;
            border: 1px solid {COLOR["border"]};
            border-radius: 10px;
            padding: 14px 16px;
        }}
        /* st.logo()는 최대 높이가 32px로 고정돼 있어 그림 로고가 뭉개진다.
           네비게이션 목록 위 자리는 유지하면서 실제 렌더링 크기만 키운다. */
        img[data-testid="stSidebarLogo"] {{
            max-height: none !important;
            height: 140px !important;
            width: auto !important;
        }}
        div[data-testid="stSidebarHeader"] {{
            height: auto !important;
            align-items: flex-start !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_logo():
    """사이드바 네비게이션 목록 '위' 자리에 팀 로고를 띱운다. 각 페이지 스크립트 최상단에서 호출한다.

    st.logo()만 그 위쪽 자리를 쓸 수 있는데 기본 최대 높이가 32px라 작게 나온다.
    inject_css()의 [data-testid="stLogo"] 규칙으로 높이 제한을 풀어서 크게 보이게 한다.
    """
    import streamlit as st

    if LOGO_PATH.exists():
        st.logo(str(LOGO_PATH), size="large")
