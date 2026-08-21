"""
이 파일은 Qwen 8B LLM 및 경량 대체 모델을 활용한 뉴스 감성 분석 엔진 모듈입니다.
기사 제목에 대해 심층 추론(최종 감정: 긍정/중립/부정)을 실행하고,
결과를 CSV 파일에 쓰고 전체 시기별 요약 통계 결과(summary)까지 함께 도출합니다.
리소스가 부족한 환경의 경우 경량 감정 모델 및 규칙 기반 매핑으로 자동 FallBack이 동작합니다.
"""

import os
import pandas as pd
import torch
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer

# --- 1. Transformers 내 qwen3 아키텍처 지원을 위한 임시 우회 매핑 등록 ---
try:
    from transformers.models.auto.configuration_auto import CONFIG_MAPPING
    from transformers import Qwen2Config
    if "qwen3" not in CONFIG_MAPPING:
        CONFIG_MAPPING.register("qwen3", Qwen2Config)
        print("[Info] Qwen3 Config 매핑을 Qwen2Config로 우회 등록했습니다.")
        
    from transformers.models.auto.modeling_auto import MODEL_FOR_CAUSAL_LM_MAPPING
    from transformers import Qwen2ForCausalLM
    if "qwen3" not in MODEL_FOR_CAUSAL_LM_MAPPING:
        MODEL_FOR_CAUSAL_LM_MAPPING.register("qwen3", Qwen2ForCausalLM)
        print("[Info] Qwen3 Model 매핑을 Qwen2ForCausalLM으로 우회 등록했습니다.")
except Exception as e:
    print(f"[Warning] Transformers 임시 매핑 등록 중 예외 발생: {e}")

# 전역 모델 상태 변수들
fallback_mode = False
fallback_classifier = None
model = None
tokenizer = None

def load_sentiment_model(model_id="LLM-SocialMedia/Qwen3-8B-Korean-Sentiment"):
    """
    Qwen3 8B 한국어 감성 분석 모델을 적재합니다.
    CPU 환경이나 가상 메모리 부족(WinError 1455) 시, OOM을 방지하기 위해 경량 로컬 분류 모델(Fallback)로 자동 전환합니다.
    """
    global fallback_mode, fallback_classifier, model, tokenizer
    
    try:
        print(f"[Info] Qwen3 8B 모델 로딩 시작: {model_id} (CPU 적재 및 메모리 최적화)")
        model = AutoPeftModelForCausalLM.from_pretrained(
            model_id,
            device_map="cpu",
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
            trust_remote_code=True
        )
        tokenizer = AutoTokenizer.from_pretrained(
            "Qwen/Qwen3-8B",
            trust_remote_code=True,
            use_fast=False
        )
        model.eval()
        print("[Success] Qwen 8B 모델 및 토크나이저 로드가 완료되었습니다.")
        fallback_mode = False
        
    except (OSError, MemoryError, RuntimeError) as e:
        print(f"\n[Warning] 자원 한계로 Qwen 8B 로드 실패: {e}")
        print("[Info] 시스템 안정성을 위해 '경량 감정 분류기(Fallback) 모드'로 전환합니다.")
        fallback_mode = True
        try:
            from transformers import pipeline
            # 용량이 매우 작아 CPU에서도 즉시 작동하는 감정 분류 모델
            fallback_classifier = pipeline(
                "sentiment-analysis",
                model="matthewchang/klue-roberta-base-sentiment-classification",
                device="cpu"
            )
            print("[Success] 경량 로컬 감정 분류기(Fallback) 로딩 완료.")
        except Exception as ex:
            print(f"[Warning] 경량 모델 로딩도 실패: {ex}. 키워드 매핑 방식으로 처리합니다.")

