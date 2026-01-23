import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
st.sidebar.header("🗓️ 필터")
selected_dates = st.sidebar.date_input(
    "날짜 범위",
    value=(df["날짜"].min(), df["날짜"].max()),
    min_value=df["날짜"].min(),
    max_value=df["날짜"].max(),
)

if len(selected_dates) != 2:
    st.sidebar.error("날짜 범위를 선택하세요.")
    st.stop()
start_date, end_date = selected_dates

all_regions = df["지역"].unique()
selected_regions = st.sidebar.multiselect("지역 선택", options=all_regions, default=all_regions[:3])

st.sidebar.header("🎨 색상")
color_map = {reg: st.sidebar.color_picker(f"{reg}", px.colors.qualitative.Plotly[i%10]) 
             for i, reg in enumerate(selected_regions)}

# --- 메인 화면 ---
st.title("부동산 매매/전세 가격 경로 분석")

# --- 데이터 필터링 ---
mask = (df["날짜"] >= pd.to_datetime(start_date)) & \
       (df["날짜"] <= pd.to_datetime(end_date)) & \
       (df["지역"].isin(selected_regions))
df_sel = df[mask].sort_values(['지역', '날짜'])

if df_sel.empty:
    st.warning("데이터가 없습니다.")
else:
    # 기본 라인 차트 생성
    fig = go.Figure()

    for region in selected_regions:
        rdf = df_sel[df_sel['지역'] == region]
        if rdf.empty: continue
        
        reg_color = color_map.get(region, "black")

        # 1. 경로 선 추가
        fig.add_trace(go.Scatter(
            x=rdf['매매지수'], y=rdf['전세지수'],
            mode='lines+markers',
            name=region,
            line=dict(color=reg_color, width=2),
            marker=dict(size=4, opacity=0.5),
            hoverinfo='text',
            text=[f"{region}<br>{d.strftime('%Y-%m-%d')}<br>매매:{s}<br>전세:{r}" 
                  for d, s, r in zip(rdf['날짜'], rdf['매매지수'], rdf['전세지수'])]
        ))

        # 2. 유동적 진행 화살표 추가 (중간중간 흐름 표시)
        # 데이터가 너무 많으면 지저분하므로 4개 포인트마다 화살표 생성
        step = max(1, len(rdf) // 5) 
        for i in range(step, len(rdf), step):
            curr = rdf.iloc[i]
            prev = rdf.iloc[i-1]
            
            fig.add_annotation(
                x=curr['매매지수'], y=curr['전세지수'],
                ax=prev['매매지수'], ay=prev['전세지수'],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=1.5,
                arrowcolor=reg_color, opacity=0.8
            )

        # 3. 최신 지점(현재) 강조 레이블
        last = rdf.iloc[-1]
        fig.add_annotation(
            x=last['매매지수'], y=last['전세지수'],
            text=f"<b>{region} (현재)</b>",
            showarrow=False, yshift=15,
            font=dict(color="white", size=11),
            bgcolor=reg_color, borderpad=4, opacity=1
        )

        # 4. 시작 지점 표시
        first = rdf.iloc[0]
        fig.add_trace(go.Scatter(
            x=[first['매매지수']], y=[first['전세지수']],
            mode='markers+text',
            text=["START"], textposition="bottom center",
            marker=dict(color="grey", size=8, symbol="circle"),
            showlegend=False
        ))

    # 레이아웃 설정
    fig.update_layout(
        title=f"부동산 지수 경로 분석 ({start_date} ~ {end_date})",
        xaxis_title="매매지수", yaxis_title="전세지수",
        template="plotly_white",
        height=700,
        hovermode="closest"
    )

    st.plotly_chart(fig, use_container_width=True)

