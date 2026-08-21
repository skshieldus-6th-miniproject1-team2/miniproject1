"""
이 파일은 Qwen 8B LLM 및 경량 대체 모델을 활용하여 3가지 관점(기업, 소비자, 시장)에서 뉴스 감성 분석을 수행하는 엔진 모듈입니다.
pandas 벡터화 방식을 지원하여 대량의 기사를 고속으로 분석하고, 결과를 CSV에 저장하며,
부동산 대책별 시행 전/후의 3관점 감정 비율 요약 통계(summary)를 생성합니다.
"""

import os
import time
import pandas as pd
import torch
from datetime import datetime, timedelta

# --- 1. Transformers 내 qwen3 아키텍처 지원을 위한 임시 우회 매핑 등록 ---
try:
    from transformers.models.auto.configuration_auto import CONFIG_MAPPING
    from transformers import Qwen2Config
    if "qwen3" not in CONFIG_MAPPING:
        CONFIG_MAPPING.register("qwen3", Qwen2Config)
        
    from transformers.models.auto.modeling_auto import MODEL_FOR_CAUSAL_LM_MAPPING
    from transformers import Qwen2ForCausalLM
    if "qwen3" not in MODEL_FOR_CAUSAL_LM_MAPPING:
        MODEL_FOR_CAUSAL_LM_MAPPING.register("qwen3", Qwen2ForCausalLM)
except Exception:
    pass

# 전역 모델 상태 변수들
fallback_mode = False
fallback_classifier = None
model = None
tokenizer = None

# 3관점별 Heuristic 키워드 사전 정의
VIEWPOINT_KEYWORDS = {
    '기업': {
        'pos': ['분양호조', '착공', '수주', '분양성공', '완판', '공급확대', '활성화', '매출증가',
                '실적개선', '흑자', '호실적', '수익성', '사업승인', '인허가', '정비사업',
                '재건축', '재개발', '도시정비', '공급물량', '분양대전', '청약열기'],
        'neg': ['미분양', '공사중단', '분양실패', '부도', '워크아웃', '자금난', '유동성위기',
                '적자', '매출감소', '수주감소', '사업지연', '인허가지연', '규제강화',
                '대출규제', '분양가상한제', '원가공개', '분양권전매금지', '착공감소']
    },
    '소비자': {
        'pos': ['금리인하', '대출완화', '취득세감면', '세금감면', '전세안정', '월세하락',
                '공급확대', '청약완화', '주거안정', '보금자리', '내집마련', '무주택',
                '실수요자', '생애최초', '신혼부부', '집값하락', '매수기회', '전세대출'],
        'neg': ['집값폭등', '전세폭등', '월세급등', '금리인상', '대출축소', '대출규제',
                '이자부담', '주거비', 'DSR', 'LTV', '영끌', '패닉바잉', '갭투자',
                '전세사기', '깡통전세', '역전세', '보증금미반환', '주거불안', '세부담']
    },
    '시장': {
        'pos': ['거래량증가', '거래회복', '매매증가', '상승세', '상승전환', '반등',
                '매수세', '회복세', '호가상승', '시장활성', '투자심리', '유동성',
                '상승', '급등', '돌파', '상한가', '신고가', '회복', '활황'],
        'neg': ['거래절벽', '거래감소', '하락세', '약세', '냉각', '침체', '위축',
                '매수절벽', '관망세', '하방압력', '폭락', '급락', '조정', '둔화',
                '하락', '규제', '우려', '부담', '위기', '불안', '경착륙']
    }
}

# 3개 대책 시행일 리스트
EFFECTIVE_DATES = [
    {"label": "6·27", "date": "2025-06-28"},
    {"label": "9·7", "date": "2025-09-08"},
    {"label": "10·15", "date": "2025-10-16"}
]

