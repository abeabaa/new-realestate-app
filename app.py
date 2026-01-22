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
    st.warning("데이터가 없습니다.")
else:
    df_sel_sorted = df_sel.sort_values(by=['지역', '날짜'])

    fig = px.line(
        df_sel_sorted,
        x="매매지수",
        y="전세지수",
        color="지역",
        markers=True,
        hover_data=['날짜', '지역'],
        color_discrete_map=color_map
    )

    # --- 화살표 및 지역명 표시 로직 ---
    for region in selected_regions:
        region_df = df_sel_sorted[df_sel_sorted['지역'] == region]
        if len(region_df) < 2: continue # 포인트가 2개 이상일 때만 화살표 가능

        # 마지막 포인트(머리)와 직전 포인트(꼬리) 추출
        last_row = region_df.iloc[-1]
        prev_row = region_df.iloc[-2]

        # 화살표 추가
        fig.add_annotation(
            x=last_row['매매지수'],  # 화살표가 가리킬 곳 (끝점)
            y=last_row['전세지수'],
            ax=prev_row['매매지수'], # 화살표가 시작될 곳 (이전 점)
            ay=prev_row['전세지수'],
            xref="x", yref="y",
            axref="x", ayref="y",
            showarrow=True,
            arrowhead=2, # 화살표 머리 모양 (1~8)
            arrowsize=3,
            arrowwidth=5,
            arrowcolor=color_map.get(region, "black")
        )

        # 지역 이름 텍스트 추가 (화살표 끝에 표시)
        fig.add_annotation(
            x=last_row['매매지수'],
            y=last_row['전세지수'],
            text=f"<b>{region}</b>",
            showarrow=False,
            yshift=15,
            font=dict(size=12, color=color_map.get(region, "black")),
            bgcolor="rgba(255, 255, 255, 0.8)"
        )

    fig.update_layout(
        title=f"부동산 4분면 지수 경로 ({start_date} ~ {end_date})",
        xaxis_title="매매지수",
        yaxis_title="전세지수",
        height=700,
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)


