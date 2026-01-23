import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go  # 세부 시각화 컨트롤을 위해 추가

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

# 데이터 로드 (파일 경로 확인 필요)
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

st.sidebar.header("🎨 지역별 색상")
color_map = {}
for i, region in enumerate(selected_regions):
    # 기본 색상 리스트 (선택 안했을 때 대비)
    default_colors = px.colors.qualitative.Plotly
    color_map[region] = st.sidebar.color_picker(f"'{region}'", default_colors[i % len(default_colors)])

# --- 메인 화면 ---
col1_main, col2_main = st.columns([1, 10])
with col1_main:
    try: st.image(logo_image_path, width=70)
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
    st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
else:
    df_sel_sorted = df_sel.sort_values(by=['지역', '날짜'])

    # 1. 기본 라인 생성 (경로선)
    fig = px.line(
        df_sel_sorted,
        x="매매지수",
        y="전세지수",
        color="지역",
        hover_data=['날짜', '지역'],
        color_discrete_map=color_map,
        category_orders={"지역": selected_regions}
    )
    
    # 선의 투명도를 조절하여 흐름을 부드럽게 표현
    fig.update_traces(line=dict(width=2.5), opacity=0.6)

    # 2. 지역별 특수 표식 추가 (시작점, 끝점, 화살표)
    for region in selected_regions:
        region_df = df_sel_sorted[df_sel_sorted['지역'] == region]
        if len(region_df) == 0: continue

        first_row = region_df.iloc[0]
        last_row = region_df.iloc[-1]
        
        # 시작점 표시 (작은 회색 원)
        fig.add_trace(go.Scatter(
            x=[first_row['매매지수']], y=[first_row['전세지수']],
            mode='markers+text',
            marker=dict(size=8, color='lightgrey', symbol='circle'),
            text=["시작"], textposition="bottom center",
            showlegend=False, hoverinfo='skip'
        ))

        # 최신점 강조 (큰 마커)
        fig.add_trace(go.Scatter(
            x=[last_row['매매지수']], y=[last_row['전세지수']],
            mode='markers',
            marker=dict(size=12, color=color_map.get(region), symbol='triangle-up',
                        line=dict(width=2, color='white')),
            showlegend=False, hoverinfo='skip'
        ))

        # 화살표 추가 (직전 데이터 -> 최신 데이터 방향)
        #if len(region_df) > 1:
        #    prev_row = region_df.iloc[-2]
        #    fig.add_annotation(
        #        x=last_row['매매지수'], y=last_row['전세지수'],
        #        ax=prev_row['매매지수'], ay=prev_row['전세지수'],
        #        xref="x", yref="y", axref="x", ayref="y",
        #        showarrow=True, arrowhead=3, arrowsize=1.5, arrowwidth=2.5,
        #        arrowcolor=color_map.get(region)
        #    )

        # 지역명 레이블 (최신 지점에 말풍선처럼 표시)
        fig.add_annotation(
            x=last_row['매매지수'], y=last_row['전세지수'],
            text=f" [최근]{region} ",
            showarrow=False,
            yshift=18,
            font=dict(size=12, color="white"),
            bgcolor=color_map.get(region),
            borderpad=3,
            opacity=0.9
        )

    # 3. 레이아웃 최적화
    fig.update_layout(
        title=f"부동산 4분면 지수 경로 ({start_date} ~ {end_date})",
        xaxis_title="매매지수 (X축)",
        yaxis_title="전세지수 (Y축)",
        height=750,
        hovermode="closest",
        plot_bgcolor="white",
        xaxis=dict(gridcolor='lightgrey', zerolinecolor='grey'),
        yaxis=dict(gridcolor='lightgrey', zerolinecolor='grey')
    )

    st.plotly_chart(fig, use_container_width=True)

    # 데이터 요약 정보 제공
    #with st.expander("데이터 요약 보기"):
    #    st.dataframe(df_sel_sorted)




