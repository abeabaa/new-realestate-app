import streamlit as st
import pandas as pd
import plotly.express as px

# --- 페이지 설정 ---
# Streamlit 페이지의 제목과 레이아웃을 설정합니다.
# wide 레이아웃은 콘텐츠를 화면 너비에 맞게 채워줍니다.
st.set_page_config(
    page_title="부동산 4분면 분석",
    page_icon="🏠",
    layout="wide"
)

# --- 데이터 로딩 및 전처리 ---
# @st.cache_data 데코레이터는 데이터 로딩처럼 오래 걸리는 작업을 캐싱(임시 저장)해줍니다.
# 이렇게 하면 위젯을 조작할 때마다 파일을 다시 읽지 않아 앱 속도가 매우 빨라집니다.
@st.cache_data
def load_data(file_path):
    """엑셀 파일을 읽고 데이터를 전처리하는 함수"""
    try:
        sale = pd.read_excel(file_path, sheet_name="1.매매증감", skiprows=[0, 2, 3])
        rent = pd.read_excel(file_path, sheet_name="2.전세증감", skiprows=[0, 2, 3])
    except FileNotFoundError:
        # 파일이 없을 경우 에러 메시지를 표시하고 앱 실행을 중지합니다.
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

# 데이터 로딩 함수를 호출합니다.
file_path = "20250818_주간시계열.xlsx"
df = load_data(file_path)

# --- 사이드바 UI 구성 ---
# st.sidebar를 사용하면 왼쪽에 컨트롤러(위젯)를 모아놓을 수 있어 깔끔합니다.
st.sidebar.header("📈 옵션을 선택하세요")

# 날짜 선택 위젯 (범위 선택)
# Streamlit의 date_input은 시작일과 종료일을 한번에 받을 수 있어 편리합니다.
selected_dates = st.sidebar.date_input(
    "날짜 범위 선택",
    value=(df["날짜"].min(), df["날짜"].max()), # 기본값: 전체 기간
    min_value=df["날짜"].min(),
    max_value=df["날짜"].max(),
)

# 시작일과 종료일 분리 (두 개 값이 없으면 에러 방지)
if len(selected_dates) != 2:
    st.sidebar.warning("날짜 범위를 올바르게 선택해주세요.")
    st.stop()
start_date, end_date = selected_dates

# 지역 선택 위젯 (다중 선택)
all_regions = df["지역"].unique()
selected_regions = st.sidebar.multiselect(
    "지역 선택",
    options=all_regions,
    default=all_regions[:5] # 기본값: 처음 5개 지역 선택
)

# --- 메인 화면 구성 ---
st.title("🏠 부동산 매매/전세 가격 4분면 분석")
st.markdown("사이드바에서 날짜와 지역을 선택하여 데이터를 시각화하세요.")


# --- 데이터 필터링 ---
# 위젯에서 선택된 값에 따라 데이터를 필터링합니다.
# Streamlit은 위젯 값이 바뀔 때마다 이 스크립트를 자동으로 다시 실행합니다.
start_date_pd = pd.to_datetime(start_date)
end_date_pd = pd.to_datetime(end_date)

mask = (df["날짜"] >= start_date_pd) & \
       (df["날짜"] <= end_date_pd) & \
       (df["지역"].isin(selected_regions))
df_sel = df[mask]

# --- 그래프 시각화 ---
if df_sel.empty or not selected_regions:
    # 필터링된 데이터가 없거나 지역 선택이 안된 경우
    st.warning("선택한 조건에 맞는 데이터가 없습니다. 다른 옵션을 선택해주세요.")
else:
    # Plotly 그래프 생성
    fig = px.scatter(
        df_sel,
        x="매매증감률",
        y="전세증감률",
        color="지역",
        hover_data=['날짜', '지역'],
        labels={'날짜': '날짜'} # hover_data의 날짜 포맷팅을 위해 라벨 추가
    )
    
    # 날짜 포맷을 'YYYY-MM-DD' 형식으로 깔끔하게 변경
    fig.update_traces(hovertemplate='<b>%{customdata[1]}</b><br>날짜: %{customdata[0]|%Y-%m-%d}<br>매매증감률: %{x:.3f}%<br>전세증감률: %{y:.3f}%')

    fig.update_layout(
        title=f"부동산 4분면 ({start_date} ~ {end_date})",
        xaxis_title="매매증감률 (%)",
        yaxis_title="전세증감률 (%)",
        height=700,
        legend_title="지역"
    )

    # st.plotly_chart()를 사용해 Streamlit 앱에 그래프를 표시합니다.
    st.plotly_chart(fig, use_container_width=True)
