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
    try:
        sale = pd.read_excel(file_path, sheet_name="3.매매지수", skiprows=[0, 2, 3])
        rent = pd.read_excel(file_path, sheet_name="4.전세지수", skiprows=[0, 2, 3])
    except Exception as e:
        st.error(f"파일 로드 오류: {e}")
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
color_map = {region: st.sidebar.color_picker(f"'{region}' 색상", '#000000') for region in selected_regions}

# --- 메인 화면 ---
st.title("부동산 매매/전세 가격 경로 분석")

# --- 데이터 필터링 및 샘플링 (핵심!) ---
mask = (df["날짜"] >= pd.to_datetime(start_date)) & \
       (df["날짜"] <= pd.to_datetime(end_date)) & \
       (df["지역"].isin(selected_regions))
df_filtered = df[mask].sort_values(by=['지역', '날짜'])

# [방법 1 적용] 지역별로 4개 행마다 하나씩만 추출 (주간 -> 월간 흐름으로 압축)
df_sel_sorted = df_filtered.groupby('지역', group_keys=False).apply(lambda x: x.iloc[::4, :])

# --- 그래프 시각화 ---
if df_sel_sorted.empty:
    st.warning("선택한 조건에 맞는 데이터가 없습니다.")
else:
    # 기본 라인 생성 (선은 얇게 보조적으로 사용)
    fig = px.line(
        df_sel_sorted, x="매매지수", y="전세지수", color="지역",
        hover_data=['날짜', '지역'],
        color_discrete_map=color_map,
        render_mode="svg" # 고품질 렌더링
    )

    annotations = []
    for region in selected_regions:
        reg_data = df_sel_sorted[df_sel_sorted['지역'] == region]
        reg_color = color_map.get(region, "#000000")
        
        # 모든 구간에 화살표 추가
        for i in range(len(reg_data) - 1):
            curr = reg_data.iloc[i]
            nxt = reg_data.iloc[i+1]
            
            annotations.append(dict(
                x=nxt['매매지수'], y=nxt['전세지수'],
                ax=curr['매매지수'], ay=curr['전세지수'],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5,
                arrowcolor=reg_color, opacity=0.7
            ))
            
        # 마지막 포인트 지역명 표시
        if not reg_data.empty:
            last = reg_data.iloc[-1]
            annotations.append(dict(
                x=last['매매지수'], y=last['전세지수'],
                text=f"<b>{region}</b>", showarrow=False,
                yshift=15, font=dict(size=12, color=reg_color),
                bgcolor="rgba(255, 255, 255, 0.8)"
            ))

    fig.update_layout(
        annotations=annotations,
        title=f"부동산 4분면 경로 (4주 단위 샘플링)",
        xaxis_title="매매지수", yaxis_title="전세지수",
        height=750, template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)
