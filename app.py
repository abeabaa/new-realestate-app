import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. 페이지 기본 설정 ---
st.set_page_config(
    page_title="부동산 지수 4분면 분석",
    page_icon="✒️",
    layout="wide"
)

# --- 2. 데이터 로딩 및 전처리 ---
@st.cache_data
def load_data(file_path):
    """엑셀 파일을 로드하고 데이터를 전처리하는 함수"""
    try:
        # '3.매매지수', '4.전세지수' 시트를 읽습니다.
        sale = pd.read_excel(file_path, sheet_name="3.매매지수", skiprows=[0, 2, 3])
        rent = pd.read_excel(file_path, sheet_name="4.전세지수", skiprows=[0, 2, 3])
    except FileNotFoundError:
        st.error(f"'{file_path}' 파일을 찾을 수 없습니다. app.py와 같은 폴더에 엑셀 파일을 넣어주세요.")
        st.stop()
    except Exception as e:
        st.error(f"엑셀 파일을 읽는 중 오류가 발생했습니다. 오류: {e}")
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

# 파일 로드
file_path = "주간시계열.xlsx"
logo_image_path = "jak_logo.png"
df = load_data(file_path)

# --- 3. 사이드바 (사용자 입력 UI) ---
st.sidebar.header("🗓️ 필터를 선택하세요")

# 날짜 범위 선택
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

# 지역 선택
all_regions = df["지역"].unique()
selected_regions = st.sidebar.multiselect(
    "지역 선택",
    options=all_regions,
    default=all_regions[:5]
)

# 사용자 색상 선택
st.sidebar.header("🎨 색상을 지정하세요")
color_map = {}
for region in selected_regions:
    # 기본 색상을 검은색으로 하되, 지역별 구분을 위해 자동 할당 가능
    selected_color = st.sidebar.color_picker(f"'{region}' 색상", '#000000')
    color_map[region] = selected_color

# --- 4. 메인 화면 ---
col1_main, col2_main = st.columns([1, 10])
with col1_main:
    try:
        st.image(logo_image_path, width=80) 
    except:
        pass # 로고 없을 시 건너뜀

with col2_main:
    st.title("부동산 매매/전세 가격 경로 분석")

# --- 5. 데이터 필터링 ---
mask = (df["날짜"] >= pd.to_datetime(start_date)) & \
       (df["날짜"] <= pd.to_datetime(end_date)) & \
       (df["지역"].isin(selected_regions))
df_sel = df[mask].sort_values(by=['지역', '날짜'])

# --- 6. 그래프 시각화 ---
if df_sel.empty:
    st.warning("선택한 조건에 맞는 데이터가 없습니다. 다른 필터를 선택해주세요.")
else:
    # 경로 플롯 (기본 라인과 포인트)
    fig = px.line(
        df_sel,
        x="매매지수",
        y="전세지수",
        color="지역",
        markers=True,
        hover_data=['날짜', '지역'],
        color_discrete_map=color_map
    )

    # 마지막 포인트에만 화살표와 레이블 추가
    annotations = []
    for region in selected_regions:
        reg_data = df_sel[df_sel['지역'] == region]
        if len(reg_data) >= 2:
            last = reg_data.iloc[-1]   # 가장 최신 점
            prev = reg_data.iloc[-2]   # 바로 전 점
            reg_color = color_map.get(region, "#000000")
            
            # 1. 방향 화살표 (이전 점 -> 현재 점)
            annotations.append(dict(
                x=last['매매지수'],
                y=last['전세지수'],
                ax=prev['매매지수'],
                ay=prev['전세지수'],
                xref="x", yref="y",
                axref="x", ayref="y",
                showarrow=True,
                arrowhead=3,      # 화살촉 모양
                arrowsize=1.5,    # 화살촉 크기
                arrowwidth=2,     # 화살촉 두께
                arrowcolor=reg_color
            ))
            
            # 2. 지역명 표시
            annotations.append(dict(
                x=last['매매지수'],
                y=last['전세지수'],
                text=f"<b>{region}</b>",
                showarrow=False,
                yshift=18,
                font=dict(size=12, color=reg_color),
                bgcolor="rgba(255, 255, 255, 0.8)"
            ))

    # 레이아웃 업데이트
    fig.update_layout(
        annotations=annotations,
        title=f"부동산 4분면 지수 경로 ({start_date} ~ {end_date})",
        xaxis_title="매매지수 (X)",
        yaxis_title="전세지수 (Y)",
        height=750,
        template="plotly_white",
        legend_title="지역"
    )

    # 격자선 최적화
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='whitesmoke', zeroline=True, zerolinewidth=2)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='whitesmoke', zeroline=True, zerolinewidth=2)

    st.plotly_chart(fig, use_container_width=True)

# 하단 정보 표시
#st.caption("데이터 출처: KB부동산 주간시계열 자료를 기반으로 분석되었습니다.")
