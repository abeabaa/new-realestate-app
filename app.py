import streamlit as st
import pandas as pd
import plotly.express as px

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="부동산 지수 4분면 분석",
    page_icon="✒️",
    layout="wide"
)

@st.cache_data
def load_data(file_path):
    try:
        sale = pd.read_excel(file_path, sheet_name="3.매매지수", skiprows=[0, 2, 3])
        rent = pd.read_excel(file_path, sheet_name="4.전세지수", skiprows=[0, 2, 3])
    except Exception as e:
        st.error(f"오류 발생: {e}")
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

file_path = "주간시계열.xlsx"
logo_image_path = "jak_logo.png" 
df = load_data(file_path)

# --- 사이드바 ---
st.sidebar.header("🗓️ 필터를 선택하세요")
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
selected_regions = st.sidebar.multiselect("지역 선택", options=all_regions, default=all_regions[:5])

st.sidebar.header("🎨 색상을 지정하세요")
color_map = {}
for region in selected_regions:
    selected_color = st.sidebar.color_picker(f"'{region}' 색상", '#000000')
    color_map[region] = selected_color

# --- 메인 화면 ---
col1_main, col2_main = st.columns([1, 10])
with col1_main:
    try: st.image(logo_image_path, width=700)
    except: pass
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
    # 1. 지역과 날짜순으로 데이터 정렬
    df_sel_sorted = df_sel.sort_values(by=['지역', '날짜'])

    # 2. 기본 라인 그래프 생성 (선은 지우고 포인트만 남기거나, 얇은 선으로 배경 처리 가능)
    fig = px.line(
        df_sel_sorted,
        x="매매지수",
        y="전세지수",
        color="지역",
        markers=False, # 화살표가 점 역할을 하므로 점은 숨깁니다
        hover_data=['날짜', '지역'],
        color_discrete_map=color_map 
    )

    # 3. 모든 구간에 화살표 추가
    for region in selected_regions:
        reg_data = df_sel_sorted[df_sel_sorted['지역'] == region]
        reg_color = color_map.get(region, "#000000")
        
        # 데이터가 2개 이상이어야 화살표(선) 형성 가능
        for i in range(len(reg_data) - 1):
            curr_pt = reg_data.iloc[i]
            next_pt = reg_data.iloc[i+1]
            
            # 이전 점에서 다음 점으로 향하는 화살표 추가
            fig.add_annotation(
                x=next_pt['매매지수'],    # 화살촉이 도착하는 곳
                y=next_pt['전세지수'],
                ax=curr_pt['매매지수'],   # 화살표가 시작되는 곳
                ay=curr_pt['전세지수'],
                xref="x", yref="y",
                axref="x", ayref="y",
                text="", 
                showarrow=True,
                arrowhead=2,           # 화살표 머리 스타일
                arrowsize=1.2,         # 화살표 머리 크기
                arrowwidth=1.5,        # 선 굵기
                arrowcolor=reg_color,  # 지역별 지정 색상
                opacity=0.8            # 너무 진하면 겹칠 때 복잡하므로 약간 투명하게
            )
        
        # 4. 마지막 지점에 지역명 표시 (가독성)
        if not reg_data.empty:
            last_pt = reg_data.iloc[-1]
            fig.add_annotation(
                x=last_pt['매매지수'],
                y=last_pt['전세지수'],
                text=f"<b>{region}</b>",
                showarrow=False,
                yshift=15,
                font=dict(size=12, color=reg_color),
                bgcolor="rgba(255, 255, 255, 0.7)"
            )

    # 그래프 레이아웃 설정
    fig.update_layout(
        title=f"부동산 4분면 지수 경로 (화살표 방향 분석)",
        xaxis_title="매매지수",
        yaxis_title="전세지수",
        height=800,
        showlegend=True,
        plot_bgcolor='white' # 배경을 깨끗하게 설정
    )
    
    # 격자선 추가 (4분면 분석을 용이하게 함)
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGrey')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGrey')

    st.plotly_chart(fig, use_container_width=True)


