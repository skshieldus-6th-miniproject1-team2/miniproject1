"""
이 파일은 네이버 부동산 뉴스를 수집하고 저장하는 크롤러 모듈입니다.
특정 부동산 규제 정책 시행일을 기준으로 앞뒤 분석 대상 기간 동안의 뉴스 기사를 수집하며,
제외 단어 정규식(EXCLUDE_PATTERN)을 사용해 잡음이 섞인 기사를 자동으로 필터링합니다.
"""

import os
import re
import csv
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# --- 1. 단일 키워드 기반 제외 패턴 정의 (잡음 뉴스 필터링) ---
EXCLUDE_PATTERN = (
    # 1. 종합 브리핑 / 뉴스 요약 / 미디어 포맷
    r"오늘뉴스|뉴스브리핑|헤드라인|주요뉴스|포토뉴스|카드뉴스|그래픽뉴스|분양캘린더|"
    # 2. 일반 정치 / 형사 / 수사 / 재판 / 비리
    r"특검|명품백|김만배|청문회|국정감사|상임위|체포동의안|경선|계좌추적|"
    r"사기범|구속영장|피의자|징역|횡령|배임|음주운전|도주|압수수색|기소|송치|입건|뇌물|선고|"
    # 3. 노조 / 파업
    r"건설노조|철도노조|민주노총|한국노총|타워크레인|준법투쟁|총파업|"
    # 4. 해외 국가 / 도시 / 글로벌
    r"해외|글로벌|외신|월가|연준|Fed|美|"
    r"미국|중국|일본|베트남|사우디|체코|인도네시아|아프리카|두바이|유럽|영국|프랑스|독일|호주|캐나다|대만|홍콩|"
    r"뉴욕|런던|파리|도쿄|맨해튼|"
    # 5. 기업 M&A / 회사 지분 거래 / 사옥
    r"합병|인수|매각|흡수합병|M&A|빅딜|자회사|지분|사옥|법인|자산매각|인수무산|"
    # 6. 건설사 경영 / 인사 / 실적 / 폐업 / 브랜드
    r"임원인사|대표이사|신임대표|CEO|선임|취임|사임|사의|조직개편|"
    r"잠정실적|어닝|영업이익|흑자전환|적자전환|회사채|신용등급|"
    r"줄폐업|폐업|부도|도산|브랜드론칭|브랜드리뉴얼|새브랜드|"
    # 7. 비주택 토목 / 플랜트 / 인프라 / 항공
    r"원전|플랜트|고속도로|휴게시설|가덕도|항만|교량|터널|풍력|신재생|수주|수주전|수주고|수주액|"
    r"공항|활주로|항공기|여객기|비행기|화물차|KTX|"
    # 8. 비주거용 상업시설 / 물류 / 레저 / 공장
    r"물류센터|데이터센터|지식산업센터|골프장|리조트|호텔|꼬마빌딩|상업시설|상가|공장|물류단지|산업단지|"
    # 9. CSR / 기부 / 행사 / 학술 / 협회 / 포상
    r"기부|봉사|장학|사회공헌|후원금|시상식|협약식|MOU|인테리어|한샘|리바트|부실시공|부실공사|하자|"
    r"간담회|포럼|세미나|컨퍼런스|공모전|박람회|수여식|설명회|공제조합|기념식|표창|위촉|임명|공모|"
    # 10. 단순 개관 홍보 / 시공 하자 / 연예·가십 / IT·테크
    r"견본주택|모델하우스|홍보관|외벽|하자논란|하자보수|자택공개|초호화자택|"
    r"연예인|배우|가수|아이돌|BTS|방탄소년단|영화|드라마|예능|올림픽|월드컵|페스티벌|콘서트|축제|"
    r"갤럭시|아이폰|스마트폰|인공지능|챗GPT|생성형|자율주행|비트코인|가상화폐|코인|SKT|"
    # 11. 단순 안전사고 / 재난 / 인사 / 부고 / 채용
    r"사망|숨져|숨진|추락사|정전|지진|안전점검|"
    r"부고|부친상|모친상|별세|화촉|출판기념회|공인중개사|신입채용|인턴채용|공모|공개|개장|진출"
)
exclude_re = re.compile(EXCLUDE_PATTERN)

