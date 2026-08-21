"""
이 파일은 뉴스 감성 분석 데이터의 통계 연산 및 매핑을 담당하는 모듈입니다.
7종 세부 감정을 긍정/중립/부정의 3대 극성 그룹으로 매핑하고,
부동산 대책 시행 전/후 변화 지표(Delta) 및 특정 날짜의 주요 뉴스를 연산합니다.
"""

import pandas as pd

def map_emotion_7_to_3(emotion_label):
    """
    dlckdfuf141/korean-emotion-kluebert-v2 모델의 7종 감정 결과를 3대 극성으로 매핑합니다.
    - 긍정: 행복
    - 중립: 중립, 놀람 (놀람은 기획 상 중립으로 병합)
    - 부정: 혐오, 분노, 슬픔, 공포
    """
    if not isinstance(emotion_label, str):
        return '중립'
        
    emotion_label = emotion_label.strip()
    if emotion_label == '행복':
        return '긍정'
    elif emotion_label in ['중립', '놀람']:
        return '중립'
    elif emotion_label in ['혐오', '분노', '슬픔', '공포']:
        return '부정'
    else:
        return '중립'

def calculate_metrics(df, effective_date="2025-06-28"):
    """
    부동산 대책 시행일(effective_date)을 기준으로 시행 전과 후의 긍정/중립/부정 비율 및
    그에 따른 증감폭(Delta)을 계산하여 딕셔너리로 반환합니다.
    """
    eff_dt = pd.to_datetime(effective_date)
    
    # 시행 전과 후로 데이터 분리
    before_df = df[df['날짜'] < eff_dt]
    after_df = df[df['날짜'] >= eff_dt]
    
    def get_ratios(sub_df):
        if len(sub_df) == 0:
            return {'긍정': 0.0, '부정': 0.0, '중립': 0.0}
            
        counts = sub_df['감정'].value_counts()
        total = len(sub_df)
        return {
            '긍정': (counts.get('긍정', 0) / total) * 100,
            '부정': (counts.get('부정', 0) / total) * 100,
            '중립': (counts.get('중립', 0) / total) * 100
        }
        
    before_ratios = get_ratios(before_df)
    after_ratios = get_ratios(after_df)
    
    delta_pos = after_ratios['긍정'] - before_ratios['긍정']
    delta_neg = after_ratios['부정'] - before_ratios['부정']
    delta_neu = after_ratios['중립'] - before_ratios['중립']
    
    return {
        'before_pos': before_ratios['긍정'],
        'after_pos': after_ratios['긍정'],
        'delta_pos': delta_pos,
        'before_neg': before_ratios['부정'],
        'after_neg': after_ratios['부정'],
        'delta_neg': delta_neg,
        'before_neu': before_ratios['중립'],
        'after_neu': after_ratios['중립'],
        'delta_neu': delta_neu
    }

def get_top_news_by_date(df, target_date, top_n=5):
    """
    지정한 날짜(target_date)에 감정 분류의 신뢰도('수치')가 가장 높은 뉴스 기사를 정렬하여 조회합니다.
    """
    target_dt = pd.to_datetime(target_date)
    df_day = df[df['날짜'].dt.date == target_dt.date()]
    
    if len(df_day) == 0:
        return pd.DataFrame(columns=['시기', '날짜', '기사제목', 'url', '감정', '수치', '분류근거'])
        
    df_sorted = df_day.sort_values(by='수치', ascending=False).head(top_n)
    
    cols = ['시기', '날짜', '기사제목', 'url', '감정', '수치', '분류근거']
    # 필요한 컬럼만 추출 (없는 경우 기본값 채움)
    result_cols = [c for c in cols if c in df_sorted.columns]
    
    return df_sorted[result_cols]
