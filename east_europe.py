import streamlit as st
import pandas as pd
import os
import urllib.parse
import plotly.express as px
from datetime import datetime
import pytz
import requests
import folium
from streamlit_folium import st_folium
import random
import json

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="Classic Europe 🍷", page_icon="🍷", layout="wide")

# 데이터 파일 경로
DATA_FILE = "europe_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"expenses": [], "total_budget": 5000000, "diary": [], "dark_mode": False}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"expenses": st.session_state.expenses, "total_budget": st.session_state.total_budget, "diary": st.session_state.diary, "dark_mode": st.session_state.dark_mode}, f, ensure_ascii=False, indent=4)

if 'initialized' not in st.session_state:
    saved_data = load_data()
    for k, v in saved_data.items(): st.session_state[k] = v
    if 'selected_day' not in st.session_state: st.session_state.selected_day = "6/7 (일) - 부다페스트"
    st.session_state.initialized = True

def toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode
    save_data()

# 유럽풍 테마 컬러 적용 (Burgundy & Deep Blue)
if st.session_state.dark_mode:
    page_bg = """
    <style>
    .stApp { background-color: #121212; color: #e0e0e0; font-family: "Georgia", serif; }
    .wave-header { background-color: #1e1e1e; border: 1px solid #333; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
    .wave-header h2 { color: #d4af37 !important; font-size: 28px !important; margin: 0; font-weight: 700; letter-spacing: 1px; }
    .wave-header p { color: #aaa; font-size: 14px; margin: 5px 0 0 0; }
    .card { background-color: #1e1e1e; color: #e0e0e0; border: 1px solid #444; border-left: 4px solid #d4af37; border-radius: 12px; padding: 22px; margin-bottom: 18px; }
    .weather-row { border-bottom: 1px solid #333; }
    .streamlit-expanderHeader { background-color: #1e1e1e !important; color: #d4af37 !important; border: 1px solid #333; border-radius: 8px; }
    div[data-testid="stPills"] { gap: 8px; }
    </style>"""
else:
    page_bg = """
    <style>
    .stApp { background: linear-gradient(180deg, #fafafa 0%, #f4f4f4 100%); font-family: "Georgia", serif; }
    .wave-header { background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); border: 1px solid #eaeaea; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.03); }
    .wave-header h2 { color: #5a3d2b !important; font-size: 28px !important; margin: 0; font-weight: 700; letter-spacing: 1px; }
    .wave-header p { color: #777; font-size: 14px; margin: 5px 0 0 0; }
    .card { background-color: white; padding: 22px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.03); border-left: 4px solid #5a3d2b; margin-bottom: 18px; }
    .sos-card { background-color: #fdfbfb; border: 1px solid #eee; padding: 15px; border-radius: 12px; color: #5a3d2b; }
    .streamlit-expanderHeader { font-weight: 700; color: #5a3d2b; background-color: white; border-radius: 8px; border: 1px solid #eee; }
    div[data-testid="stPills"] { gap: 8px; }
    </style>"""
st.markdown(page_bg, unsafe_allow_html=True)

# 2. API 함수들
@st.cache_data(ttl=3600)
def get_exchange_rates():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/KRW"
        data = requests.get(url).json()['rates']
        return {"EUR": 1/data['EUR'], "CZK": 1/data['CZK'], "HUF": 1/data['HUF']}
    except: return {"EUR": 1450.0, "CZK": 60.0, "HUF": 3.8}

@st.cache_data(ttl=3600)
def get_europe_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=Europe%2FBerlin&forecast_days=3"
        daily = requests.get(url).json()['daily']
        forecasts = []
        for i in range(3):
            code = daily['weathercode'][i]
            icon = "☀️" if code < 3 else "☁️" if code < 50 else "🌧️" if code < 80 else "☔"
            forecasts.append({"day": ["오늘", "내일", "모레"][i], "icon": icon, "max": round(daily['temperature_2m_max'][i]), "min": round(daily['temperature_2m_min'][i])})
        return forecasts
    except: return None

# 좌표 데이터
city_coords = {"부다페스트": (47.4979, 19.0402), "빈": (48.2082, 16.3738), "잘츠부르크": (47.8095, 13.0432), "프라하": (50.0755, 14.4378)}
d_day = (datetime(2026, 6, 7).date() - datetime.now(pytz.timezone('Asia/Seoul')).date()).days
rates = get_exchange_rates()