# --- 2. 부동산 정책 데이터 정의 (이재명 대통령 6.27 대책 타겟팅) ---
POLICIES = [
    {
        "president": "이재명",
        "policy": "6·27 가계부채 관리 강화방안",
        "announcement_date": "2025-06-27",
        "effective_date": "2025-06-28",
        "summary": "수도권 주담대 규제 강화"
    }
]

def get_policy_mapping(date_str):
    """
    입력된 날짜에 대응하는 부동산 정책 정보 및 시기(시행전, 시행일, 초기반응, 체감반응)를 매핑합니다.
    """
    input_date = None
    for fmt in ("%Y%m%d", "%Y-%m-%d"):
        try:
            input_date = datetime.strptime(date_str, fmt).date()
            break
        except ValueError:
            continue

    if not input_date:
        return []

    matched = []
    for item in POLICIES:
        eff_date = datetime.strptime(item["effective_date"], "%Y-%m-%d").date()

        # 각 시점 범위 설정
        before_start = eff_date - timedelta(days=30)
        before_end = eff_date - timedelta(days=1)
        after_start = eff_date + timedelta(days=1)
        after_end = eff_date + timedelta(days=30)
        feel_start = eff_date + timedelta(days=31)
        feel_end = eff_date + timedelta(days=90)

        period = None
        if before_start <= input_date <= before_end:
            period = "시행전"
        elif input_date == eff_date:
            period = "시행일"
        elif after_start <= input_date <= after_end:
            period = "초기반응"
        elif feel_start <= input_date <= feel_end:
            period = "체감반응"

        if period:
            matched.append({
                "president": item["president"],
                "policy": item["policy"],
                "policy_summary": item["summary"],
                "period": period,
                "date": input_date.strftime("%Y-%m-%d")
            })

    return matched

def scrape_naver_land_news(date_str, max_articles=100):
    """
    네이버 부동산 뉴스 섹션에서 특정 날짜(date_str: YYYYMMDD)의 기사 제목과 링크를 페이지네이션을 통해
    최대 max_articles개 수집하되, EXCLUDE_PATTERN 필터와 매칭되는 기사는 필터링합니다.
    """
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36'
    }
    articles = []
    
    url = f"https://news.naver.com/breakingnews/section/101/260?date={date_str}"
    try:
        res = requests.get(url, headers=headers)
        if not res.ok:
            return articles
            
        soup = BeautifulSoup(res.text, 'html.parser')
        a_tags = soup.select("a.sa_text_title")
        for a in a_tags:
            title = a.text.strip()
            link = a.get('href', '').strip()
            if title and link:
                if exclude_re.search(title):
                    continue
                articles.append((title, link))
                
        if len(articles) >= max_articles:
            return articles[:max_articles]
            
        container = soup.select_one("div.section_latest_article._CONTENT_LIST._PERSIST_META")
        if not container:
            return articles
            
        cursor = container.get("data-cursor")
        has_next = container.get("data-has-next")
        
        page_no = 2
        while cursor and has_next == "true" and len(articles) < max_articles:
            api_url = f"https://news.naver.com/section/template/SECTION_ARTICLE_LIST_FOR_LATEST?sid=101&sid2=260&cluid=&pageNo={page_no}&date={date_str}&next={cursor}"
            api_res = requests.get(api_url, headers=headers)
            if not api_res.ok:
                break
                
            data = api_res.json()
            rendered_component = data.get("renderedComponent", {})
            html_content = rendered_component.get("SECTION_ARTICLE_LIST_FOR_LATEST", "")
            if not html_content:
                break
                
            api_soup = BeautifulSoup(html_content, 'html.parser')
            api_a_tags = api_soup.select("a.sa_text_title")
            if not api_a_tags:
                break
                
            for a in api_a_tags:
                title = a.text.strip()
                link = a.get('href', '').strip()
                if title and link:
                    if exclude_re.search(title):
                        continue
                    articles.append((title, link))
                    
            if len(articles) >= max_articles:
                return articles[:max_articles]
                
            cursor_el = api_soup.select_one("div.section_latest_article._CONTENT_LIST._PERSIST_META")
            if not cursor_el:
                break
                
            cursor = cursor_el.get("data-cursor")
            has_next = cursor_el.get("data-has-next")
            page_no += 1
            
            time.sleep(0.1)
            
    except Exception as e:
        pass
        
    return articles