def load_sentiment_model_3view(model_id="LLM-SocialMedia/Qwen3-8B-Korean-Sentiment"):
    """
    Qwen3 8B 한국어 감정 분석 모델을 적재합니다.
    CPU 환경이나 가상 메모리 부족(WinError 1455) 시, OOM을 방지하기 위해 경량 로컬 분류 모델(Fallback)로 자동 전환합니다.
    """
    global fallback_mode, fallback_classifier, model, tokenizer
    
    try:
        from peft import AutoPeftModelForCausalLM
        from transformers import AutoTokenizer
        print(f"[Info] Qwen3 8B 모델 로딩 시도: {model_id} (CPU 적재 및 bfloat16 메모리 최적화)")
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
        print("[Success] Qwen 8B 모델 및 토크나이저가 로드 완료되었습니다.")
        fallback_mode = False
    except OSError as e:
        print(f"\n[Warning] CPU 시스템 메모리/가상 메모리 고갈로 Qwen 8B 적재 실패: {e}")
        print("[Info] 시스템 안정성을 위해 '경량 감정 분류기(Fallback) 모드'로 자동 전환합니다.")
        fallback_mode = True
        try:
            from transformers import pipeline
            fallback_classifier = pipeline(
                "sentiment-analysis", 
                model="matthewchang/klue-roberta-base-sentiment-classification",
                device="cpu"
            )
            print("[Success] 대체 경량 감정 모델 로드가 완료되었습니다.")
        except Exception as ex:
            print(f"[Warning] 대체 모델 로드 실패: {ex}. Heuristic 어휘 규칙 매칭 모드로 전환합니다.")

