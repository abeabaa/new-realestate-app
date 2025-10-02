import streamlit as st
import pandas as pd
import plotly.express as px

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="부동산 4분면 경로 분석",
    page_icon="📈", # 탭 아이콘은 그대로 유지
    layout="wide"
)

# --- 데이터 로딩 및 전처리 (캐싱 기능 포함) ---
@st.cache_data
def load_data(file_path):
    """엑셀 파일을 로드하고 데이터를 전처리하는 함수"""
    try:
        sale = pd.read_excel(file_path, sheet_name="1.매매증감", skiprows=[0, 2, 3])
        rent = pd.read_excel(file_path, sheet_name="2.전세증감", skiprows=[0, 2, 3])
    except FileNotFoundError:
        st.error(f"'{file_path}' 파일을 찾을 수 없습니다. app.py와 같은 폴더에 엑셀 파일을 넣어주세요.")
        st.stop()
    except Exception as e:
        st.error(f"엑셀 파일 시트를 읽는 중 오류가 발생했습니다: {e}")
        st.info("엑셀 파일에 '1.매매증감'과 '2.전세증감' 시트가 있는지 확인해주세요.")
        st.stop()

    sale = sale.dropna(subset=['구분'])
    sale[:] = sale[:].fillna(0).infer_objects(copy=False)
    rent = rent.dropna(subset=['구분'])
    rent[:] = rent[:].fillna(0).infer_objects(copy=False)
    sale.rename(columns={'구분': '날짜'}, inplace=True)
    rent.rename(columns={'구분': '날짜'}, inplace=True)
    sale_melt = sale.melt(id_vars=['날짜'], var_name='지역', value_name='매매증감률')
    rent_melt = rent.melt(id_vars=['날짜'], var_name='지역', value_name='전세증감률')
    df = pd.merge(sale_melt, rent_melt, on=['날짜', '지역'])
    df['날짜'] = pd.to_datetime(df['날짜'])
    return df

# --- 파일 경로 및 로고 이미지 설정 ---
# 🚨 app.py와 같은 폴더에 파일들이 있어야 합니다.
excel_file_path = "20250922_주간시계열.xlsx"
logo_image_path = "jak_logo.png" # 로고 파일 경로
df = load_data(excel_file_path)

# --- 사이드바 (사용자 입력 UI) ---
st.sidebar.header("🗓️ 필터를 선택하세요")

# (날짜, 지역 선택 등 나머지 사이드바 코드는 기존과 동일)
selected_dates = st.sidebar.date_input(
    "날짜 범위",
    value=(df["날짜"].min(), df["날짜"].max()),
    min_value=df["날짜"].min(),
    max_value=df["날짜"].max(),
)
if len(selected_dates) != 2:
    st.sidebar.error("날짜 범위를 올바르게 선택해주세요.")
    st.stop()
start_date, end_date = selected_dates

all_regions = df["지역"].unique()
selected_regions = st.sidebar.multiselect(
    "지역 선택",
    options=all_regions,
    default=list(all_regions[:5])
)

# ========================= [ 수정된 부분 1: 사이드바 색상 선택 헤더 ] =========================
# st.columns를 사용해 이미지와 텍스트를 나란히 배치합니다.
# [1, 5]는 컬럼의 너비 비율을 의미합니다. (이미지 컬럼이 1, 텍스트 컬럼이 5)
col1, col2 = st.sidebar.columns([1, 5])
with col1:
    st.image(logo_image_path, width=30) # 로고 이미지 표시 (너비 조절)
with col2:
    st.header("색상 지정") # st.sidebar.header 대신 st.header 사용

color_map = {}
for region in selected_regions:
    default_color = px.colors.qualitative.Plotly[len(color_map) % len(px.colors.qualitative.Plotly)]
    selected_color = st.sidebar.color_picker(f"'{region}' 색상", default_color)
    color_map[region] = selected_color

# ========================= [ 수정된 부분 2: 메인 화면 타이틀 ] =========================
# 메인 화면에서도 동일한 방법으로 로고와 제목을 나란히 배치합니다.
col1_main, col2_main = st.columns([1, 10])
with col1_main:
    try:
        st.image(logo_image_path, width=70) # 로고 이미지 표시
    except Exception as e:
        st.error(f"로고 파일을 불러올 수 없습니다: {e}")
        st.info(f"`{logo_image_path}` 파일이 현재 폴더에 있는지 확인해주세요.")
with col2_main:
    st.title("부동산 매매/전세 가격 경로 분석")

st.markdown("사이드바에서 필터와 색상을 직접 선택하여 시각화할 수 있습니다.")

# (데이터 필터링 및 그래프 시각화 코드는 기존과 동일)
mask = (df["날짜"] >= pd.to_datetime(start_date)) & \
       (df["날짜"] <= pd.to_datetime(end_date)) & \
       (df["지역"].isin(selected_regions))
df_sel = df[mask]

if df_sel.empty:
    st.warning("선택한 조건에 맞는 데이터가 없습니다. 다른 필터를 선택해주세요.")
else:
    df_sel_sorted = df_sel.sort_values(by='날짜')
    fig = px.line(
        df_sel_sorted,
        x="매매증감률",
        y="전세증감률",
        color="지역",
        markers=True,
        hover_data={'날짜': '|%Y-%m-%d', '지역': True},
        color_discrete_map=color_map
    )
    last_points = df_sel_sorted.loc[df_sel_sorted.groupby('지역')['날짜'].idxmax()]
    for index, row in last_points.iterrows():
        fig.add_annotation(
            x=row['매매증감률'],
            y=row['전세증감률'],
            text=row['지역'],
            showarrow=False,
            yshift=10,
            font=dict(size=12, color="black"),
            bgcolor="rgba(255, 255, 255, 0.7)",
            borderpad=4
        )
    fig.update_layout(
        title="부동산 4분면 경로",
        xaxis_title="매매증감률 (%)",
        yaxis_title="전세증감률 (%)",
        height=700,
        legend_title="지역"
    )
    st.plotly_chart(fig, use_container_width=True)


