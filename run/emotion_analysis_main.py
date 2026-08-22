"""
이 파일은 수집된 뉴스 기사(data/News_Scraping.csv) 전체에 대해
경량 감정 분류 모델(korean-emotion-kluebert-v2)을 사용하여 감성 분석 및 통계 요약을 단독 수행하는 메인 스크립트입니다.
"""

import os
import sys
import time
import json
import pandas as pd
from datetime import datetime, timedelta
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoConfig, pipeline
from huggingface_hub import hf_hub_download

def main():
    # 1. 프로젝트 루트(data 폴더가 존재하는 상위 폴더) 동적 탐색
    project_root = os.getcwd()
    while not os.path.exists(os.path.join(project_root, "data")) and os.path.dirname(project_root) != project_root:
        project_root = os.path.dirname(project_root)
        
    input_path = os.path.join(project_root, "data", "News_Scraping.csv")
    output_path = os.path.join(project_root, "data", "News_Scraping.csv")
    summary_path = os.path.join(project_root, "data", "News_Scraping_summary.csv")
    
    print("=============================================================")
    print(" [경량 AI 모델(kluebert-v2) 기반 부동산 뉴스 감성 라벨링]")
    print("=============================================================")
    print(f" 입력 파일: {input_path}")
    print(f" 출력 파일: {output_path}")
    print(f" 요약 파일: {summary_path}")
    print("-------------------------------------------------------------")
    
    if not os.path.exists(input_path):
        print(f"[Error] 입력 파일 '{input_path}'이 존재하지 않습니다. 먼저 크롤링 수집을 구동해 주세요.")
        sys.exit(1)
        
    # 2. 경량 감정 분류 모델(kluebert-v2) 적재
    print("[Info] 경량 감정 분류기(dlckdfuf141/korean-emotion-kluebert-v2) 로딩 시작...")
    try:
        # 허깅페이스 허브에서 원시 config.json 파일을 직접 다운로드 (검증 우회)
        print("[Info] 원격 config.json 파일 다운로드 및 로컬 패치 진행 중...")
        raw_config_path = hf_hub_download(
            repo_id="dlckdfuf141/korean-emotion-kluebert-v2",
            filename="config.json"
        )
        
        with open(raw_config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            
        # 규격에 맞게 7개 감정 이름(dict[int, str])으로 명시적 오버라이드
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
        
        # 보정된 config.json 파일을 프로젝트 내 임시 경로에 저장
        local_config_dir = os.path.join(project_root, "data", "temp_config")
        os.makedirs(local_config_dir, exist_ok=True)
        local_config_path = os.path.join(local_config_dir, "config.json")
        
        with open(local_config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
            
        # 로컬 설정을 참조하여 AutoConfig 생성 (ValidationError 완전 해결)
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
    except Exception as e:
        print(f"[Error] 모델 로딩 중 예외 발생: {e}")
        sys.exit(1)
        
    # 3. 데이터프레임 로드
    df = pd.read_csv(input_path, encoding="utf-8-sig")
    print(f"[Info] 총 {len(df):,}개의 기사가 로드되었습니다.")
    
    # 4. 개별 예측 헬퍼 함수 정의
    def predict_sentiment(title):
        try:
            pred = classifier(title)[0]
            emotion = pred['label'] # 한글 감정 명칭 반환됨
            
            # 2차 최종 감정 매핑
            sentiment_map = {
                "공포": "부정", "분노": "부정", "슬픔": "부정", "혐오": "부정",
                "놀람": "중립", "중립": "중립", "행복": "긍정"
            }
            return sentiment_map.get(emotion, "중립")
        except Exception:
            return "중립"
            
    # 5. 전체 감성 분류 일괄 루프 수행
    print("\n[Start] 뉴스 기사 감성 분석을 시작합니다...")
    start_time = time.time()
    
    sentiments = []
    total = len(df)
    for idx, row in enumerate(df.itertuples(), 1):
        title = row.기사제목
        sentiment = predict_sentiment(title)
        sentiments.append(sentiment)
        
        if idx % 100 == 0 or idx == total:
            print(f"  [{idx}/{total}] 감정 분석 진행 중... (현재: {sentiment})")
            
    df['감정'] = sentiments
    elapsed = time.time() - start_time
    print(f"[Success] 감성 분석 완료! (소요 시간: {elapsed:.1f}초)")
    
    # 6. CSV 저장
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[Success] 감성 분석 결과가 '{output_path}'에 저장되었습니다.")
    
    # 7. 대책 시행 전/후(시행일 6/27, 9/7, 10/15) 감정 요약 통계(summary) 생성
    print("\n[Info] 대책 시행일 전/후 요약 통계를 산출합니다...")
    EFFECTIVE_DATES = [
        {"label": "6·27", "date": "2025-06-28"},
        {"label": "9·7", "date": "2025-09-08"},
        {"label": "10·15", "date": "2025-10-16"}
    ]
    
    try:
        df_sum = df.copy()
        df_sum['날짜'] = pd.to_datetime(df_sum['날짜'])
        
        summary_rows = []
        for policy in EFFECTIVE_DATES:
            eff_dt = pd.to_datetime(policy['date'])
            before_start = eff_dt - timedelta(days=30)
            after_end = eff_dt + timedelta(days=30)
            
            before_df = df_sum[(df_sum['날짜'] >= before_start) & (df_sum['날짜'] < eff_dt)]
            after_df = df_sum[(df_sum['날짜'] >= eff_dt) & (df_sum['날짜'] <= after_end)]
            
            for period_label, sub_df in [('before', before_df), ('after', after_df)]:
                if len(sub_df) == 0:
                    summary_rows.append({
                        '대책': policy['label'], 'period': period_label,
                        '긍정': 0.0, '중립': 0.0, '부정': 0.0, '기사수': 0
                    })
                    continue
                    
                counts = sub_df['감정'].value_counts()
                total_count = len(sub_df)
                summary_rows.append({
                    '대책': policy['label'],
                    'period': period_label,
                    '긍정': (counts.get('긍정', 0) / total_count) * 100,
                    '중립': (counts.get('중립', 0) / total_count) * 100,
                    '부정': (counts.get('부정', 0) / total_count) * 100,
                    '기사수': total_count
                })
                
        summary_df = pd.DataFrame(summary_rows)
        summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
        
        print("=============================================================")
        print(" [대책별 요약 통계 결과 (단일 감정)]")
        print("=============================================================")
        for policy in EFFECTIVE_DATES:
            print(f"\n{'='*50}")
            print(f"  {policy['label']} 대책 (시행일: {policy['date']})")
            print(f"{'='*50}")
            policy_df = summary_df[summary_df['대책'] == policy['label']]
            print(policy_df.to_string(index=False))
        print(f"\n[Success] 요약 통계 파일이 '{summary_path}'에 저장 완료되었습니다.")
        
    except Exception as e:
        print(f"[Warning] 요약 통계 계산 중 에러 발생: {e}")
        
    print("\n[Complete] 모든 분석 및 라벨링 처리가 정상 종료되었습니다.")

if __name__ == "__main__":
    main()
