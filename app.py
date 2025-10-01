import streamlit as st
import pandas as pd
import plotly.express as px

# --- 페이지 기본 설정 ---
# 웹 앱의 제목, 아이콘, 레이아웃을 설정합니다.
st.set_page_config(
    page_title="부동산 4분면 경로 분석",
    page_icon="📈",
    layout="wide"
)

# --- 데이터 로딩 및 전처리 ---
# @st.cache_data: 데이터 로딩을 캐싱하여 앱 속도를 향상시킵니다.
@st.cache_data
def load_data(file_path):
    """엑셀 파일을 로드하고 데이터를 전처리하는 함수"""
    try:
        sale = pd.read_excel(file_path, sheet_name="1.매매증감", skiprows=[0, 2, 3])
        rent = pd.read_excel(file_path, sheet_name="2.전세증감", skiprows=[0, 2, 3])
    except FileNotFoundError:
        st.error(f"'{file_path}' 파일을 찾을 수 없습니다. app.py와 같은 폴더에 엑셀 파일을 넣어주세요.")
        st.stop()

    sale = sale.dropna(subset=['구분'])
    sale[:] = sale[:].fillna(0).infer_objects(copy=False)
    rent[:] = rent[:].fillna(0).infer_objects(copy=False)

    sale.rename(columns={'구분': '날짜'}, inplace=True)
    rent.rename(columns={'구분': '날짜'}, inplace=True)

    sale_melt = sale.melt(id_vars=['날짜'], var_name='지역', value_name='매매증감률')
    rent_melt = rent.melt(id_vars=['날짜'], var_name='지역', value_name='전세증감률')

    df = pd.merge(sale_melt, rent_melt, on=['날짜', '지역'])
    df['날짜'] = pd.to_datetime(df['날짜'])
    return df

# --- ⚙️ 중요: 파일 경로를 상대 경로로 변경 ---
# 클라우드 배포를 위해 파일 이름만 사용합니다.
file_path = "20250818_주간시계열.xlsx"
df = load_data(file_path)

# --- 사이드바 (사용자 입력 UI) ---
st.sidebar.header("🗓️ 필터를 선택하세요")

# 1. 날짜 범위 선택 위젯
selected_dates = st.sidebar.date_input(
    "날짜 범위",
    value=(df["날짜"].min(), df["날짜"].max()), # 기본값: 전체 기간
    min_value=df["날짜"].min(),
    max_value=df["날짜"].max(),
)

# 날짜가 2개 선택되었는지 확인 (시작일, 종료일)
if len(selected_dates) != 2:
    st.sidebar.error("날짜 범위를 올바르게 선택해주세요.")
    st.stop()
start_date, end_date = selected_dates

# 2. 지역 선택 위젯
all_regions = sorted(df["지역"].unique())
selected_regions = st.sidebar.multiselect(
    "지역 선택",
    options=all_regions,
    default=all_regions[:3] # 기본값: 처음 3개 지역
)

# --- 메인 화면 ---
st.title("📈 부동산 매매/전세 가격 경로 분석")
st.markdown(f"**선택된 기간:** `{start_date.strftime('%Y-%m-%d')}` ~ `{end_date.strftime('%Y-%m-%d')}`")
st.markdown("시간에 따른 각 지역의 부동산 가격 변화 궤적을 보여줍니다.")

# --- 데이터 필터링 ---
mask = (df["날짜"] >= pd.to_datetime(start_date)) & \
       (df["날짜"] <= pd.to_datetime(end_date)) & \
       (df["지역"].isin(selected_regions))
df_sel = df[mask]

# --- 그래프 시각화 ---
if df_sel.empty:
    st.warning("선택한 조건에 맞는 데이터가 없습니다. 다른 필터를 선택해주세요.")
else:
    # 경로 플롯을 그리기 위해 날짜순으로 정렬
    df_sel_sorted = df_sel.sort_values(by='날짜')

    fig = px.line(
        df_sel_sorted,
        x="매매증감률",
        y="전세증감률",
        color="지역",
        markers=True, # 각 지점에 점도 함께 표시
        hover_data=['날짜', '지역']
    )

    # 공통 레이아웃 업데이트
    fig.update_layout(
        title="부동산 4분면 경로",
        xaxis_title="매매증감률 (%)",
        yaxis_title="전세증감률 (%)",
        height=700,
        legend_title="지역"
    )

    # st.plotly_chart로 Streamlit에 그래프 표시
    st.plotly_chart(fig, use_container_width=True)
