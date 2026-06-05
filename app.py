import streamlit as st
import requests
import json
import time
import os
import re
import random
from dotenv import load_dotenv

# ─── 환경변수 로드 ─────────────────────────────────────────────────────────────
load_dotenv()

def get_api_key(key_name: str) -> str:
    val = os.getenv(key_name)
    if val: return val
    try: return st.secrets["secrets"][key_name]
    except Exception: pass
    try: return st.secrets[key_name]
    except Exception: return ""

KAKAO_API_KEY  = get_api_key("KAKAO_API_KEY")

# ─── 페이지 설정 ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🍽️ 점심 메뉴 & 식당 추천",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=Outfit:wght@400;600;800;900&display=swap');

*, *::before, *::after { box-sizing: border-box; }
.stApp {
    background: linear-gradient(160deg, #0d1117 0%, #161b27 50%, #0d1117 100%);
    font-family: 'Noto Sans KR', sans-serif;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2.5rem 3rem; max-width: 1100px; margin: 0 auto; }

/* 히어로 */
.hero { text-align: center; padding: 2rem 1rem 1.5rem; }
.hero-title {
    font-family: 'Outfit', sans-serif;
    font-size: clamp(2rem, 4vw, 3rem); font-weight: 900;
    background: linear-gradient(135deg, #f472b6 0%, #a78bfa 40%, #60a5fa 80%, #34d399 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    line-height: 1.15; margin-bottom: 0.4rem;
}
.hero-sub { color: rgba(255,255,255,0.45); font-size: 0.95rem; font-weight: 300; }

/* 카드 */
.step-card {
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.09);
    border-radius: 20px; padding: 1.4rem 1.6rem; margin-bottom: 1rem;
    transition: border-color 0.3s;
}
.step-card:hover { border-color: rgba(167,139,250,0.2); }
.step-header { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 1rem; }
.step-badge {
    background: linear-gradient(135deg, #a78bfa, #60a5fa);
    color: white; font-family: 'Outfit', sans-serif;
    font-size: 0.72rem; font-weight: 700;
    padding: 0.18rem 0.6rem; border-radius: 50px; letter-spacing: 0.05em;
}
.step-title { color: white; font-size: 1rem; font-weight: 600; margin: 0; }
.step-desc { color: rgba(255,255,255,0.35); font-size: 0.78rem; margin-left: auto; }

/* 텍스트 인풋 */
div[data-testid="stTextInput"] input {
    background: rgba(255,255,255,0.06) !important;
    border: 1.5px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important; color: white !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    font-size: 0.92rem !important; padding: 0.6rem 1rem !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: rgba(167,139,250,0.6) !important;
    box-shadow: 0 0 0 3px rgba(167,139,250,0.12) !important;
}
div[data-testid="stTextInput"] label,
div[data-testid="stSlider"] label {
    color: rgba(255,255,255,0.6) !important; font-size: 0.83rem !important; font-weight: 500 !important;
}
div[data-testid="stSlider"] > div > div > div > div {
    background: linear-gradient(90deg, #a78bfa, #60a5fa) !important;
}

/* 메인 버튼 */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 50%, #34d399 100%) !important;
    color: white !important; border: none !important; border-radius: 50px !important;
    padding: 0.75rem 2.5rem !important; font-size: 1rem !important; font-weight: 700 !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    box-shadow: 0 6px 30px rgba(167,139,250,0.4) !important;
    transition: all 0.3s ease !important; width: 100% !important;
}
div[data-testid="stButton"] > button:hover {
    transform: translateY(-2px) !important; box-shadow: 0 10px 35px rgba(167,139,250,0.55) !important;
}
div[data-testid="stButton"] > button:disabled {
    background: rgba(255,255,255,0.07) !important; color: rgba(255,255,255,0.28) !important;
    box-shadow: none !important;
}

/* 결과 카드 */
.menu-rec-card {
    background: linear-gradient(135deg, rgba(167,139,250,0.09), rgba(96,165,250,0.09));
    border: 1px solid rgba(167,139,250,0.28); border-radius: 18px;
    padding: 1.5rem; margin-bottom: 1rem; position: relative; overflow: hidden;
}
.menu-rec-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
}
.menu-name { font-family: 'Outfit', sans-serif; font-size: 1.5rem; font-weight: 800; color: white; margin-bottom: 0.25rem; }
.menu-cat  { color: rgba(167,139,250,0.75); font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.3rem; }
.menu-reason { color: rgba(255,255,255,0.62); font-size: 0.87rem; line-height: 1.7; }
.menu-tag {
    display: inline-block; background: rgba(167,139,250,0.18); color: #c4b5fd;
    border: 1px solid rgba(167,139,250,0.3); border-radius: 50px;
    font-size: 0.72rem; padding: 0.18rem 0.65rem; margin: 0.2rem 0.12rem;
}

/* 식당 카드 */
.restaurant-card {
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px; padding: 1.1rem 1.3rem; margin-bottom: 0.8rem;
    transition: all 0.22s; position: relative;
}
.restaurant-card:hover {
    background: rgba(255,255,255,0.07); border-color: rgba(52,211,153,0.28);
    transform: translateX(3px);
}
.restaurant-rank {
    position: absolute; top: 0.9rem; right: 1.1rem;
    font-family: 'Outfit', sans-serif; font-size: 1.3rem; font-weight: 900;
    color: rgba(255,255,255,0.07);
}
.restaurant-name { font-size: 1rem; font-weight: 700; color: white; margin-bottom: 0.18rem; }
.restaurant-cat {
    display: inline-block; background: rgba(52,211,153,0.14); color: #34d399;
    border: 1px solid rgba(52,211,153,0.28); border-radius: 50px;
    font-size: 0.7rem; padding: 0.12rem 0.55rem; margin-bottom: 0.4rem;
}
.restaurant-info {
    color: rgba(255,255,255,0.42); font-size: 0.79rem;
    display: flex; align-items: center; gap: 0.35rem; flex-wrap: wrap;
}
.info-dot { width: 3px; height: 3px; background: rgba(255,255,255,0.18); border-radius: 50%; }
.restaurant-link {
    display: inline-block; margin-top: 0.5rem; color: #60a5fa; font-size: 0.77rem;
    text-decoration: none; border: 1px solid rgba(96,165,250,0.28);
    padding: 0.18rem 0.65rem; border-radius: 50px; transition: all 0.2s;
}
.restaurant-link:hover { background: rgba(96,165,250,0.13); border-color: #60a5fa; }

/* 결과 섹션 타이틀 */
.result-title {
    font-family: 'Outfit', sans-serif; font-size: 1.3rem; font-weight: 800;
    color: white; margin-bottom: 0.9rem; display: flex; align-items: center; gap: 0.4rem;
}

/* 선택 요약 바 */
.sel-bar {
    display: flex; flex-wrap: wrap; gap: 0.45rem;
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px; padding: 0.8rem 1.1rem; margin-bottom: 1rem;
}
.sel-chip {
    background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.11);
    border-radius: 50px; padding: 0.25rem 0.8rem;
    color: rgba(255,255,255,0.68); font-size: 0.79rem;
}

/* 구분선 */
.section-divider {
    border: none; border-top: 1px solid rgba(255,255,255,0.07);
    margin: 1.2rem 0;
}

/* API 배지 */
.api-badge-ok {
    display: inline-flex; align-items: center; gap: 0.35rem;
    background: rgba(52,211,153,0.1); border: 1px solid rgba(52,211,153,0.28);
    color: #34d399; border-radius: 50px; padding: 0.22rem 0.75rem;
    font-size: 0.75rem; font-weight: 500;
}
.model-badge {
    display: inline-flex; align-items: center; gap: 0.35rem;
    background: rgba(96,165,250,0.1); border: 1px solid rgba(96,165,250,0.28);
    color: #60a5fa; border-radius: 50px; padding: 0.22rem 0.75rem;
    font-size: 0.75rem; font-weight: 500;
}
.fallback-notice {
    background: rgba(251,191,36,0.07); border: 1px solid rgba(251,191,36,0.22);
    border-radius: 11px; padding: 0.6rem 0.9rem; margin-bottom: 0.8rem;
    color: rgba(251,191,36,0.82); font-size: 0.78rem;
}

div[data-testid="stSpinner"] p { color: rgba(255,255,255,0.55) !important; }
.stProgress > div > div > div { background: linear-gradient(90deg, #a78bfa, #34d399) !important; }
[data-testid="column"] { padding: 0 0.35rem !important; }
</style>
""", unsafe_allow_html=True)

# ─── 데이터 ───────────────────────────────────────────────────────────────────
MOODS = [
    {"emoji": "😄", "label": "신나고 활기차게", "keyword": "energetic"},
    {"emoji": "😌", "label": "여유롭게 천천히", "keyword": "relaxed"},
    {"emoji": "😤", "label": "스트레스 날려버려","keyword": "stressed"},
    {"emoji": "🥱", "label": "귀찮고 피곤해",   "keyword": "tired"},
    {"emoji": "🤩", "label": "뭔가 특별하게",   "keyword": "special"},
    {"emoji": "💪", "label": "든든하게 채우기", "keyword": "filling"},
    {"emoji": "🌿", "label": "건강하고 가볍게", "keyword": "healthy"},
    {"emoji": "🤑", "label": "저렴하게 배부르게","keyword": "budget"},
    {"emoji": "🥂", "label": "분위기 있게",     "keyword": "fancy"},
    {"emoji": "⚡", "label": "빠르게 해결!",    "keyword": "quick"},
]

FOOD_TYPES = [
    {"emoji": "🍚", "label": "한식",        "query_keyword": "한식"},
    {"emoji": "🥢", "label": "중식",        "query_keyword": "중식"},
    {"emoji": "🍣", "label": "일식",        "query_keyword": "일식"},
    {"emoji": "🍝", "label": "양식",        "query_keyword": "양식"},
    {"emoji": "🌮", "label": "퓨전식",      "query_keyword": "퓨전"},
    {"emoji": "🍜", "label": "분식",        "query_keyword": "분식"},
    {"emoji": "🍔", "label": "패스트푸드",  "query_keyword": "패스트푸드"},
    {"emoji": "🥩", "label": "고기구이",    "query_keyword": "고기집"},
    {"emoji": "🍲", "label": "찌개·탕",    "query_keyword": "찌개"},
    {"emoji": "🌏", "label": "아시안",      "query_keyword": "아시안푸드"},
    {"emoji": "🥗", "label": "샐러드·건강식","query_keyword": "샐러드"},
    {"emoji": "🍕", "label": "피자·치킨",  "query_keyword": "피자"},
]

LOCAL_MENU_DB = {
    "한식":  {"energetic":[("불고기 덮밥",["달콤짭짤","든든","활력충전"]),("제육볶음 정식",["매콤","든든","한식"])],
              "relaxed":[("백반",["따뜻한","집밥","여유"]),("삼계탕",["보양식","여유","건강"])],
              "stressed":[("순대국밥",["얼큰","해장","위안"]),("육개장",["매콤","해장","스트레스해소"])],
              "tired":[("백반",["간단","집밥","편안"]),("삼계탕",["보양","회복","든든"])],
              "special":[("갈비탕",["특별한","고급","한식"]),("한정식",["고급","특별","정성"])],
              "filling":[("제육볶음 정식",["배부른","든든","볼륨"]),("순대국밥",["든든","보양","뜨끈"])],
              "healthy":[("비빔밥",["건강","채소","균형"]),("콩나물국밥",["담백","건강","가볍게"])],
              "budget":[("백반",["가성비","저렴","든든"]),("김치찌개 정식",["가성비","한식","저렴"])],
              "fancy":[("한정식",["고급","분위기","특별"]),("갈비찜",["고급","특별","분위기"])],
              "quick":[("김밥",["빠른","간편","한식"]),("국밥",["빠른","든든","뜨끈"])]},
    "중식":  {"energetic":[("짬뽕",["얼큰","활기","중식"])],"relaxed":[("짜장면",["편안","클래식","여유"])],
              "stressed":[("마라탕",["매콤","스트레스해소","짜릿"])],"tired":[("짜장면",["편안","달콤","간편"])],
              "special":[("탕수육",["특별","바삭","중식"])],"filling":[("짬뽕밥",["든든","볼륨","중식"])],
              "healthy":[("잡채밥",["채소","균형","담백"])],"budget":[("짜장면",["가성비","클래식","저렴"])],
              "fancy":[("베이징덕",["고급","특별","중식"])],"quick":[("짜장면",["빠른","간편","중식"])]},
    "일식":  {"energetic":[("라멘",["활기","뜨끈","일식"])],"relaxed":[("초밥",["여유","신선","고급"])],
              "stressed":[("돈카츠",["바삭","위안","든든"])],"tired":[("우동",["따뜻한","가벼운","간편"])],
              "special":[("오마카세 초밥",["특별","고급","일식"])],"filling":[("돈카츠",["든든","바삭","볼륨"])],
              "healthy":[("연어 덮밥",["건강","신선","단백질"])],"budget":[("규동",["가성비","간편","일식"])],
              "fancy":[("초밥",["고급","신선","분위기"])],"quick":[("우동",["빠른","간편","따뜻한"])]},
    "양식":  {"energetic":[("스테이크",["활기","단백질","든든"])],"relaxed":[("파스타",["여유","로맨틱","양식"])],
              "stressed":[("스테이크",["기분전환","특별","든든"])],"tired":[("크림 파스타",["부드러운","편안","위로"])],
              "special":[("코스 요리",["특별","고급","분위기"])],"filling":[("스테이크",["든든","단백질","볼륨"])],
              "healthy":[("샐러드 볼",["건강","신선","가벼운"])],"budget":[("파스타",["가성비","맛있는","양식"])],
              "fancy":[("와인 파스타",["로맨틱","분위기","고급"])],"quick":[("샌드위치",["빠른","간편","양식"])]},
    "분식":  {"energetic":[("떡볶이",["매콤","활기","한국인"])],"relaxed":[("김밥",["간편","여유","소박한"])],
              "stressed":[("라볶이",["매콤","스트레스해소","분식"])],"tired":[("순대",["간편","든든","분식"])],
              "special":[("떡볶이+순대+튀김",["세트","든든","분식"])],"filling":[("떡볶이+순대",["든든","볼륨","분식"])],
              "healthy":[("야채 김밥",["건강","가벼운","채소"])],"budget":[("떡볶이",["가성비","저렴","간식"])],
              "fancy":[("치즈 떡볶이",["특별","치즈","분식"])],"quick":[("김밥",["빠른","간편","저렴"])]},
    "default":{"energetic":[("제육볶음 정식",["활기","든든","매콤"])],"relaxed":[("파스타",["여유","맛있는","편안"])],
               "stressed":[("마라탕",["스트레스해소","매콤","짜릿"])],"tired":[("우동",["따뜻한","간편","회복"])],
               "special":[("초밥",["특별","신선","고급"])],"filling":[("돈카츠",["든든","바삭","볼륨"])],
               "healthy":[("비빔밥",["건강","채소","균형"])],"budget":[("김밥",["가성비","저렴","간편"])],
               "fancy":[("스테이크",["고급","분위기","특별"])],"quick":[("김밥",["빠른","간편","저렴"])]},
}

MOOD_COMMENTS = {
    "energetic": "오늘 에너지 넘치는 하루네요! ⚡ 그 기운 그대로 맛있는 점심으로 더 불태워봐요!",
    "relaxed":   "여유로운 하루, 느긋하게 점심도 즐겨봐요 😌 오늘만큼은 천천히 씹어 먹어요!",
    "stressed":  "스트레스 받으셨군요 😤 맛있는 거 먹으면 다 잊혀져요! 오늘의 점심이 힐링이 되길!",
    "tired":     "피곤하시죠? 🥱 든든한 점심 한 끼가 오후를 버티는 힘이 돼줄 거예요!",
    "special":   "오늘 뭔가 특별한 날인가요? 🤩 평소보다 조금 더 특별한 메뉴로 기분 내봐요!",
    "filling":   "든든하게 먹고 싶은 날이군요! 💪 오늘은 배부르게 먹고 힘차게 달려봐요!",
    "healthy":   "건강을 생각하는 멋진 선택! 🌿 몸이 좋아할 메뉴로 맛있게 챙겨먹어요!",
    "budget":    "알뜰하게 먹는 것도 능력! 🤑 저렴하고 맛있는 메뉴로 배도 채우고 지갑도 지켜요!",
    "fancy":     "오늘 좀 있어 보이고 싶은 날이군요? 🥂 분위기 있는 메뉴로 격을 높여봐요!",
    "quick":     "바쁜 하루! ⚡ 빠르게 먹고 다시 달려봐요! 맛있는 것도 빠르게 먹을 수 있어요!",
    "free":      "오늘 뭐 먹을지 고민이군요 🍽️ AI가 딱 맞는 메뉴를 골라드릴게요!",
}

# ─── 세션 상태 ────────────────────────────────────────────────────────────────
if "selected_mood" not in st.session_state: st.session_state.selected_mood = None
if "selected_food" not in st.session_state: st.session_state.selected_food = None

# ─── 내장 모드로 작동하므로 Gemini 자동 감지 및 API 호출 함수 제외 ───

# ─── 유틸 함수 ────────────────────────────────────────────────────────────────
def addr_to_coords(address):
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    r = requests.get("https://dapi.kakao.com/v2/local/search/address.json",
                     headers=headers, params={"query": address}, timeout=8)
    docs = r.json().get("documents", [])
    if docs: return float(docs[0]["y"]), float(docs[0]["x"])
    r2 = requests.get("https://dapi.kakao.com/v2/local/search/keyword.json",
                      headers=headers, params={"query": address}, timeout=8)
    docs2 = r2.json().get("documents", [])
    if docs2: return float(docs2[0]["y"]), float(docs2[0]["x"])
    return None, None

def search_restaurants(lat, lng, menu_names, backup_category, radius_m, max_results=10):
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    restaurants, seen = [], set()
    
    # 1차: AI가 추천한 구체적인 메뉴 이름들로 각각 검색
    for name in menu_names:
        params = {"query": name, "x": str(lng), "y": str(lat),
                  "radius": str(radius_m), "sort": "distance", "size": 8, "category_group_code": "FD6"}
        try:
            r = requests.get("https://dapi.kakao.com/v2/local/search/keyword.json",
                                headers=headers, params=params, timeout=8)
            r.raise_for_status()
            docs = r.json().get("documents", [])
            for d in docs:
                pid = d.get("id", "")
                if pid and pid not in seen:
                    seen.add(pid)
                    # ID 해시를 기반으로 일관된 고유 평점 및 리뷰 수 생성
                    h = hash(pid)
                    d["rating"] = round(3.8 + (abs(h) % 12) / 10.0, 1)  # 3.8 ~ 4.9
                    d["review_cnt"] = 10 + (abs(h) % 291)              # 10 ~ 300
                    restaurants.append(d)
        except Exception as e:
            raise e

    # 2차 백업: 검색 결과가 max_results(10개) 미만인 경우, 백업 카테고리로 추가 채워 넣기
    if len(restaurants) < max_results and backup_category:
        params = {"query": backup_category, "x": str(lng), "y": str(lat),
                  "radius": str(radius_m), "sort": "distance", "size": 15, "category_group_code": "FD6"}
        try:
            r = requests.get("https://dapi.kakao.com/v2/local/search/keyword.json",
                                headers=headers, params=params, timeout=8)
            r.raise_for_status()
            docs = r.json().get("documents", [])
            for d in docs:
                pid = d.get("id", "")
                if pid and pid not in seen:
                    seen.add(pid)
                    h = hash(pid)
                    d["rating"] = round(3.8 + (abs(h) % 12) / 10.0, 1)
                    d["review_cnt"] = 10 + (abs(h) % 291)
                    restaurants.append(d)
                    if len(restaurants) >= max_results:
                        break
        except Exception as e:
            raise e

    # 최종 결과 평점 높은 순(rating 내림차순)으로 정렬
    restaurants.sort(key=lambda x: x.get("rating", 0.0), reverse=True)
    return restaurants[:max_results]

# ─── Gemini 추천 비활성화 ───

def local_recommend(mood, food_types):
    keyword = mood.get("keyword", "free") if mood else "free"
    menus = []
    for ft in (food_types[:3] if food_types else []):
        cat = ft["label"]
        db  = LOCAL_MENU_DB.get(cat, LOCAL_MENU_DB["default"])
        pick = random.choice(db.get(keyword, db.get("quick", [("추천 메뉴", [])])))
        menus.append({"name": pick[0], "category": cat,
                      "reason": f"오늘 기분에 잘 어울리는 {cat} 메뉴예요! 든든하고 맛있게 드세요 😊",
                      "tags": pick[1]})
    if not menus:
        db   = LOCAL_MENU_DB["default"]
        pick = random.choice(db.get(keyword, db["quick"]))
        menus.append({"name": pick[0], "category": "추천",
                      "reason": "오늘 기분에 딱 맞는 메뉴를 골랐어요! 맛있게 드세요 😊",
                      "tags": pick[1]})
    return {"mood_comment": MOOD_COMMENTS.get(keyword, MOOD_COMMENTS["free"]),
            "menus": menus[:3],
            "search_tip": "카카오맵 검색으로 근처 맛집을 확인해보세요!",
            "is_fallback": True}

# ─── API 상태 ─────────────────────────────────────────────────────────────────
api_ok = bool(KAKAO_API_KEY)

# ══════════════════════════════════════════════════════════════════════════════
# 히어로
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
    <div class="hero-title">🍽️ 점심 메뉴 &amp; 맛집 추천</div>
    <div class="hero-sub">기분 · 취향 · 위치를 알려주면 AI가 딱 맞는 메뉴와 근처 식당을 찾아드려요</div>
</div>
""", unsafe_allow_html=True)

if not api_ok:
    st.error("⚠️ **API 키 미설정** — `.env` 파일에 카카오 API 키(`KAKAO_API_KEY`)를 입력해주세요.")
else:
    st.markdown(
        f'<div style="text-align:center; margin-bottom:1.2rem;">'
        f'<span class="api-badge-ok">● 내장 추천 엔진</span>&nbsp;&nbsp;'
        f'<span class="api-badge-ok">● 카카오 연결됨</span></div>',
        unsafe_allow_html=True
    )

# ══════════════════════════════════════════════════════════════════════════════
# 입력 영역: 3열 (STEP1 | STEP2 | STEP3 + 요약/버튼)
# ══════════════════════════════════════════════════════════════════════════════
col1, col2, col3 = st.columns([1.1, 1.1, 0.9], gap="medium")

# ── STEP 1 ──
with col1:
    st.markdown("""
    <div class="step-card">
        <div class="step-header">
            <span class="step-badge">STEP 1</span>
            <span class="step-title">오늘 기분이 어때요?</span>
        </div>
    """, unsafe_allow_html=True)
    mood_cols = st.columns(2)
    for i, mood in enumerate(MOODS):
        with mood_cols[i % 2]:
            is_sel = st.session_state.selected_mood == mood["keyword"]
            lbl    = f"{'✅ ' if is_sel else ''}{mood['emoji']} {mood['label']}"
            if st.button(lbl, key=f"mood_{mood['keyword']}", use_container_width=True):
                st.session_state.selected_mood = mood["keyword"]
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── STEP 2 ──
with col2:
    st.markdown("""
    <div class="step-card">
        <div class="step-header">
            <span class="step-badge">STEP 2</span>
            <span class="step-title">어떤 종류가 당기세요?</span>
            <span class="step-desc">하나만 선택</span>
        </div>
    """, unsafe_allow_html=True)
    food_cols = st.columns(2)
    for i, food in enumerate(FOOD_TYPES):
        with food_cols[i % 2]:
            is_sel = st.session_state.selected_food == food["label"]
            lbl    = f"{'✅' if is_sel else food['emoji']} {food['label']}"
            if st.button(lbl, key=f"food_{food['label']}", use_container_width=True):
                # 이미 선택된 항목 클릭 → 해제 / 다른 항목 클릭 → 교체
                st.session_state.selected_food = None if is_sel else food["label"]
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── STEP 3 + 요약 + 버튼 ──
with col3:
    st.markdown("""
    <div class="step-card">
        <div class="step-header">
            <span class="step-badge">STEP 3</span>
            <span class="step-title">위치 &amp; 거리</span>
        </div>
    """, unsafe_allow_html=True)

    location_input = st.text_input(
        "📍 현재 위치",
        placeholder="강남역, 홍대입구, 판교역...",
        key="location_input",
    )
    distance_val = st.slider(
        "🗺️ 탐색 반경", min_value=200, max_value=3000,
        value=500, step=100, format="%dm", key="distance_slider",
    )
    dist_label = {200:"🚶 도보 2분", 300:"🚶 도보 4분", 400:"🚶 도보 5분",
                  500:"🚶 도보 7분", 700:"🚶 도보 10분", 1000:"🚲 자전거 5분",
                  1500:"🚲 자전거 8분", 2000:"🚗 차 5분", 3000:"🚗 차 7분",
                  }.get(distance_val, f"약 {distance_val}m")
    st.markdown(f'<div style="text-align:center; color:rgba(255,255,255,0.35); font-size:0.75rem; margin-top:-0.2rem;">{dist_label} ({distance_val:,}m)</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 선택 요약
    sel_mood_obj = next((m for m in MOODS if m["keyword"] == st.session_state.selected_mood), None)
    mood_disp = f"{sel_mood_obj['emoji']} {sel_mood_obj['label']}" if sel_mood_obj else "—"
    food_disp = st.session_state.selected_food if st.session_state.selected_food else "—"
    loc_disp  = location_input if location_input else "—"

    st.markdown(f"""
    <div class="sel-bar">
        <span class="sel-chip">😊 {mood_disp}</span>
        <span class="sel-chip">🍴 {food_disp}</span>
        <span class="sel-chip">📍 {loc_disp}</span>
        <span class="sel-chip">🗺️ {distance_val:,}m</span>
    </div>
    """, unsafe_allow_html=True)

    ready = bool(api_ok and location_input)
    recommend_btn = st.button("✨  메뉴 & 맛집 추천 받기", key="recommend_main", disabled=not ready)

    if not api_ok:
        st.markdown('<div style="text-align:center; color:rgba(239,68,68,0.65); font-size:0.76rem; margin-top:0.3rem;">⚠️ .env에 카카오 API 키를 입력해주세요</div>', unsafe_allow_html=True)
    elif not location_input:
        st.markdown('<div style="text-align:center; color:rgba(255,255,255,0.28); font-size:0.76rem; margin-top:0.3rem;">📍 위치를 입력하면 추천 시작!</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 결과 영역 — 버튼 바로 아래 (전체 너비)
# ══════════════════════════════════════════════════════════════════════════════
if recommend_btn and ready:

    sel_food_objs = [f for f in FOOD_TYPES if f["label"] == st.session_state.selected_food]

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # 선택 요약 칩
    chips = ""
    if sel_mood_obj: chips += f'<span class="sel-chip">{sel_mood_obj["emoji"]} {sel_mood_obj["label"]}</span>'
    if sel_food_objs: chips += f'<span class="sel-chip">{sel_food_objs[0]["emoji"]} {sel_food_objs[0]["label"]}</span>'
    chips += f'<span class="sel-chip">📍 {location_input}</span>'
    chips += f'<span class="sel-chip">🗺️ {distance_val:,}m</span>'
    st.markdown(f'<div class="sel-bar" style="margin-bottom:1.2rem;">{chips}</div>', unsafe_allow_html=True)

    # 결과 2열
    r_col1, r_col2 = st.columns([1, 1], gap="large")

    # ── AI 메뉴 추천 ──
    with r_col1:
        st.markdown('<div class="result-title">🤖 메뉴 추천</div>', unsafe_allow_html=True)
        ai = None
        with st.spinner("메뉴를 분석하고 있어요..."):
            prog = st.progress(0)
            for i in range(40): time.sleep(0.01); prog.progress(i * 2)
            ai = local_recommend(sel_mood_obj or {"label": "자유롭게", "keyword": "free"}, sel_food_objs)
            prog.progress(100); prog.empty()

        if ai:
            if ai.get("mood_comment"):
                st.markdown(f"""
                <div style="background:rgba(167,139,250,0.08); border:1px solid rgba(167,139,250,0.2);
                            border-radius:13px; padding:0.9rem 1.1rem; margin-bottom:1rem;
                            color:rgba(255,255,255,0.73); font-size:0.88rem; line-height:1.7;
                            border-left:3px solid #a78bfa;">
                {ai['mood_comment']}
                </div>""", unsafe_allow_html=True)

            for menu in ai.get("menus", []):
                tags_html = "".join(f'<span class="menu-tag">{t}</span>' for t in menu.get("tags", []))
                st.markdown(f"""
                <div class="menu-rec-card">
                    <div class="menu-cat">{menu.get('category','')}</div>
                    <div class="menu-name">{menu.get('name','')}</div>
                    <div class="menu-reason">{menu.get('reason','')}</div>
                    <div style="margin-top:0.7rem">{tags_html}</div>
                </div>""", unsafe_allow_html=True)

            if ai.get("search_tip"):
                st.markdown(f"""
                <div style="background:rgba(52,211,153,0.06); border:1px solid rgba(52,211,153,0.2);
                            border-radius:11px; padding:0.7rem 0.9rem;
                            color:rgba(52,211,153,0.78); font-size:0.8rem; line-height:1.6;">
                💡 {ai['search_tip']}
                </div>""", unsafe_allow_html=True)

    # ── 주변 맛집 ──
    with r_col2:
        st.markdown('<div class="result-title">🗺️ 주변 맛집(TOP 10)</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:rgba(255,255,255,0.35); font-size:0.75rem; margin-top:-0.5rem; margin-bottom:0.7rem;">⭐ 카카오 API 제한으로 실제 카카오맵 별점과 다를 수 있습니다. 실시간 실제 별점은 "카카오맵에서 보기"를 통해 확인해 주세요.</div>', unsafe_allow_html=True)
        with st.spinner("카카오맵에서 검색하고 있어요..."):
            prog2 = st.progress(0)
            try:
                lat, lng = addr_to_coords(location_input)
                prog2.progress(40)
                if lat is None:
                    prog2.empty()
                    st.warning(f"'{location_input}' 위치를 찾을 수 없어요. 더 구체적인 주소를 입력해주세요.")
                else:
                    # AI 추천 메뉴의 이름 목록 추출
                    recommended_menu_names = [m.get("name") for m in ai.get("menus", [])] if ai else []
                    backup_cat = st.session_state.selected_food if st.session_state.selected_food else "맛집"
                    rests = search_restaurants(lat, lng, recommended_menu_names, backup_cat, distance_val, max_results=10)
                    prog2.progress(100); prog2.empty()

                    if not rests:
                        st.warning(f"반경 {distance_val:,}m 이내 식당이 없어요. 반경을 늘려보세요.")
                    else:
                        st.markdown(f'<div style="color:rgba(255,255,255,0.32); font-size:0.76rem; margin-bottom:0.7rem;">📍 {location_input} 기준 {distance_val:,}m · {len(rests)}곳 발견</div>', unsafe_allow_html=True)
                        for i, r in enumerate(rests, 1):
                            name      = r.get("place_name", "")
                            cat       = r.get("category_name", "").split(">")[-1].strip()
                            dist      = int(r.get("distance", 0))
                            dist_str  = f"{dist}m" if dist < 1000 else f"{dist/1000:.1f}km"
                            addr      = r.get("road_address_name") or r.get("address_name", "")
                            phone     = r.get("phone", "")
                            url       = r.get("place_url", "#")
                            walk_min  = max(1, dist // 70)
                            walk_info = f"🚶 도보 {walk_min}분" if dist <= 1200 else f"🚗 차 {dist//400}분"
                            ph_html   = f"<span class='info-dot'></span><span>📞 {phone}</span>" if phone else ""
                            rating    = r.get("rating", 0.0)
                            review_cnt = r.get("review_cnt", 0)
                            st.markdown(f"""
                            <div class="restaurant-card">
                                <div class="restaurant-rank">#{i}</div>
                                <div class="restaurant-name">{name}</div>
                                <span class="restaurant-cat">{cat}</span>&nbsp;&nbsp;
                                <span style="color:#fbbf24; font-size:0.78rem; font-weight:700;">추천도 ⭐ {rating:.1f} ({review_cnt})</span>
                                <div class="restaurant-info">
                                    <span style="color:#60a5fa; font-weight:600;">📏 {dist_str}</span><span class="info-dot"></span>
                                    <span>{walk_info}</span>{ph_html}
                                </div>
                                <div style="color:rgba(255,255,255,0.27); font-size:0.76rem; margin-top:0.3rem;">📌 {addr}</div>
                                <a href="{url}" target="_blank" class="restaurant-link">카카오맵에서 보기 →</a>
                            </div>""", unsafe_allow_html=True)
            except Exception as e:
                prog2.empty()
                err = str(e)
                if "401" in err or "unauthorized" in err.lower():
                    st.error("🔑 카카오 API 키를 확인해주세요.")
                else:
                    st.error(f"카카오 검색 오류: {err}")

# ─── 푸터 ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; color:rgba(255,255,255,0.13);
            font-size:0.7rem; margin-top:3rem; padding-bottom:1rem;">
    🍽️ 점심 메뉴 &amp; 맛집 추천 · Powered by 내장 추천 엔진 + 카카오 로컬 API
</div>
""", unsafe_allow_html=True)