def save_to_csv(rows, filename="data/News_Scraping_retouch.csv"):
    """
    수집 및 가공된 뉴스 기사를 CSV 파일에 추가 저장합니다. 중복 데이터(시기, 날짜, URL 기준)는 제외합니다.
    """
    file_exists = os.path.exists(filename)
    existing_keys = set()
    
    if file_exists:
        try:
            with open(filename, mode='r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header:
                    for line in reader:
                        if len(line) >= 4:
                            period = line[0]
                            date = line[1]
                            url = line[3]
                            existing_keys.add((period, date, url))
        except Exception:
            pass
            
    new_rows = []
    for r in rows:
        period = r[0]
        date = r[1]
        url = r[3]
        key = (period, date, url)
        if key not in existing_keys:
            new_rows.append(r)
            existing_keys.add(key)
            
    if not new_rows:
        return None

    try:
        # 데이터 폴더가 없는 경우 생성
        dir_name = os.path.dirname(filename)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            
        file_exists = os.path.exists(filename)
        with open(filename, mode='a', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["시기", "날짜", "기사제목", "url", "감정"])
            writer.writerows(new_rows)
    except Exception:
        pass
    
    return len(new_rows)

def sort_csv_by_date(filename="data/News_Scraping_retouch.csv"):
    """
    저장된 CSV 파일을 날짜 오름차순으로 정렬하여 다시 덮어씁니다.
    """
    if not os.path.exists(filename):
        return

    try:
        with open(filename, mode='r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                return
            rows = list(reader)

        def parse_date(row):
            if len(row) > 1:
                try:
                    return datetime.strptime(row[1], "%Y-%m-%d").date()
                except ValueError:
                    pass
            return datetime.min.date()

        rows.sort(key=parse_date)

        with open(filename, mode='w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
    except Exception:
        pass

def scrape_all_policies(filename="data/News_Scraping_retouch.csv", max_articles_per_day=100):
    """
    이재명 대통령 6.27 부동산 대책의 4개 시점 전체 기간(총 121일)에 대해
    매일 최대 max_articles_per_day개의 부동산 뉴스를 수집해 CSV에 정렬 및 누적합니다.
    """
    total_started = time.time()
    print(f"\n[Start] 이재명 대통령 6.27 부동산 대책 전체 기간(총 121일) 뉴스 수집을 시작합니다.")
    
    p = POLICIES[0]
    eff_date = datetime.strptime(p["effective_date"], "%Y-%m-%d").date()
    
    # 4개 정책 시점 기간 정의
    periods = {
        "시행전": [eff_date - timedelta(days=i) for i in range(30, 0, -1)],
        "시행일": [eff_date],
        "초기반응": [eff_date + timedelta(days=i) for i in range(1, 31)],
        "체감반응": [eff_date + timedelta(days=i) for i in range(31, 91)]
    }
    
    # 기존 크롤링 파일이 있으면 삭제하고 새로 시작
    if os.path.exists(filename):
        try:
            os.remove(filename)
            print(f"[Info] 기존 데이터 파일 '{filename}'을 삭제하고 새로 수집을 개시합니다.")
        except Exception as e:
            print(f"[Warning] 기존 파일 삭제 실패: {e}")
            
    for period_name, date_list in periods.items():
        print(f"\n>>> [{period_name}] 수집 시작 (기간: {len(date_list)}일, 하루 한도: {max_articles_per_day}개) ...")
        
        for idx, target_date in enumerate(date_list, 1):
            date_str = target_date.strftime("%Y%m%d")
            print(f"[{idx}/{len(date_list)}] {target_date.strftime('%Y-%m-%d')} 수집 중...", end=" ", flush=True)
            
            day_articles = scrape_naver_land_news(date_str, max_articles=max_articles_per_day)
            if day_articles:
                rows = []
                for title, url in day_articles:
                    rows.append([
                        period_name,
                        target_date.strftime("%Y-%m-%d"),
                        title,
                        url,
                        ""  # 감정 컬럼 초기화 공란
                    ])
                saved_cnt = save_to_csv(rows, filename)
                print(f"성공: {len(day_articles)}개 수집 완료 (신규 추가: {saved_cnt if saved_cnt is not None else 0}개)")
            else:
                print("기사 없음")
            
            time.sleep(0.1)
            
        print(f"[{period_name}] 수집 완료!")
        
    duration = time.time() - total_started
    print(f"\n[Finished] 전체 121일 뉴스 기사 수집 완료. 소요 시간: {duration:.2f}초.")
    sort_csv_by_date(filename)
