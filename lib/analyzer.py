"""
이 파일은 경량 감정 모델(korean-emotion-kluebert-v2)을 활용한 뉴스 감성 분석 엔진 모듈입니다.
기사 제목에 대해 7가지 감정을 분류한 후 이를 긍정/중립/부정으로 매핑하여
결과를 CSV 파일에 저장하고 시기별 요약 통계 결과(summary)까지 함께 도출합니다.
"""

import os
import pandas as pd
import torch

# 전역 모델 상태 변수
classifier = None

def load_classifier():
    """
    korean-emotion-kluebert-v2 모델을 로드하여 감정 분류 pipeline을 생성합니다.
    """
    global classifier
    if classifier is not None:
        return classifier
        
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoConfig, pipeline
        from huggingface_hub import hf_hub_download
        import json
        print("[Info] 경량 감정 분류기(dlckdfuf141/korean-emotion-kluebert-v2) 로딩 시작...")
        
        # 1. 원격에서 원시 config.json 파일 다운로드 (Strict Validation 우회)
        raw_config_path = hf_hub_download(
            repo_id="dlckdfuf141/korean-emotion-kluebert-v2",
            filename="config.json"
        )
        
        with open(raw_config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            
        # 2. 한글 맵핑 데이터 패치
        config_data["id2label"] = {
            0: "공포",
            1: "놀람",
            2: "분노",
            3: "슬픔",
            4: "중립",
            5: "행복",
            6: "혐오"
        }
        config_data["label2id"] = {
            "공포": 0,
            "놀람": 1,
            "분노": 2,
            "슬픔": 3,
            "중립": 4,
            "행복": 5,
            "혐오": 6
        }
        
        # 3. 로컬 파일로 저장
        project_root = os.getcwd()
        while not os.path.exists(os.path.join(project_root, "data")) and os.path.dirname(project_root) != project_root:
            project_root = os.path.dirname(project_root)
            
        local_config_dir = os.path.join(project_root, "data", "temp_config")
        os.makedirs(local_config_dir, exist_ok=True)
        local_config_path = os.path.join(local_config_dir, "config.json")
        
        with open(local_config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
            
        # 4. 로컬 구성을 바탕으로 로드
        config = AutoConfig.from_pretrained(local_config_dir)
        tokenizer = AutoTokenizer.from_pretrained(
            "dlckdfuf141/korean-emotion-kluebert-v2",
            config=config
        )
        model = AutoModelForSequenceClassification.from_pretrained(
            "dlckdfuf141/korean-emotion-kluebert-v2",
            config=config
        )
        
        classifier = pipeline(
            "text-classification",
            model=model,
            tokenizer=tokenizer,
            device="cpu"
        )
        print("[Success] 경량 감정 분류기 로딩 완료.")
        return classifier
    except Exception as e:
        print(f"[Warning] 경량 모델 로딩 실패: {e}")
        return None

def predict_sentiment_qwen(title):
    """
    개별 뉴스 기사 제목의 감정을 예측하여 긍정/중립/부정으로 분류합니다.
    AutoConfig 매핑으로 반환된 한글 감정을 최종 2차 감정으로 변환합니다.
    """
    try:
        clf = load_classifier()
        if clf is None:
            raise RuntimeError("감정 분류기 로드 실패")
            
        pred = clf(title)[0]
        emotion = pred['label'] # 직접 한글 감정 명칭 반환
        
        # 2차 최종 감정 매핑
        # 공포(0), 분노(2), 슬픔(3), 혐오(6) -> 부정
        # 놀람(1), 중립(4) -> 중립
        # 행복(5) -> 긍정
        sentiment_map = {
            "공포": "부정",
            "분노": "부정",
            "슬픔": "부정",
            "혐오": "부정",
            "놀람": "중립",
            "중립": "중립",
            "행복": "긍정"
        }
        sentiment = sentiment_map.get(emotion, "중립")
        return sentiment
    except Exception as e:
        return "중립"

def run_qwen_analysis_pipeline(input_path="data/News_Scraping_retouch.csv", 
                               output_path="data/News_Scraping.csv", 
                               summary_path="data/News_Scraping_summary.csv", 
                               sample_mode=False):
    """
    수집된 뉴스 CSV를 읽어 경량 감정 분석을 일괄 수행하고 결과를 CSV 파일로 저장합니다.
    또한 before / after 시점별 감정 요약 통계(summary) 결과도 생성합니다.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"[Error] 입력 파일 '{input_path}'을 찾을 수 없습니다. 수집을 먼저 실행해 주세요.")
        
    df = pd.read_csv(input_path, encoding="utf-8-sig")
    print(f"[Info] 총 {len(df)}개의 기사가 로드되었습니다.")
    
    # 리소스 절약을 위한 샘플링 처리
    if sample_mode:
        df_target = df.head(100).copy()
        print(f"[Info] 샘플 분석 모드 가동: 상위 100건만 감정 분류를 수행합니다.")
    else:
        df_target = df.copy()
        print(f"[Info] 전체 감성 분석 시작 (경량 모델 활용)...")
        
    # 모델 로드
    if classifier is None:
        load_classifier()
        
    sentiments = []
    total = len(df_target)
    for idx, row in enumerate(df_target.itertuples(), 1):
        title = row.기사제목
        sentiment = predict_sentiment_qwen(title)
        sentiments.append(sentiment)
        
        if idx % 100 == 0 or idx == total:
            print(f"[{idx}/{total}] 기사 감성 분류 진행 중... (현재: {sentiment})")
            
    df_target['감정'] = sentiments
    
    # 데이터 폴더가 없는 경우 생성
    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
        
    # 최종 결과 저장
    df_target.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[Success] 감성 분석 결과가 '{output_path}'에 저장되었습니다.")
    
    # --- before / after 요약 CSV 생성 ---
    df_target['period'] = df_target['시기'].map(
        lambda x: 'before' if x == '시행전' else 'after'
    )
    
    pivot_df = df_target.groupby(['period', '감정']).size().unstack(fill_value=0)
    for col in ['긍정', '중립', '부정']:
        if col not in pivot_df.columns:
            pivot_df[col] = 0
            
    ratio_df = pivot_df.div(pivot_df.sum(axis=1), axis=0) * 100
    ratio_df = ratio_df.reindex(columns=['긍정', '중립', '부정']).reset_index()
    
    sum_dir = os.path.dirname(summary_path)
    if sum_dir and not os.path.exists(sum_dir):
        os.makedirs(sum_dir, exist_ok=True)
        
    ratio_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
    print("=============================================================")
    print(" [뉴스 감성 요약 통계 결과]")
    print("=============================================================")
    print(ratio_df.to_string(index=False))
    print(f"[Success] 요약 파일이 '{summary_path}'에 저장 완료되었습니다.")