def predict_sentiment_qwen(title):
    """
    개별 뉴스 기사 제목의 감정을 예측하고 분류 근거를 출력합니다.
    """
    global fallback_mode, fallback_classifier, model, tokenizer
    
    # --- A. Fallback 경량 분류기 또는 키워드 분석 실행 ---
    if fallback_mode:
        try:
            if fallback_classifier is not None:
                pred = fallback_classifier(title)[0]
                label = pred['label']
                score = pred['score']
                
                # 라벨 3그룹 정규화
                if 'positive' in label.lower() or '긍정' in label:
                    sentiment = '긍정'
                elif 'negative' in label.lower() or '부정' in label:
                    sentiment = '부정'
                else:
                    sentiment = '중립'
                    
                reason = f"[Fallback 예측] 신뢰도 {score:.2f}로 {sentiment} 감정으로 평가되었습니다."
                return reason, sentiment
        except Exception:
            pass
            
        # --- B. 초경량 어휘 규칙 분석 (Heuristic) ---
        pos_words = ['상승', '급등', '돌파', '환영', '호재', '완화', '대책', '활성화', '인기', '상승세']
        neg_words = ['하락', '폭락', '규제', '우려', '부담', '둔화', '위기', '냉각', '하자', '불안']
        
        sentiment = '중립'
        reason = "문맥 상 중립 판단"
        
        for w in pos_words:
            if w in title:
                sentiment = '긍정'
                reason = f"단어 '{w}'이(가) 포함되어 긍정적으로 판단되었습니다."
                break
        if sentiment == '중립':
            for w in neg_words:
                if w in title:
                    sentiment = '부정'
                    reason = f"단어 '{w}'이(가) 포함되어 부정적으로 판단되었습니다."
                    break
                    
        return reason, sentiment
        
    # --- C. Qwen 8B LLM 추론 가동 ---
    messages = [
        {
            "role": "user",
            "content": (
                "아래는 한국어 부동산 뉴스 제목의 감정 분류 작업입니다.\n\n"
                f"댓글: {title}\n\n"
                "다음 단계별로 꼼꼼히 생각하고 분석해 주세요:\n"
                "step_0. 댓글에서 사용된 주요 단어와 표현의 감정적 의미 분석\n"
                "step_1. 이모티콘, 이모지, 밈, 인터넷 은어의 숨겨진 의미 분석\n"
                "step_2. 댓글의 맥락과 의도 분석\n"
                "step_3. 댓글을 감정을 분류 하세요\n"
                "step_4. 최종 감정 분류: '긍정', '중립', '부정' 중 하나\n\n"
                "마지막으로 아래 두 가지를 명확히 작성하세요:\n"
                "1. 분류 근거: 각 단계 분석을 종합한 감정 분류 이유\n"
                "2. 감정 분류 결과: '긍정', '중립', '부정' 중 하나로 출력\n\n"
                "출력 예시:\n"
                "분류 근거: 이 댓글은 규제에 대한 우려를 표명하고 있어 부정적인 평가를 담고 있습니다.\n"
                "감정 분류 결과: 부정"
            )
        }
    ]
    
    try:
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                input_ids=inputs["input_ids"],
                max_new_tokens=256,
                temperature=0.1,
                do_sample=False
            )
            
        gen_tokens = outputs[0][inputs["input_ids"].shape[1]:]
        decoded = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()
        
        reason = "분류 근거 분석 실패"
        sentiment = "중립"
        for line in decoded.split("\n"):
            line = line.strip()
            if "분류 근거:" in line or "분류근거:" in line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    reason = parts[1].strip()
            elif "감정 분류 결과:" in line or "감정분류결과:" in line or "결과:" in line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    val = parts[1].strip()
                    if "긍정" in val:
                        sentiment = "긍정"
                    elif "부정" in val:
                        sentiment = "부정"
                    elif "중립" in val:
                        sentiment = "중립"
                        
        return reason, sentiment
        
    except Exception as e:
        return f"에러 발생: {e}", "중립"

def run_qwen_analysis_pipeline(input_path="data/News_Scraping_retouch.csv", 
                               output_path="data/News_Scraping_retouch_qwen.csv", 
                               summary_path="data/News_Scraping_retouch_qwen_summary.csv", 
                               sample_mode=False):
    """
    수집된 뉴스 CSV를 읽어 Qwen 감성 분석을 일괄 수행하고 결과를 CSV 파일로 저장합니다.
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
        print(f"[Warning] 전체 감성 분석 시작: 대형 LLM 가중치로 인해 시간이 걸릴 수 있습니다.")
        
    # 모델 로드 (지연 적재 방식)
    if model is None and fallback_classifier is None:
        load_sentiment_model()
        
    reasons = []
    qwen_sentiments = []
    
    total = len(df_target)
    for idx, row in enumerate(df_target.itertuples(), 1):
        title = row.기사제목
        reason, sentiment = predict_sentiment_qwen(title)
        reasons.append(reason)
        qwen_sentiments.append(sentiment)
        
        if idx % 10 == 0 or idx == total:
            print(f"[{idx}/{total}] 기사 감성 분류 진행 중... (현재: {sentiment})")
            
    df_target['분류근거'] = reasons
    df_target['감정'] = qwen_sentiments
    
    # 데이터 폴더가 없는 경우 생성
    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
        
    # 최종 결과 저장
    df_target.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[Success] Qwen 감성 분석 결과가 '{output_path}'에 저장되었습니다.")
    
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
    print(" [Qwen 요약 통계 결과]")
    print("=============================================================")
    print(ratio_df.to_string(index=False))
    print(f"[Success] Qwen 요약 파일이 '{summary_path}'에 저장 완료되었습니다.")
