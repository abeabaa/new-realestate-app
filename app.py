import streamlit as st
import pandas as pd
import plotly.express as px

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="부동산 지수 4분면 분석",
    page_icon="✒️",
    layout="wide"
)

# --- 데이터 로딩 및 전처리 ---
@st.cache_data
def load_data(file_path):
    """엑셀 파일을 로드하고 데이터를 전처리하는 함수"""
    try:
        sale = pd.read_excel(file_path, sheet_name="3.매매지수", skiprows=[0, 2, 3])
        rent = pd.read_excel(file_path, sheet_name="4.전세지수", skiprows=[0, 2, 3])
    except FileNotFoundError:
        st.error(f"'{file_path}' 파일을 찾을 수 없습니다. app.py와 같은 폴더에 엑셀 파일을 넣어주세요.")
        st.stop()
    except Exception as e:
        st.error(f"엑셀 파일을 읽는 중 오류가 발생했습니다. 시트 이름('3.매매지수', '4.전세지수')을 확인해주세요. 오류: {e}")
        st.stop()

    sale = sale.dropna(subset=['구분'])
    sale[:] = sale[:].fillna(0).infer_objects(copy=False)
    rent[:] = rent[:].fillna(0).infer_objects(copy=False)

    sale.rename(columns={'구분': '날짜'}, inplace=True)
    rent.rename(columns={'구분': '날짜'}, inplace=True)

    sale_melt = sale.melt(id_vars=['날짜'], var_name='지역', value_name='매매지수')
    rent_melt = rent.melt(id_vars=['날짜'], var_name='지역', value_name='전세지수')

    df = pd.merge(sale_melt, rent_melt, on=['날짜', '지역'])
    df['날짜'] = pd.to_datetime(df['날짜'])
    return df

file_path = "20251103_주간시계열.xlsx"
logo_image_path = "" # 로고 파일 경로
df = load_data(file_path)

# --- 사이드바 (사용자 입력 UI) ---
st.sidebar.header("🗓️ 필터를 선택하세요")

# 1. 날짜 범위 선택 위젯
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

# 2. 지역 선택 위젯
all_regions = df["지역"].unique()
selected_regions = st.sidebar.multiselect(
    "지역 선택",
    options=all_regions,
    default=all_regions[:5] # 기본값: 처음 5개 지역 선택
)

st.sidebar.header("🎨 색상을 지정하세요")
color_map = {}
for region in selected_regions:
    default_color = '#000000' # 기본값은 검은색으로 설정
    selected_color = st.sidebar.color_picker(f"'{region}' 색상", default_color)
    color_map[region] = selected_color

# --- 메인 화면 ---
col1_main, col2_main = st.columns([1, 10])
with col1_main:
    try:
        st.image(logo_image_path, width=700) # 로고 이미지 표시
    except Exception as e:
        st.error(f"로고 파일을 불러올 수 없습니다: {e}")
        st.info(f"`{logo_image_path}` 파일이 현재 폴더에 있는지 확인해주세요.")
with col2_main:
    st.title("부동산 매매/전세 가격 경로 분석")

# --- 데이터 필터링 ---
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
        x="매매지수",
        y="전세지수",
        color="지역",
        markers=True,
        hover_data=['날짜', '지역'],
        color_discrete_map=color_map 
    )

    # 경로 마지막에 지역명 표시
    last_points = df_sel_sorted.loc[df_sel_sorted.groupby('지역')['날짜'].idxmax()]
    
    for index, row in last_points.iterrows():
        fig.add_annotation(
            x=row['매매지수'],
            y=row['전세지수'],
            text=f"<b>{row['지역']}</b>",
            showarrow=False,
            yshift=12,
            font=dict(size=12, color="black"),
            bgcolor="rgba(255, 255, 255, 0.7)"
        )

    # 그래프 레이아웃 설정
    fig.update_layout(
        title=f"부동산 4분면 지수 경로 ({start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')})",
        xaxis_title="매매지수",
        yaxis_title="전세지수",
        height=700,
        legend_title="지역",
        showlegend=True 
    )

    # Streamlit에 그래프 표시
    st.plotly_chart(fig, use_container_width=True)