# 3. 사이드바
with st.sidebar:
    st.header("🎻 Trip Dashboard")
    st.toggle("🌙 Night Mode", value=st.session_state.dark_mode, on_change=toggle_theme)
    
    st.subheader("⛅ Euro Weather")
    sel_city = st.selectbox("도시 선택", list(city_coords.keys()))
    weather_3days = get_europe_weather(city_coords[sel_city][0], city_coords[sel_city][1])
    if weather_3days:
        st.markdown(f"""<div style="background:{'#1e1e1e' if st.session_state.dark_mode else 'white'}; padding:15px; border-radius:12px; border:1px solid #eee;">""", unsafe_allow_html=True)
        for w in weather_3days:
            st.markdown(f"""<div style="display:flex; justify-content:space-between; margin-bottom:5px;"><span>{w['day']}</span><span>{w['icon']}</span><span style="color:#e74c3c;">{w['max']}°</span></div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("💶 Currency Calc")
    currency = st.radio("화폐 선택", ["EUR (유로)", "CZK (코루나)", "HUF (포린트)"], horizontal=True)
    cur_code = currency.split(" ")[0]
    st.caption(f"1 {cur_code} ≈ {rates[cur_code]:.1f} KRW")
    
    f_input = st.number_input(f"금액 ({cur_code})", value=None, step=10, placeholder="금액 입력")
    if f_input: st.success(f"🇰🇷 약 {int(f_input * rates[cur_code]):,} 원")
    
    st.markdown("---")
    if d_day > 0: st.metric("D-Day", f"D-{d_day}", "유럽의 낭만 속으로!")
    else: st.metric("D-Day", f"D+{abs(d_day)}", "여행 중")
    
    st.markdown("---")
    st.subheader("🎵 Classic Vibe")
    st.video("https://www.youtube.com/embed/videoseries?list=PLW21PjM_K34qQyQh-GkMvL59z1F5s4w-d")

# 4. 헤더
st.markdown(f"""<div class="wave-header"><h2>Classic Europe ✨</h2><p>A Timeless Journey for Chris.</p></div>""", unsafe_allow_html=True)

# 5. 데이터
def get_map_url(place): return f"https://www.google.com/maps/search/{urllib.parse.quote(place)}"

itinerary_data = [
    ["6/7 (일) - 부다페스트", "18:05", "도착", "부다페스트 공항", "공항 도착 및 숙소 이동", "공항 도착 및 이동"],
    ["6/7 (일) - 부다페스트", "19:30", "숙소", "호텔 체크인", "호텔 체크인 및 짐 보관", "호텔 체크인 및 짐 보관"],
    ["6/7 (일) - 부다페스트", "20:30", "석식", "맥도날드", "[저녁] 파인다이닝 (1)", "구시가지 산책 및 첫 파인다이닝 디너"],
    
    ["6/8 (월) - 부다페스트", "07:00", "운동", "웨이트 트레이닝", "호텔 헬스장 또는 근처 피트니스", "아침 운동으로 상쾌하게 시작"],
    ["6/8 (월) - 부다페스트", "10:00", "관광", "국회의사당, 다뉴브 강가의 신발들", "", ""],
    ["6/8 (월) - 부다페스트", "10:30", "관광", "성 이슈트반 대성당", "성 이슈트반 대성당", "[명소 2] 성 이슈트반 대성당"],
    ["6/8 (월) - 부다페스트", "12:00", "관광", "엘리자베스광장", "", ""],
    ["6/8 (월) - 부다페스트", "12:30", "중식", "점심 식사", "[점심] 고급 레스토랑 (2)", "고급 식당에서 런치"],
    ["6/8 (월) - 부다페스트", "14:00", "관광", "세체니 다리", "", ""],
    ["6/8 (월) - 부다페스트", "15:00", "관광", "Buda Castle Funicular", "", ""],
    ["6/8 (월) - 부다페스트", "16:00", "관광", "부다 왕궁", "[명소 1] 부다 왕궁", "부다페스트의 상징적인 왕궁 탐방"],
    ["6/8 (월) - 부다페스트", "17:00", "휴식", "숙소 휴식 (1시간)", "", ""],
    ["6/8 (월) - 부다페스트", "19:00", "석식", "저녁 식사", "[저녁] 고급 레스토랑 (3)", "야경 감상 후 고급 다이닝"],
    
    ["6/9 (화) - 부다페스트", "07:00", "운동", "웨이트 트레이닝", "오운완", ""],
    ["6/9 (화) - 부다페스트", "09:00", "관광", "세체니 온천", "[명소 1] 피로 회복", "유럽 최대 규모의 온천에서 힐링"],
    ["6/9 (화) - 부다페스트", "11:00", "관광", "버이더후녀드 성/회쇠크 광장", "", ""],
    ["6/9 (화) - 부다페스트", "11:30", "관광", "Kodály körönd", "", ""],
    ["6/9 (화) - 부다페스트", "12:00", "중식", "점심 식사", "[점심] 고급 레스토랑 (4)", "안드라시 거리에서 식사"],
    ["6/9 (화) - 부다페스트", "13:00", "휴식", "숙소 휴식 (1시간)", "오후 재정비", ""],
    ["6/9 (화) - 부다페스트", "14:00", "관광", "Váci u", "", ""],
    ["6/9 (화) - 부다페스트", "15:00", "관광", "그레이트 마켓홀", "", ""],
    ["6/9 (화) - 부다페스트", "17:00", "관광", "겔레르트 언덕", "[명소 3] 겔레르트 언덕", "일몰 및 야경 감상 포인트"],
    ["6/9 (화) - 부다페스트", "18:30", "석식", "저녁 식사", "일반 로컬 식당", "현지 분위기 물씬 나는 로컬 맛집 탐방"],
    ["6/9 (화) - 부다페스트", "20:00", "관광", "어부의 요새", "[명소 2] 어부의 요새", "도나우 강과 페스트 지구가 한눈에 보이는 명소"],
    ["6/9 (화) - 부다페스트", "20:30", "관광", "다뉴브강 크루즈", "[명소 3] 국회의사당 야경", "로맨틱한 다뉴브강 야경 크루즈"],
    
    ["6/10 (수) - 빈", "07:00", "운동", "웨이트 트레이닝", "오운완", ""],
    ["6/10 (수) - 빈", "09:30", "이동", "기차 이동", "부다페스트 -> 빈", "약 2시간 30분 소요 편안한 기차 여행"],
    ["6/10 (수) - 빈", "12:00", "숙소", "빈 호텔 체크인", "짐 보관", ""],
    ["6/10 (수) - 빈", "12:30", "중식", "점심 식사", "[점심] 파인다이닝 (5)", "음악의 도시 빈 입성 기념 파인다이닝"],
    ["6/10 (수) - 빈", "13:30", "관광", "페스트조일레", "", ""],
    ["6/10 (수) - 빈", "15:00", "숙소", "빈 호텔 체크인", "", ""],
    ["6/10 (수) - 빈", "16:00", "관광", "슈테판 대성당", "[명소 1] 슈테판 대성당", "이동일로 오후 휴식 생략"],
    ["6/10 (수) - 빈", "17:00", "관광", "호프부르크 왕궁", "[명소 2] 호프부르크 왕궁", "합스부르크 왕가의 겨울 궁전 외관 및 주변 산책"],
    ["6/10 (수) - 빈", "19:00", "석식", "저녁 식사", "[저녁] 고급 레스토랑 (6)", "빈의 낭만적인 저녁 다이닝"],
    
    ["6/11 (목) - 빈", "07:00", "운동", "웨이트 트레이닝", "오운완", ""],
    ["6/11 (목) - 빈", "09:30", "관광", "쇤브룬 궁전", "[명소 1] 내부 및 정원", "여름 궁전과 아름다운 정원 산책"],
    ["6/11 (목) - 빈", "13:00", "중식", "점심 식사", "일반 로컬 식당", "현지식 즐기기"],
    ["6/11 (목) - 빈", "15:00", "휴식", "숙소 휴식 (1시간)", "재정비", ""],
    ["6/11 (목) - 빈", "16:30", "관광", "벨베데레 궁전", "[명소 2] 클림트 작품 감상", "'키스'를 비롯한 명작 감상"],
    ["6/11 (목) - 빈", "19:00", "석식", "저녁 식사", "[저녁] 고급 레스토랑 (7)", "예술적인 하루를 마무리하는 다이닝"],
    
    ["6/12 (금) - 빈", "07:00", "운동", "웨이트 트레이닝", "오운완", ""],
    ["6/12 (금) - 빈", "10:00", "관광", "빈 미술사 박물관", "[명소 1] 빈 미술사 박물관", "세계적인 미술품 전시 관람"],
    ["6/12 (금) - 빈", "13:00", "중식", "점심 식사", "[점심] 고급 레스토랑 (8)", "미술관 관람 후 여유로운 오찬"],
    ["6/12 (금) - 빈", "15:00", "휴식", "숙소 휴식 (1시간)", "야간 공연을 위한 체력 비축", ""],
    ["6/12 (금) - 빈", "16:30", "휴식", "전통 카페 휴식", "카페 자허 또는 데멜", "빈의 정통 커피와 디저트 타임"],
    ["6/12 (금) - 빈", "18:00", "석식", "저녁 식사", "[저녁] 파인다이닝 (9)", "공연 전 훌륭한 저녁 식사"],
    ["6/12 (금) - 빈", "20:00", "관광", "국립 오페라 극장", "[명소 2] 오페라 또는 클래식 공연 직관", "클래식의 본고장에서 공연 관람"],
    
    ["6/13 (토) - 잘츠부르크", "07:00", "운동", "웨이트 트레이닝", "오운완", ""],
    ["6/13 (토) - 잘츠부르크", "09:30", "이동", "기차 이동", "빈 -> 잘츠부르크", "약 2시간 30분 소요"],
    ["6/13 (토) - 잘츠부르크", "12:30", "숙소", "잘츠부르크 호텔 체크인", "짐 보관", ""],
    ["6/13 (토) - 잘츠부르크", "13:30", "중식", "점심 식사", "일반 로컬 식당", "잘츠부르크 도착 첫 식사"],
    ["6/13 (토) - 잘츠부르크", "15:00", "관광", "미라벨 정원", "[명소 1] 미라벨 정원", "이동일로 오후 휴식 생략"],
    ["6/13 (토) - 잘츠부르크", "16:30", "관광", "모차르트 생가", "[명소 2] 게트라이데 거리", "거리 쇼핑 및 모차르트 생가 방문"],
    ["6/13 (토) - 잘츠부르크", "19:00", "석식", "저녁 식사", "[저녁] 고급 레스토랑 (10)", "고급 디너"],
    
    ["6/14 (일) - 할슈타트(근교)", "07:00", "운동", "웨이트 트레이닝", "오운완", ""],
    ["6/14 (일) - 할슈타트(근교)", "09:00", "이동", "할슈타트 당일치기", "숙소 휴식 제외", "동화 같은 호수 마을 투어 출발"],
    ["6/14 (일) - 할슈타트(근교)", "11:30", "관광", "할슈타트 호수 마을", "[명소 1] 할슈타트 호수 마을", "자연 경관이 어우러진 산책"],
    ["6/14 (일) - 할슈타트(근교)", "13:00", "중식", "점심 식사", "일반 로컬 식당", "아름다운 호수를 보며 점심"],
    ["6/14 (일) - 할슈타트(근교)", "14:30", "관광", "파이브 핑거스 전망대", "[명소 2] 알프스 만년설 조망", "알프스 뷰 감상"],
    ["6/14 (일) - 할슈타트(근교)", "18:30", "이동", "잘츠부르크 복귀", "이동", ""],
    ["6/14 (일) - 할슈타트(근교)", "19:30", "석식", "저녁 식사", "[저녁] 고급 레스토랑 (13)", "수고한 하루를 보상하는 고급 만찬"],
    
    ["6/15 (월) - 잘츠부르크", "07:00", "운동", "웨이트 트레이닝", "오운완", ""],
    ["6/15 (월) - 잘츠부르크", "10:00", "관광", "호엔잘츠부르크 성", "[명소 1] 푸니쿨라 탑승", "성곽에 올라 시내 조망"],
    ["6/15 (월) - 잘츠부르크", "13:00", "중식", "점심 식사", "[점심] 고급 레스토랑 (11)", "성벽 관람 후 고급 런치"],
    ["6/15 (월) - 잘츠부르크", "15:00", "휴식", "숙소 휴식 (1시간)", "재정비", ""],
    ["6/15 (월) - 잘츠부르크", "16:30", "관광", "묀히스베르크 전망대", "[명소 2] 시내 전경 감상", "잘츠부르크 최고의 파노라마 뷰"],
    ["6/15 (월) - 잘츠부르크", "19:00", "석식", "저녁 식사", "[저녁] 파인다이닝 (12)", "로맨틱한 잘츠부르크 야경과 식사"],
    
    ["6/16 (화) - 프라하", "07:00", "운동", "웨이트 트레이닝", "오운완", ""],
    ["6/16 (화) - 프라하", "09:00", "이동", "기차 이동", "잘츠부르크 -> 프라하", "약 5시간 30분 소요 (린츠 환승)"],
    ["6/16 (화) - 프라하", "15:00", "숙소", "프라하 호텔 체크인", "이동일로 휴식 시간 대체", "체코 프라하 입성 및 짐 풀기"],
    ["6/16 (화) - 프라하", "16:00", "관광", "화약탑", "", ""],
    ["6/16 (화) - 프라하", "17:00", "관광", "하벨시장", "", ""],
    ["6/16 (화) - 프라하", "18:00", "관광", "프라하천문시계", "", ""],
    ["6/16 (화) - 프라하", "19:00", "석식", "저녁 식사", "[저녁] 고급 레스토랑 (14)", "카를교 인근 다이닝"],
    ["6/16 (화) - 프라하", "20:00", "관광", "구시가지 광장 야경", "[명소 2] 구시가지 광장 야경", "광장 야경 감상"],
    
    ["6/17 (수) - 프라하", "07:00", "운동", "웨이트 트레이닝", "오운완", ""],
    ["6/17 (수) - 프라하", "09:00", "관광", "카를교", "[명소 1] 도보 횡단", "프라하 낭만의 중심지 산책"],
    ["6/17 (수) - 프라하", "10:00", "관광", "프라하 성", "[명소 1] 성 비투스 대성당 포함", "프라하의 상징 탐방"],
    ["6/17 (수) - 프라하", "13:00", "중식", "점심 식사", "[점심] 고급 레스토랑 (15)", "프라하 성 관람 후 고급 런치"],
    ["6/17 (수) - 프라하", "15:00", "휴식", "발트슈타인 궁전", "", ""],
    ["6/17 (수) - 프라하", "16:30", "관광", "천문 시계탑", "[명소 2] 천문 시계탑", "정각 쇼 관람"],
    ["6/17 (수) - 프라하", "19:00", "석식", "저녁 식사", "일반 로컬 식당", "체코 전통 음식 즐기기"],
    
    ["6/18 (목) - 체스키(근교)", "07:00", "운동", "웨이트 트레이닝", "오운완", ""],
    ["6/18 (목) - 체스키(근교)", "09:00", "이동", "체스키 크룸로프 투어", "숙소 휴식 제외", "동화 같은 중세 마을 투어 출발"],
    ["6/18 (목) - 체스키(근교)", "11:30", "관광", "체스키 크룸로프 성", "[명소 1] 체스키 크룸로프 성", "마을을 내려다보는 붉은 지붕 관람"],
    ["6/18 (목) - 체스키(근교)", "13:00", "중식", "점심 식사", "[점심] 파인다이닝 (16)", "파인다이닝"],
    ["6/18 (목) - 체스키(근교)", "14:30", "관광", "이발사의 다리 및 구시가지", "[명소 2] 이발사의 다리 및 구시가지", "아기자기한 중세 골목 산책"],
    ["6/18 (목) - 체스키(근교)", "18:30", "이동", "프라하 복귀", "이동", ""],
    ["6/18 (목) - 체스키(근교)", "19:30", "석식", "저녁 식사", "[저녁] 고급 레스토랑 (17)", "프라하 도착 후 여유로운 디너"],
    
    ["6/19 (금) - 프라하", "07:00", "운동", "웨이트 트레이닝", "오운완", ""],
    ["6/19 (금) - 프라하", "10:00", "관광", "Rozhledna v Kasárnách Karlín", "", ""],
    ["6/19 (금) - 프라하", "12:30", "중식", "점심 식사", "일반 로컬 식당", "로컬 맛집 탐방"],
    ["6/19 (금) - 프라하", "15:00", "휴식", "숙소 휴식 (1시간)", "재정비", ""],
    ["6/19 (금) - 프라하", "17:00", "관광", "구시가광장", "", ""],
    ["6/19 (금) - 프라하", "18:00", "석식", "저녁 식사", "[저녁] 미슐랭/파인다이닝 (18)", "프라하 여행의 하이라이트 디너"],
    ["6/19 (금) - 프라하", "20:00", "관광", "블타바 강 페달 보트", "[명소 2] 액티비티", "강 위에서 여유로운 오후 즐기기"],
    
    ["6/20 (토) - 프라하", "07:00", "운동", "웨이트 트레이닝", "마지막 오운완", "마지막 헬스 루틴"],
    ["6/20 (토) - 프라하", "10:00", "관광", "바츨라프 광장", "[명소 1] 바츨라프 광장", "프라하의 역사적인 중심지"],
    ["6/20 (토) - 프라하", "12:30", "중식", "점심 식사", "[점심] 고급 레스토랑 (19)", "유럽 여행 19번째 다이닝 대미 장식"],
    ["6/20 (토) - 프라하", "14:00", "쇼핑", "기념품 및 마트 쇼핑", "귀국 전 쇼핑", "지인 선물 구매"],
    ["6/20 (토) - 프라하", "15:30", "이동", "공항으로 이동", "이동", "바츨라프 하벨 공항으로 이동"],
    ["6/20 (토) - 프라하", "19:05", "이동", "비행기 탑승 및 귀국", "총 19회의 고급 다이닝 달성", "아쉬움을 뒤로하고 한국으로 출발"]
]
df_itinerary = pd.DataFrame(itinerary_data, columns=["날짜", "시간", "구분", "장소", "요약", "설명"])

# 6. 탭 구성
tab0, tab_map, tab1, tab_reservation, tab2, tab_local_picks, tab3, tab4, tab5 = st.tabs([
    "🏛️ Overview", "🗺️ Map", "📅 Itinerary", "🛎️ Reservations", 
    "💎 Secret Spots", "🛍️ Local Picks", "🎭 Experiences", "🎒 Travel Kit", "💰 Wallet"
])

with tab0:
    st.markdown("### Trip Overview")
    df_themes = pd.DataFrame([
        ["부다페스트", "6/7 - 6/10", "다뉴브 강의 진주", "야경 크루즈, 미슐랭 다이닝, 뉴욕 카페"],
        ["오스트리아 빈", "6/10 - 6/13", "클래식과 럭셔리", "콜마르크트 명품 쇼핑, 호프부르크, 콘서트"],
        ["잘츠부르크", "6/13 - 6/16", "음악과 자연", "모차르트 디너, 미라벨 궁전, 할슈타트(당일치기)"],
        ["프라하", "6/16 - 6/20", "보헤미안 낭만", "파르지주스카 쇼핑, 카를교, 프라하 성"]
    ], columns=["국가/도시", "일정", "테마", "포인트"])
    st.table(df_themes.set_index("국가/도시"))
    
    st.markdown("#### 📝 One-Line Diary")
    with st.form("diary_form", clear_on_submit=True):
        note = st.text_input("오늘 여행에서 가장 기억에 남는 순간은?")
        if st.form_submit_button("기록 (Save)") and note:
            st.session_state.diary.append(f"[{datetime.now(pytz.timezone('Europe/Berlin')).strftime('%m/%d %H:%M')}] {note}")
            save_data()
            st.rerun()
            
    if st.session_state.diary:
        for i, entry in enumerate(st.session_state.diary):
            c1, c2 = st.columns([0.9, 0.1])
            c1.text(entry)
            if c2.button("🗑️", key=f"del_diary_{i}"):
                st.session_state.diary.pop(i)
                save_data()
                st.rerun()

with tab_map:
    st.markdown("### 🗺️ Euro Route Map")
    m = folium.Map(location=[48.2, 16.3], zoom_start=6)
    for city, coords in city_coords.items():
        folium.Marker(coords, popup=city, tooltip=city, icon=folium.Icon(color="red", icon="star")).add_to(m)
    folium.PolyLine([city_coords["부다페스트"], city_coords["빈"], city_coords["잘츠부르크"], city_coords["프라하"]], color="blue", weight=2.5, opacity=0.8).add_to(m)
    st_folium(m, width=700, height=400)

with tab1:
    days = df_itinerary['날짜'].unique()
    selection = st.pills("Select Day", days, selection_mode="single", default=st.session_state.selected_day, label_visibility="collapsed")
    if selection: st.session_state.selected_day = selection

    st.markdown(f"##### {st.session_state.selected_day} Schedule")
    for _, r in df_itinerary[df_itinerary['날짜'] == st.session_state.selected_day].iterrows():
        with st.expander(f"⏰ {r['시간']} | {r['장소']} ({r['구분']})"):
            if r['요약']:
                st.markdown(f"**💡 {r['요약']}**")
            if r['설명']:
                st.write(r['설명'])
            st.link_button(f"📍 구글 지도 연결", get_map_url(f"{r['장소']} 유럽"))

with tab_reservation:
    st.markdown("### 🛎️ Must-Reserve List")
    st.caption("※ 인기 다이닝 및 명소, 국가 간 기차는 조기 매진되므로 사전 예약이 필수입니다. 일정 및 날짜순으로 정리되었습니다.")

    st.markdown("#### 🇭🇺 6/7 (일) ~ 6/10 (수) : 부다페스트")
    st.markdown("""
    * **🍽️ 파인다이닝 예약 (Costes / Comme Chez Soi)**
      * [Costes (미슐랭 1스타) 예약](https://costes.hu/en/)
      * [Comme Chez Soi (인기 이탈리안) 예약](https://www.commechezsoi.hu/)
    * **🛳️ 6/9 (화) 다뉴브강 야경 크루즈**
      * [Legenda 야경 크루즈 예약](https://legenda.hu/en)
    * **🚆 6/10 (수) 기차 이동 (부다페스트 → 빈)**
      * [ÖBB (오스트리아 철도청) 예매](https://www.oebb.at/en/) (좌석 지정 필수)
    """)

    st.markdown("#### 🇦🇹 6/10 (수) ~ 6/13 (토) : 빈")
    st.markdown("""
    * **🍽️ 주요 다이닝 (Figlmüller / Plachutta)**
      * [Figlmüller (슈니첼) 예약](https://figlmueller.at/en/)
      * [Plachutta (타펠슈피츠) 예약](https://www.plachutta.at/en/)
    * **🏛️ 6/11 (목) 쇤브룬 궁전 & 벨베데레 궁전**
      * [쇤브룬 궁전 공식 예매](https://www.schoenbrunn.at/en/)
      * [벨베데레 궁전 상궁 (클림트) 예매](https://www.belvedere.at/en)
    * **🎭 6/12 (금) 빈 국립 오페라 극장 공연**
      * [오페라 극장 공식 예매](https://www.wiener-staatsoper.at/en/)
    * **🚆 6/13 (토) 기차 이동 (빈 → 잘츠부르크)**
      * [ÖBB 예매](https://www.oebb.at/en/) 또는 [Westbahn 예매](https://westbahn.at/en/)
    """)

    st.markdown("#### 🇦🇹 6/13 (토) ~ 6/16 (화) : 잘츠부르크")
    st.markdown("""
    * **🍽️ 6/15 (월) St. Peter Stiftskulinarium**
      * [모차르트 디너 콘서트 예약](https://www.stpeter.at/en/)
    * **🚆 6/16 (화) 기차 이동 (잘츠부르크 → 프라하)**
      * [ÖBB 예매 (린츠 환승 편)](https://www.oebb.at/en/)
    """)

    st.markdown("#### 🇨🇿 6/16 (화) ~ 6/20 (토) : 프라하 & 체스키")
    st.markdown("""
    * **🍽️ 인기 레스토랑 (Terasa U Zlaté studně / Pork's)**
      * [Terasa U Zlaté studně (뷰 맛집 파인다이닝) 예약](https://www.terasauzlatestudne.cz/en/)
      * [Pork's (꼴레뇨 로컬 맛집) 예약](https://www.porks.cz/en/)
    * **🚌 6/18 (목) 체스키 크룸로프 왕복 이동**
      * [RegioJet 왕복 버스 예매](https://regiojet.com/) (개별 이동 시 필수)
    """)

with tab2: 
    st.markdown("### 💎 The Hidden Gems & Top Dining")
    st.caption("※ 모든 레스토랑은 구글 평점 4.5 이상의 검증된 맛집이며, 고급 다이닝의 경우 사전 예약이 필수입니다.")
    
    city_tabs = st.tabs(["🇭🇺 부다페스트", "🇦🇹 빈", "🇦🇹 잘츠부르크", "🇨🇿 프라하"])
    
    with city_tabs[0]:
        st.markdown("#### 🍽️ Must-Eat Restaurants (부다페스트)")
        st.markdown(f"""
        1. **[Costes (코스테스)]({get_map_url('Costes Restaurant Budapest')})**: (★4.7) 헝가리 최초의 미슐랭 1스타. 완벽한 서비스와 예술적인 플레이팅을 자랑하는 파인다이닝.
        2. **[Menza (멘자)]({get_map_url('Menza Budapest')})**: (★4.5) 부다페스트 굴라쉬(Goulash) 1대장. 오리 가슴살 스테이크도 훌륭한 레트로풍 레스토랑.
        3. **[Comme Chez Soi (꼼 셰 수아)]({get_map_url('Comme Chez Soi Budapest')})**: (★4.8) 사과를 곁들인 푸아그라 요리가 환상적인 이탈리안 베이스 식당. (예약 필수)
        4. **[Borkonyha Winekitchen]({get_map_url('Borkonyha Winekitchen Budapest')})**: (★4.7) 와인 페어링이 기가 막힌 미슐랭 1스타. 혁신적인 헝가리 요리를 선보임.
        """)
        st.markdown("#### 📸 Secret Viewpoints")
        st.markdown(f"""
        * **[Gellért Baths (겔레르트 온천)]({get_map_url('Gellert Baths')})**: 세체니가 너무 붐빈다면 추천. 화려한 아르누보 양식의 타일 장식이 돋보이는 럭셔리 온천.
        * **[Szimpla Kert (심플라 케르트)]({get_map_url('Szimpla Kert')})**: 오래된 건물을 개조한 부다페스트 특유의 '폐허 펍(Ruin Pub)'. 독특한 예술적 바이브가 넘치는 곳.
        """)
        
    with city_tabs[1]:
        st.markdown("#### 🍽️ Must-Eat Restaurants (빈)")
        st.markdown(f"""
        1. **[Figlmüller (피글뮐러)]({get_map_url('Figlmuller Vienna')})**: (★4.5) 100년 전통의 슈니첼 명가. 얼굴보다 큰 바삭한 돈가스 형태의 전통 요리.
        2. **[Plachutta (플라후타)]({get_map_url('Plachutta Wollzeile')})**: (★4.6) 오스트리아식 소고기 수육 '타펠슈피츠(Tafelspitz)'의 최고봉. 정갈하고 고급스러운 서비스.
        3. **[Salm Bräu (살름 브로이)]({get_map_url('Salm Brau Vienna')})**: (★4.5) 벨베데레 궁전 근처. 직접 양조한 크래프트 맥주와 부드러운 폭립이 일품.
        4. **[Café Central (카페 센트랄)]({get_map_url('Cafe Central Vienna')})**: (★4.5) 프로이트, 트로츠키가 단골이던 가장 화려한 전통 카페. 아인슈패너와 디저트.
        """)
        st.markdown("#### 📸 Secret Viewpoints")
        st.markdown(f"""
        * **[Hundertwasserhaus (훈데르트바서 하우스)]({get_map_url('Hundertwasserhaus')})**: 자연과 곡선을 사랑한 천재 건축가 훈데르트바서가 디자인한 독특하고 다채로운 색감의 공공 주택.
        * **[콜마르크트 거리 (Kohlmarkt)]({get_map_url('Kohlmarkt Vienna')})**: 오스트리아 최고의 명품 거리. 톰브라운, 구찌 등 부티크 밀집 지역. 텍스 리펀 필수!
        """)

    with city_tabs[2]:
        st.markdown("#### 🍽️ Must-Eat Restaurants (잘츠부르크)")
        st.markdown(f"""
        1. **[St. Peter Stiftskulinarium]({get_map_url('St. Peter Stiftskulinarium')})**: (★4.6) 유럽에서 가장 오래된(1200년) 레스토랑. 촛불 아래서 모차르트 음악과 함께하는 디너 코스.
        2. **[Bärenwirt (베렌비르트)]({get_map_url('Barenwirt Salzburg')})**: (★4.6) 오스트리아식 프라이드 치킨인 '백핸들(Backhendl)'이 가장 맛있는 전통 로컬 맛집.
        3. **[Augustiner Bräu (아우구스티너 맥주)]({get_map_url('Augustiner Brau Salzburg')})**: (★4.7) 거대한 수도원 맥주 공장. 직접 잔을 씻어 맥주를 받고, 푸드 코트에서 안주를 골라 먹는 축제 같은 분위기.
        """)
        st.markdown("#### 📸 Secret Viewpoints")
        st.markdown(f"""
        * **[Untersberg (운터스베르크)]({get_map_url('Untersbergbahn')})**: 케이블카를 타고 올라가는 알프스 산맥의 초입. 잘츠부르크 시내와 만년설을 동시에 볼 수 있는 압도적 뷰.
        * **[Mönchsberg Lift (묀히스베르크 엘리베이터)]({get_map_url('Monchsbergaufzug')})**: 엘리베이터를 타고 단숨에 절벽 위로 올라가, 호엔잘츠부르크 성을 가장 예쁜 구도로 찍을 수 있는 스팟.
        """)

    with city_tabs[3]:
        st.markdown("#### 🍽️ Must-Eat Restaurants (프라하)")
        st.markdown(f"""
        1. **[Pork's (포크스)]({get_map_url('Porks Prague')})**: (★4.7) 겉바속촉 체코 전통 족발 '꼴레뇨(Koleno)'의 절대 강자. 카를교 근처 위치.
        2. **[Kantýna (칸티나)]({get_map_url('Kantyna Prague')})**: (★4.6) 프리미엄 정육 식당 스타일. 최고급 체코 소고기 카르파치오와 신선한 생맥주를 입식 테이블에서 즐기는 힙한 공간.
        3. **[Terasa U Zlaté studně]({get_map_url('Terasa U Zlate studne')})**: (★4.8) 블타바 강과 프라하 성이 한눈에 내려다보이는 뷰 맛집 파인다이닝. 프러포즈 명소로 유명.
        4. **[Café Savoy (카페 사보이)]({get_map_url('Cafe Savoy Prague')})**: (★4.5) 19세기 말 아름다운 네오 르네상스 천장 아래서 즐기는 고품격 브런치와 핫초코.
        """)
        st.markdown("#### 📸 Secret Viewpoints")
        st.markdown(f"""
        * **[Vrtbovská zahrada (브르트바 정원)]({get_map_url('Vrtba Garden')})**: 카를교 인근에 숨겨진 계단식 바로크 양식 정원. 번잡한 프라하 시내에서 조용히 인생샷을 남길 수 있는 곳.
        * **[Letná Park (레트나 공원)]({get_map_url('Letna Park')})**: 블타바 강을 가로지르는 여러 개의 다리를 일렬로 내려다볼 수 있는 최고의 일몰 및 뷰포인트.
        """)

with tab_local_picks:
    st.markdown("### 🛍️ Must-Eat & Must-Buy")
    st.caption("각 도시에서 반드시 맛보아야 할 고유 음식과 기념품 리스트입니다.")
    
    local_tabs = st.tabs(["🇭🇺 부다페스트", "🇦🇹 빈", "🇦🇹 잘츠부르크", "🇨🇿 프라하"])
    
    with local_tabs[0]:
        st.markdown("#### 🍲 Must-Eat (고유 음식)")
        st.markdown("""
        * **굴라쉬 (Gulyás):** 한국의 육개장과 비슷한 얼큰한 소고기 야채 수프. 한국인 입맛에 가장 잘 맞습니다.
        * **랑고쉬 (Lángos):** 튀긴 빵 위에 마늘소스, 사워크림, 치즈를 듬뿍 올린 길거리 간식.
        * **굴뚝빵 (Kürtőskalács):** 숯불에 구워 겉은 바삭하고 속은 촉촉한 헝가리 전통 빵.
        """)
        st.markdown("#### 🎁 Must-Buy (특산물)")
        st.markdown("""
        * **파프리카 가루:** 헝가리 요리의 핵심. 매운맛(Csípős)과 단맛(Édes)이 있으며 튜브형 페이스트도 추천합니다.
        * **토카이 아수 (Tokaji Aszú):** 세계 3대 디저트 와인. 푸토뇨쉬(Puttonyos) 숫자가 5 이상인 것을 추천합니다.
        """)

    with local_tabs[1]:
        st.markdown("#### 🍲 Must-Eat (고유 음식)")
        st.markdown("""
        * **슈니첼 (Schnitzel):** 송아지 고기를 얇게 펴서 튀긴 오스트리아식 돈가스. 크랜베리 잼을 곁들여 먹습니다.
        * **타펠슈피츠 (Tafelspitz):** 맑은 육수에 삶아낸 소고기 수육 요리로 프란츠 요제프 황제가 즐겨 먹은 것으로 유명합니다.
        * **자허토르테 (Sachertorte):** 진한 초콜릿 스펀지 케이크에 살구 잼을 바른 빈의 대표 디저트.
        """)
        st.markdown("#### 🎁 Must-Buy (특산물)")
        st.markdown("""
        * **마너 (Manner) 웨하스:** 빈 여행객의 국민 간식. 분홍색 패키지가 상징적입니다.
        * **모차르트 쿠겔 초콜릿 (Mirabell 등):** 피스타치오 마지팬이 들어간 초콜릿. 슈퍼마켓에서 쉽게 구매 가능합니다.
        """)

    with local_tabs[2]:
        st.markdown("#### 🍲 Must-Eat (고유 음식)")
        st.markdown("""
        * **보스나 (Bosna):** 카레 가루와 양파, 머스타드를 듬뿍 넣은 잘츠부르크 스타일의 소시지 핫도그.
        * **잘츠부르거 녹켈른 (Salzburger Nockerl):** 알프스 산맥을 형상화한 거대하고 부드러운 머랭 디저트.
        """)
        st.markdown("#### 🎁 Must-Buy (특산물)")
        st.markdown("""
        * **오리지널 모차르트 초콜릿 (Fürst):** 파란색/은색 포장지로 된 '퓌르스트' 카페의 수제 모차르트 초콜릿(원조).
        * **소금 (Salz):** 잘츠부르크('소금성'이라는 뜻) 지역의 특산물로, 다양한 허브가 섞인 암염이 인기입니다.
        """)

    with local_tabs[3]:
        st.markdown("#### 🍲 Must-Eat (고유 음식)")
        st.markdown("""
        * **꼴레뇨 (Koleno):** 겉은 바삭하고 속은 쫄깃하게 구워낸 체코식 돼지 무릎(족발) 요리.
        * **스비치코바 (Svíčková):** 부드러운 소고기 안심에 크림 소스와 크랜베리 잼, 빵(크네들리키)을 곁들인 요리.
        * **필스너 우르켈 생맥주:** 체코에 오면 물보다 많이 마시게 되는 최고의 라거 맥주.
        """)
        st.markdown("#### 🎁 Must-Buy (특산물)")
        st.markdown("""
        * **마뉴팍투라 (Manufaktura):** 맥주, 와인 등으로 만든 자연주의 바디케어 브랜드. 맥주 샴푸가 가장 유명합니다.
        * **베체로브카 (Becherovka):** 소화를 돕는 체코 전통 허브 리큐어. 특유의 계피와 허브 향이 특징입니다.
        """)

with tab3: 
    st.markdown("### Classic Experiences")
    e1, e2 = st.columns(2)
    with e1: st.info("**🎼 빈 오페라 극장 (Staatsoper)**\n미리 좋은 좌석을 예매해 멋지게 드레스업 하고 정통 클래식 오페라 관람하기.")
    with e2: st.success("**🛳️ 부다페스트 프라이빗 요트**\n단체 크루즈 대신 소규모 요트를 렌트해 샴페인을 터트리며 야경을 즐기는 럭셔리 체험.")

with tab4:
    st.markdown("### 🎒 Smart Travel Kit (Europe Edition)")
    col_check, col_tip = st.columns([1.2, 1])
    with col_check:
        with st.expander("👔 의류 & 뷰티 (드레스업 필수)", expanded=True):
            st.checkbox("파인다이닝용 정장/자켓")
            st.checkbox("포멀한 이브닝 룩 & 구두")
            st.checkbox("편안한 런닝화 (유럽 돌바닥 대비 필수)")
            st.checkbox("짐(Gym) 전용 운동복 & 운동화")
        with st.expander("🔌 전자기기 & 촬영"):
            st.checkbox("유럽용 멀티 어댑터")
            st.checkbox("DJI Pocket 3 / GoPro (야경 브이로그용)")
            st.checkbox("소매치기 방지 폰 스트랩")
        with st.expander("🚆 국가 간 기차 예매 (Official Links)", expanded=True):
            st.markdown("""
            * **부다페스트 → 빈:** [ÖBB (오스트리아)](https://www.oebb.at/en/) 또는 [MÁV (헝가리)](https://www.mavcsoport.hu/en)
            * **빈 → 잘츠부르크:** [ÖBB (오스트리아)](https://www.oebb.at/en/) 또는 [Westbahn (사철)](https://westbahn.at/en/)
            * **잘츠부르크 → 프라하:** [ÖBB (오스트리아)](https://www.oebb.at/en/) 또는 [ČD (체코)](https://www.cd.cz/en/)
            * **💡 럭셔리 Tip:** ÖBB 예약 시 1등석 요금에 약 €15 추가하여 **'Business Class'**로 업그레이드 강력 추천 (프라이빗 좌석, 웰컴 드링크). 반드시 **좌석 지정(Seat Reservation)** 추가 필수!
            """)
    with col_tip:
        st.markdown("#### 🚨 안전 & 매너 팁")
        st.warning("**소매치기 주의:** 프라하 카를교, 주요 기차역 탑승 시 소지품 주의.")
        st.info("**팁 매너:** 계산서에 Service Charge가 포함 안 되어 있다면, 영수증 금액의 5~10% 정도를 남기는 것이 매너입니다.")
        st.success("**택스 리펀:** 쇼핑 시 항상 여권 지참! 국가 간 이동 시 마지막 EU 국가 공항에서 세금 환급 처리.")

with tab5:
    st.markdown("### 💰 Smart Wallet (유로 & 코루나 혼합 관리)")
    st.caption("※ 모든 지출은 편의상 원화(KRW)로 환산하여 총예산에서 차감합니다.")
    
    new_budget = st.number_input("총 여행 예산 (KRW)", value=st.session_state.total_budget, step=100000)
    if new_budget != st.session_state.total_budget:
        st.session_state.total_budget = new_budget
        save_data()
        st.rerun()

    col_budget, col_add = st.columns([1, 1.5])
    with col_budget:
        total_spent = sum([x['amount_krw'] for x in st.session_state.expenses])
        remaining = st.session_state.total_budget - total_spent
        progress = min(1.0, total_spent / st.session_state.total_budget) if st.session_state.total_budget > 0 else 0
        
        st.metric("Total Budget", f"₩ {st.session_state.total_budget:,}")
        st.metric("Spent", f"₩ {total_spent:,}", delta=f"- {total_spent:,}", delta_color="inverse")
        st.metric("Remaining", f"₩ {remaining:,}", delta=f"{remaining:,}")
        st.progress(progress)
        
    with col_add:
        with st.form("expense_form", clear_on_submit=True):
            item = st.text_input("내역 (예: 빈 구찌 가방)")
            c1, c2 = st.columns(2)
            cur_sel = c1.selectbox("통화", ["EUR", "CZK", "HUF", "KRW"])
            amount = c2.number_input("결제 금액", min_value=0.0, step=10.0, value=None, placeholder="금액 입력")
            
            if st.form_submit_button("추가") and item and amount:
                krw_amount = int(amount * rates[cur_sel]) if cur_sel != "KRW" else int(amount)
                st.session_state.expenses.append({"item": item, "currency": cur_sel, "original": amount, "amount_krw": krw_amount})
                save_data()
                st.rerun()
                
    st.markdown("---")
    if st.session_state.expenses:
        for i, exp in enumerate(st.session_state.expenses):
            c1, c2, c3 = st.columns([0.6, 0.3, 0.1])
            c1.text(f"{exp['item']} ({exp['original']} {exp['currency']})")
            c2.text(f"₩ {exp['amount_krw']:,}")
            if c3.button("🗑️", key=f"del_exp_{i}"):
                st.session_state.expenses.pop(i)
                save_data()
                st.rerun()
    else: st.info("지출 내역이 없습니다.")
