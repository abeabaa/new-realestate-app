import streamlit as st
import pandas as pd
import plotly.express as px

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="부동산 4분면 경로 분석 (색상 선택)",
    page_icon="🎨",
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

# --- 파일 경로 설정 및 데이터 로딩 ---
file_path = "20250922_주간시계열.xlsx"
df = load_data(file_path)

# --- 사이드바 (사용자 입력 UI) ---
st.sidebar.header("🗓️ 필터를 선택하세요")

# 날짜 범위 선택
selected_dates = st.sidebar.date_input(
    "날짜 범위",
    value=(df["날짜"].min(), df["날짜"].max()),
)
if len(selected_dates) != 2:
    st.sidebar.error("날짜 범위를 올바르게 선택해주세요.")
    st.stop()
start_date, end_date = selected_dates

# 지역 선택
all_regions = df["지역"].unique()
selected_regions = st.sidebar.multiselect(
    "지역 선택",
    options=all_regions,
    default=all_regions[:5] # 기본값: 처음 5개 지역 선택
)


# --- 🎨 사용자 색상 선택 기능 ---
st.sidebar.header("🎨 색상을 지정하세요")
color_map = {}
# 사용자가 선택한 각 지역에 대해 색상 선택 위젯을 동적으로 생성합니다.
for region in selected_regions:
    # st.color_picker는 사용자가 색상을 고를 수 있는 위젯입니다.
    default_color = '#000000' # 기본값은 검은색으로 설정
    selected_color = st.sidebar.color_picker(f"'{region}' 색상", default_color)
    color_map[region] = selected_color # 딕셔너리에 '지역:선택된 색상'을 저장합니다.

# --- 메인 화면 ---
st.title("🎨 부동산 매매/전세 가격 경로 분석")
st.markdown("사이드바에서 필터와 색상을 직접 선택하여 시각화할 수 있습니다.")

# 데이터 필터링
mask = (df["날짜"] >= pd.to_datetime(start_date)) & \
       (df["날짜"] <= pd.to_datetime(end_date)) & \
       (df["지역"].isin(selected_regions))
df_sel = df[mask]

# --- 그래프 시각화 ---
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
        hover_data=['날짜', '지역'],
        # 사용자가 선택한 색상 맵을 여기에 적용합니다.
        color_discrete_map=color_map
    )

for index, row in last_points.iterrows():
    fig.add_annotation(
        x=row['매매지수'],
        y=row['전세지수'],
        text=row['지역'],
        showarrow=False,
        yshift=10,
        font=dict(size=12, color="black"),
        bgcolor="rgba(255, 255, 255, 0.6)"
    )

fig.update_layout(
    title="부동산 4분면 경로",
    xaxis_title="매매증감률 (%)",
    yaxis_title="전세증감률 (%)",
    height=700,
    legend_title="지역"
)

st.plotly_chart(fig, use_container_width=True)







