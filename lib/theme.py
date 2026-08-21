"""
이 파일은 프로젝트 전반에 걸쳐 사용되는 감성 분석 시각화 및 UI 색상 등의 디자인 토큰과
Matplotlib 폰트 설정을 포함하는 공용 테마 모듈입니다.
"""

import matplotlib.pyplot as plt

# --- 디자인 토큰 색상 정보 ---
BG_PAGE = "#F9F9F7"
BG_CARD = "#FCFCFB"
BG_SIDEBAR = "#F1F1EE"

COLOR_TEXT_MAIN = "#0B0B0B"
COLOR_TEXT_SUB = "#52514E"
COLOR_TEXT_MUTED = "#898781"

COLOR_BORDER = "#E1E0D9"
COLOR_BRAND = "#EB6834"

# 정책 기간 비교 색상
COLOR_PRE_POLICY = "#86B6EF"
COLOR_POST_POLICY = "#1C5CAB"

# 변동률 색상
COLOR_UP = "#D03B3B"
COLOR_DOWN = "#2A78D6"

# 감정 극성 색상
COLOR_EMO_POSITIVE = "#1BAF7A"
COLOR_EMO_NEUTRAL = "#C3C2B7"
COLOR_EMO_NEGATIVE = "#E34948"

# 카테고리 시리즈 색상 (1~5)
COLOR_SERIES = ["#2A78D6", "#EB6834", "#1BAF7A", "#EDA100", "#E87BA4"]

def setup_matplotlib_font():
    """
    Matplotlib에서 한글이 정상적으로 출력될 수 있도록 맑은 고딕(Malgun Gothic) 및
    마이너스 깨짐 방지 설정을 적용합니다.
    """
    plt.rc('font', family='Malgun Gothic')
    plt.rc('axes', unicode_minus=False)