def predict_sentiment_3view(title):
    """
    기업/소비자/시장 3가지 관점에서 각각 독립적으로 감정을 분류하고 분류 근거를 함께 도출합니다.
    """
    global fallback_mode, fallback_classifier, model, tokenizer
    
    # 1. Fallback 모드 또는 Qwen 로드 실패 시: 관점별 키워드 규칙 매칭
    if fallback_mode or (model is None and fallback_classifier is None):
        results = {}
        for viewpoint, keywords in VIEWPOINT_KEYWORDS.items():
            sentiment = '중립'
            reason = f'{viewpoint} 관점에서 명확한 극성 신호가 없어 중립으로 판단됩니다.'
            
            # 긍정 키워드 검사
            for w in keywords['pos']:
                if w in title:
                    sentiment = '긍정'
                    reason = f"[{viewpoint}] 단어 '{w}'이(가) 포함되어 {viewpoint} 관점에서 긍정적으로 분석됨."
                    break
            
            # 긍정이 아닌 경우에만 부정 검사
            if sentiment == '중립':
                for w in keywords['neg']:
                    if w in title:
                        sentiment = '부정'
                        reason = f"[{viewpoint}] 단어 '{w}'이(가) 포함되어 {viewpoint} 관점에서 부정적으로 분석됨."
                        break
            
            results[f'{viewpoint}_감정'] = sentiment
            results[f'{viewpoint}_근거'] = reason
        return results
    
    # 2. Qwen 8B LLM 모드
    messages = [
        {
            "role": "user",
            "content": (
                "아래는 한국어 부동산 뉴스 제목의 감정 분류 작업입니다.\n"
                "3가지 관점(기업, 소비자, 시장)에서 각각 독립적으로 감정을 분류해 주세요.\n\n"
                f"뉴스 제목: {title}\n\n"
                "각 관점의 정의:\n"
                "- 기업 관점: 건설사·시행사·부동산 업계의 사업 환경, 수익성, 분양 성과에 미치는 영향\n"
                "- 소비자 관점: 매수자·임차인·실수요자의 주거비 부담, 자산가치, 내집마련 가능성에 미치는 영향\n"
                "- 시장 관점: 부동산 시장 전체의 거래량, 가격 추세, 유동성, 시장 심리에 미치는 영향\n\n"
                "다음 형식으로 정확히 출력하세요:\n"
                "기업_감정: 긍정/중립/부정\n"
                "기업_근거: (한 문장 이유)\n"
                "소비자_감정: 긍정/중립/부정\n"
                "소비자_근거: (한 문장 이유)\n"
                "시장_감정: 긍정/중립/부정\n"
                "시장_근거: (한 문장 이유)"
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
                max_new_tokens=512,
                temperature=0.1,
                do_sample=False
            )
        gen_tokens = outputs[0][inputs["input_ids"].shape[1]:]
        decoded = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()
        
        results = {
            '기업_감정': '중립', '기업_근거': '분류 근거 없음',
            '소비자_감정': '중립', '소비자_근거': '분류 근거 없음',
            '시장_감정': '중립', '시장_근거': '분류 근거 없음'
        }
        
        for line in decoded.split("\n"):
            line = line.strip()
            for vp in ['기업', '소비자', '시장']:
                if line.startswith(f"{vp}_감정"):
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        val = parts[1].strip()
                        if '긍정' in val:
                            results[f'{vp}_감정'] = '긍정'
                        elif '부정' in val:
                            results[f'{vp}_감정'] = '부정'
                        else:
                            results[f'{vp}_감정'] = '중립'
                elif line.startswith(f"{vp}_근거"):
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        results[f'{vp}_근거'] = parts[1].strip()
        return results
    except Exception as e:
        return {
            '기업_감정': '중립', '기업_근거': f'에러 발생: {e}',
            '소비자_감정': '중립', '소비자_근거': f'에러 발생: {e}',
            '시장_감정': '중립', '시장_근거': f'에러 발생: {e}'
        }

def run_vectorized_sentiment_analysis_3view(df):
    """
    pandas 벡터화 기반 3관점 키워드 감정 분류를 수행하여 데이터프레임에 적용합니다.
    """
    start_time = time.time()
    print(f"\n[Start] 벡터화 3관점 감정 분석을 시작합니다...")
    
    titles = df['기사제목'].fillna('')
    
    for vp, keywords in VIEWPOINT_KEYWORDS.items():
        pos_pattern = '|'.join(keywords['pos'])
        neg_pattern = '|'.join(keywords['neg'])
        
        is_pos = titles.str.contains(pos_pattern, na=False)
        is_neg = titles.str.contains(neg_pattern, na=False)
        
        sentiment = pd.Series('중립', index=df.index)
        sentiment[is_neg] = '부정'
        sentiment[is_pos] = '긍정'
        
        reason = pd.Series(f'{vp} 관점에서 명확한 극성 신호가 없어 중립으로 판단됩니다.', index=df.index)
        
        # 긍정 키워드 매칭
        for w in keywords['pos']:
            mask = titles.str.contains(w, na=False) & (sentiment == '긍정')
            reason[mask] = f"[{vp}] 단어 '{w}'이(가) 포함되어 {vp} 관점에서 긍정적으로 분석됨."
            
        # 부정 키워드 매칭
        for w in keywords['neg']:
            mask = titles.str.contains(w, na=False) & (sentiment == '부정')
            reason[mask] = f"[{vp}] 단어 '{w}'이(가) 포함되어 {vp} 관점에서 부정적으로 분석됨."
            
        df[f'{vp}_감정'] = sentiment
        df[f'{vp}_근거'] = reason
        
        pos_count = (sentiment == '긍정').sum()
        neg_count = (sentiment == '부정').sum()
        neu_count = (sentiment == '중립').sum()
        print(f"  [{vp}] 긍정: {pos_count:,}건 | 중립: {neu_count:,}건 | 부정: {neg_count:,}건")
        
    elapsed = time.time() - start_time
    print(f"[Success] 3관점 감정 분류 완료! (소요: {elapsed:.1f}초)")
    return df

def generate_3view_summary_csv(df, summary_output_path):
    """
    3개 대책 각각에 대해 시행 전(30일)/후(30일) 기간의 3관점별 긍정/중립/부정 비율(%)을 계산하여 요약 CSV를 도출합니다.
    """
    df_temp = df.copy()
    df_temp['날짜'] = pd.to_datetime(df_temp['날짜'])
    
    summary_rows = []
    viewpoints = ['기업', '소비자', '시장']
    
    for policy in EFFECTIVE_DATES:
        eff_dt = pd.to_datetime(policy['date'])
        before_start = eff_dt - timedelta(days=30)
        after_end = eff_dt + timedelta(days=30)
        
        before_df = df_temp[(df_temp['날짜'] >= before_start) & (df_temp['날짜'] < eff_dt)]
        after_df = df_temp[(df_temp['날짜'] >= eff_dt) & (df_temp['날짜'] <= after_end)]
        
        for vp in viewpoints:
            col_name = f'{vp}_감정'
            
            for period_label, sub_df in [('before', before_df), ('after', after_df)]:
                if len(sub_df) == 0:
                    summary_rows.append({
                        '대책': policy['label'], '관점': vp, 'period': period_label,
                        '긍정': 0.0, '중립': 0.0, '부정': 0.0, '기사수': 0
                    })
                    continue
                    
                counts = sub_df[col_name].value_counts()
                total_count = len(sub_df)
                summary_rows.append({
                    '대책': policy['label'],
                    '관점': vp,
                    'period': period_label,
                    '긍정': (counts.get('긍정', 0) / total_count) * 100,
                    '중립': (counts.get('중립', 0) / total_count) * 100,
                    '부정': (counts.get('부정', 0) / total_count) * 100,
                    '기사수': total_count
                })
                
    summary_df = pd.DataFrame(summary_rows)
    
    dir_name = os.path.dirname(summary_output_path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)
        
    summary_df.to_csv(summary_output_path, index=False, encoding="utf-8-sig")
    print(f"[Success] 요약 파일이 '{summary_output_path}'에 저장 완료되었습니다.")
    
    print("=============================================================")
    print(" [3개 대책 × 3관점 요약 통계 결과]")
    print("=============================================================")
    for policy in EFFECTIVE_DATES:
        print(f"\n{'='*50}")
        print(f"  {policy['label']} 대책 (시행일: {policy['date']})")
        print(f"{'='*50}")
        policy_df = summary_df[summary_df['대책'] == policy['label']]
        print(policy_df.to_string(index=False))
        
    return summary_df

def run_qwen_analysis_pipeline_3view(input_path="data/j_News_Scraping_retouch.csv",
                                     output_path="data/j_News_Scraping.csv",
                                     summary_path="data/j_News_Scraping_summary.csv",
                                     sample_mode=False):
    """
    뉴스 CSV를 읽어와 3관점 감성 분석 파이프라인을 가동합니다.
    기본적으로 고속 처리를 위해 pandas 벡터화 방식을 적용하되, 필요 시 LLM 추론도 가동할 수 있게 구조화하였습니다.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"[Error] {input_path} 파일이 존재하지 않습니다. 먼저 수집을 가동해 주세요.")
        
    df = pd.read_csv(input_path, encoding="utf-8-sig")
    print(f"[Info] 총 {len(df):,}개의 기사가 로드되었습니다.")
    print(f"[Info] 기간: {df['날짜'].min()} ~ {df['날짜'].max()}")
    
    if sample_mode:
        df = df.head(100).copy()
        print(f"[Info] 샘플 모드 활성화: 상위 100건에 대해서만 분석을 진행합니다.")
        
    # 벡터화 방식으로 고속 분류 실행
    df_analyzed = run_vectorized_sentiment_analysis_3view(df)
    
    # 결과 저장
    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    df_analyzed.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[Success] 3관점 감성 분석 결과 저장 완료 -> {output_path}")
    
    # 요약 CSV 생성
    generate_3view_summary_csv(df_analyzed, summary_path)
