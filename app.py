import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# --- 데이터 로딩 및 전처리 (Streamlit 캐싱 기능 추가) ---
@st.cache_data
def load_data(uploaded_file):
    """
    업로드된 Excel 파일을 로드하고 전처리하는 함수입니다.
    @st.cache_data 데코레이터를 사용하여 데이터 로딩 결과를 캐싱하여,
    위젯 값이 변경될 때마다 파일을 다시 읽지 않도록 하여 성능을 향상시킵니다.
    """
    try:
        # 매매증감 데이터 로드
        sale = pd.read_excel(uploaded_file, sheet_name="1.매매증감", skiprows=[0, 2, 3], engine='openpyxl')
        sale = sale.dropna(subset=['구분'])
        sale = sale.fillna(0).infer_objects(copy=False)
        sale.rename(columns={'구분': '날짜'}, inplace=True)

        # 전세증감 데이터 로드
        rent = pd.read_excel(uploaded_file, sheet_name="2.전세증감", skiprows=[0, 2, 3], engine='openpyxl')
        rent = rent.dropna(subset=['구분'])
        rent = rent.fillna(0).infer_objects(copy=False)
        rent.rename(columns={'구분': '날짜'}, inplace=True)

        # Melt 함수를 사용하여 데이터를 'long' 형태로 변환
        sale_melt = sale.melt(id_vars=['날짜'], var_name='지역', value_name='매매증감률')
        rent_melt = rent.melt(id_vars=['날짜'], var_name='지역', value_name='전세증감률')

        # 매매와 전세 데이터를 '날짜'와 '지역'을 기준으로 병합
        df = pd.merge(sale_melt, rent_melt, on=['날짜', '지역'])
        df['날짜'] = pd.to_datetime(df['날짜'])
        return df
    except Exception as e:
        st.error(f"파일을 처리하는 중 오류가 발생했습니다: {e}")
        return None

# --- Streamlit 앱 UI 구성 ---

# 페이지 기본 설정
st.set_page_config(layout="wide", page_title="부동산 4분면 분석")

st.title("🏙️ 부동산 4분면 분석 대시보드")
st.markdown("매매증감률과 전세증감률 데이터를 기반으로 부동산 시장의 추세를 시각적으로 분석합니다.")

# --- 사이드바: 파일 업로드 및 필터 ---
st.sidebar.header("⚙️ 설정")
uploaded_file = st.sidebar.file_uploader("📂 주간 시계열 엑셀 파일을 업로드하세요.", type=['xlsx'])

# 파일이 업로드된 경우에만 필터와 차트를 표시
if uploaded_file is not None:
    df = load_data(uploaded_file)

    if df is not None:
        st.sidebar.markdown("---")
        st.sidebar.header("🗓️ 기간 및 지역 선택")

        # 1. 날짜 선택 위젯 (st.date_input 사용)
        start_date = st.sidebar.date_input(
            "시작 날짜",
            value=df["날짜"].min().date(),
            min_value=df["날짜"].min().date(),
            max_value=df["날짜"].max().date()
        )
        end_date = st.sidebar.date_input(
            "종료 날짜",
            value=df["날짜"].max().date(),
            min_value=df["날짜"].min().date(),
            max_value=df["날짜"].max().date()
        )

        # 2. 지역 선택 위젯 (st.multiselect 사용)
        all_regions = sorted(df["지역"].unique())
        
        # '전체 선택' 체크박스 추가
        select_all = st.sidebar.checkbox("모든 지역 선택")

        if select_all:
            # '전체 선택'이 체크되면 모든 지역을 기본값으로 설정
            selected_regions = st.sidebar.multiselect(
                "분석할 지역 선택",
                options=all_regions,
                default=all_regions
            )
        else:
            # '전체 선택'이 체크되지 않으면 처음 3개 지역을 기본값으로 설정
            selected_regions = st.sidebar.multiselect(
                "분석할 지역 선택",
                options=all_regions,
                default=all_regions[:3]
            )

        # --- 메인 패널: 차트 및 데이터 표시 ---
        if not selected_regions:
            st.warning("분석할 지역을 1개 이상 선택하세요.")
        else:
            # 선택된 값으로 데이터 필터링 (날짜 형식 변환 후 비교)
            start_datetime = pd.to_datetime(start_date)
            end_datetime = pd.to_datetime(end_date)
            
            mask = (df["날짜"] >= start_datetime) & \
                   (df["날짜"] <= end_datetime) & \
                   (df["지역"].isin(selected_regions))
            df_sel = df[mask]

            st.header("📈 4분면 경로 분석")
            st.markdown(f"**선택 기간:** `{start_date}` ~ `{end_date}`")

            if df_sel.empty:
                st.warning("선택한 조건에 맞는 데이터가 없습니다. 기간이나 지역을 다시 선택해주세요.")
            else:
                # 날짜 기준으로 데이터 정렬
                df_sel_sorted = df_sel.sort_values(by=['지역', '날짜'])

                # Plotly를 사용한 경로 그래프 생성
                fig = px.line(
                    df_sel_sorted,
                    x="매매증감률",
                    y="전세증감률",
                    color="지역",
                    markers=True,
                    hover_data={
                        '날짜': '|%Y-%m-%d', 
                        '지역': True, 
                        '매매증감률': ':.2f', 
                        '전세증감률': ':.2f'
                    }
                )
                
                # 그래프 레이아웃 설정 (제목, 축 제목, 0 기준선 추가 등)
                fig.update_layout(
                    title=dict(text="<b>부동산 4분면 경로</b>", x=0.5, font=dict(size=20)),
                    xaxis_title="매매증감률 (%)",
                    yaxis_title="전세증감률 (%)",
                    height=600,
                    legend_title_text='지역',
                    xaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='LightGray'),
                    yaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='LightGray'),
                )
                
                # 0점을 기준으로 하는 수직선과 수평선 추가
                fig.add_vline(x=0, line_width=1, line_dash="dash", line_color="black")
                fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="black")

                # Streamlit에 차트 표시
                st.plotly_chart(fig, use_container_width=True)

                # 데이터 테이블 표시
                st.markdown("---")
                st.header("📄 필터링된 데이터")
                st.dataframe(df_sel.style.format({
                    "매매증감률": "{:.2f}%",
                    "전세증감률": "{:.2f}%",
                    "날짜": lambda t: t.strftime('%Y-%m-%d')
                }))
else:
    st.info("⬆️ 사이드바에서 엑셀 파일을 업로드하여 분석을 시작하세요.")
