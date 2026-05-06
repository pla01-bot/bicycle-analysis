import streamlit as st
import sqlite3
import pandas as pd
import os
import plotly.express as px

# 1. 페이지 기본 설정 (가장 먼저 실행됩니다)
st.set_page_config(page_title="따릉이 공공데이터 분석", page_icon="🚲", layout="wide")
st.title("🚲 서울시 공공자전거 데이터 분석 대시보드")
st.write("초보자도 쉽게 따라 할 수 있는 데이터 시각화 프로젝트입니다!")

# 2. 데이터베이스 파일 확인 (에러 방지용)
db_path = 'bicycle.db'
if not os.path.exists(db_path):
    # 파일이 없으면 아주 친절한 에러 메시지를 띄우고 실행을 멈춥니다.
    st.error("앗! 🚨 데이터베이스 파일(`bicycle.db`)을 찾을 수 없어요. `app.py`와 같은 폴더에 파일이 있는지 꼭 확인해 주세요!")
    st.stop()

# 3. 데이터베이스 연결 함수
@st.cache_data # 데이터를 매번 다시 불러오지 않도록 기억(캐싱)해두는 마법의 기능입니다.
def load_data(query):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

st.divider() # 화면에 예쁜 가로줄을 그어줍니다.

# ==========================================
# 📊 차트 1. 월별 이용 패턴 (라인 차트)
# ==========================================
st.header("1️⃣ 월별 자전거 이용 패턴")

sql1 = """
SELECT 대여일자, SUM(이용건수) AS 총이용건수
FROM 이용정보
GROUP BY 대여일자
ORDER BY 대여일자;
"""
df1 = load_data(sql1)

# ① 시각화
fig1 = px.line(df1, x='대여일자', y='총이용건수', markers=True, title="월별 총 이용건수 추이")
st.plotly_chart(fig1, use_container_width=True)

# ② 사용한 SQL
with st.expander("📝 사용한 SQL 쿼리 보기"):
    st.code(sql1, language="sql")

# ③ 인사이트
st.info("💡 **인사이트**\n\n봄, 가을 등 야외 활동하기 좋은 계절에 자전거 이용량이 크게 증가하는 것을 확인할 수 있습니다. 반면, 겨울철이나 장마철에는 날씨의 영향으로 이용건수가 감소하는 경향을 보입니다.")

st.divider()

# ==========================================
# 📊 차트 2. 기온별 평균 이용량 (막대 차트)
# ==========================================
st.header("2️⃣ 기온 구간별 평균 이용량")

# 기온 테이블에서 지점별 차이를 없애기 위해 년월별 평균기온을 먼저 구하고 조인합니다.
sql2 = """
WITH TempDaily AS (
    SELECT 년월, AVG(평균기온) AS 평균기온
    FROM 기온
    GROUP BY 년월
)
SELECT 
    CAST(T.평균기온 / 5 AS INTEGER) * 5 AS 기온구간_기준,
    CAST(T.평균기온 / 5 AS INTEGER) * 5 || '도 ~ ' || (CAST(T.평균기온 / 5 AS INTEGER) * 5 + 4) || '도' AS 기온구간,
    AVG(U.이용건수) AS 평균이용건수
FROM 이용정보 U
JOIN TempDaily T ON U.대여일자 = T.년월
GROUP BY 기온구간_기준
ORDER BY 기온구간_기준;
"""
df2 = load_data(sql2)

# ① 시각화
fig2 = px.bar(df2, x='기온구간', y='평균이용건수', text_auto='.0f', title="5도 구간별 평균 이용건수", color='평균이용건수', color_continuous_scale='Blues')
st.plotly_chart(fig2, use_container_width=True)

# ② 사용한 SQL
with st.expander("📝 사용한 SQL 쿼리 보기"):
    st.code(sql2, language="sql")

# ③ 인사이트
st.info("💡 **인사이트**\n\n기온이 15~25도 사이인 온화한 날씨일 때 자전거 이용량이 가장 높게 나타납니다. 반면 0도 이하의 한파나 30도를 넘는 폭염일 때는 자전거 이용을 기피하는 뚜렷한 패턴을 보여줍니다.")

st.divider()

# ==========================================
# 📊 차트 3. 인기 대여소 TOP 10 (가로 막대 차트)
# ==========================================
st.header("3️⃣ 인기 대여소 TOP 10")

sql3 = """
SELECT 
    대여소.보관소명, 
    SUM(이용정보.이용건수) AS 총이용건수
FROM 이용정보
JOIN 대여소 ON 이용정보.대여소번호 = 대여소.대여소번호
GROUP BY 대여소.대여소번호
ORDER BY 총이용건수 DESC
LIMIT 10;
"""
df3 = load_data(sql3)

# ① 시각화 (가로 막대 차트를 위해 x와 y를 반대로 설정하고 orientation='h'를 줍니다)
# 보관소명이 길 수 있으므로 y축을 내림차순(가장 많은게 위로)으로 정렬합니다.
fig3 = px.bar(df3.sort_values('총이용건수', ascending=True), 
              x='총이용건수', y='보관소명', orientation='h', 
              text_auto=True, title="총 이용건수 상위 10개 대여소")
st.plotly_chart(fig3, use_container_width=True)

# ② 사용한 SQL
with st.expander("📝 사용한 SQL 쿼리 보기"):
    st.code(sql3, language="sql")

# ③ 인사이트
st.info("💡 **인사이트**\n\n주로 지하철역 환승구 출구 근처나 한강공원 등 접근성이 좋고 유동 인구가 많은 곳의 대여소가 인기가 많습니다. 시민들이 출퇴근 및 레저 목적으로 자전거를 적극 활용하고 있음을 알 수 있습니다.")