import pandas as pd
import plotly.express as px
import streamlit as st

# --- 데이터 로딩 및 전처리 함수 ---
# @st.cache_data를 사용해 데이터 로딩을 캐싱하여 앱 성능을 향상시킵니다.
# 앱을 다시 실행해도 파일은 한 번만 읽어옵니다.
@st.cache_data
def load_data(file_path):
    """지정된 경로의 엑셀 파일을 읽어와 전처리 후 데이터프레임을 반환합니다."""
    # 매매지수와 전세지수 시트 불러오기
    try:
        sale = pd.read_excel(file_path, sheet_name="3.매매지수", skiprows=[0, 2, 3])
        rent = pd.read_excel(file_path, sheet_name="4.전세지수", skiprows=[0, 2, 3])
    except Exception as e:
        # 파일 로딩 중 오류 발생 시 None 반환
        st.error(f"엑셀 파일 로딩 중 오류가 발생했습니다: {e}")
        return None

    # 데이터 클리닝
    sale = sale.dropna(subset=['구분'])
    rent = rent.dropna(subset=['구분'])
    sale = sale.fillna(0).infer_objects(copy=False)
    rent = rent.fillna(0).infer_objects(copy=False)

    # 컬럼명 변경
    sale.rename(columns={'구분': '날짜'}, inplace=True)
    rent.rename(columns={'구분': '날짜'}, inplace=True)

    # 데이터를 'wide'에서 'long' 형태로 변환 (Melt)
    sale_melt = sale.melt(id_vars=['날짜'], var_name='지역', value_name='매매지수')
    rent_melt = rent.melt(id_vars=['날짜'], var_name='지역', value_name='전세지수')

    # 매매와 전세 데이터 병합
    df = pd.merge(sale_melt, rent_melt, on=['날짜', '지역'])
    
    # 날짜 컬럼을 datetime 형식으로 변환
    df['날짜'] = pd.to_datetime(df['날짜'])
    return df

# --- 메인 앱 로직 ---

file_path = "20250922_주간시계열.xlsx"
df = load_data(file_path)


# 1. 페이지 기본 설정 (제목, 레이아웃 등)
st.set_page_config(page_title="부동산 4분면 분석", layout="wide")
st.title("📈 부동산 4분면 경로 분석")

# 2. 데이터 파일 업로드 기능
# 사용자가 직접 파일을 올리도록 하여, 로컬 경로 문제를 해결하고 배포에 용이하게 만듭니다.
uploaded_file = st.file_uploader("주간 시계열 엑셀 파일을 업로드해주세요.", type=['xlsx'])

# 파일이 업로드되었을 때만 앱의 나머지 부분을 실행
if uploaded_file is not None:
    df = load_data(uploaded_file)
    
    # 데이터 로딩이 성공했을 경우에만 진행
    if df is not None:
        # 3. 사이드바에 필터 위젯 배치
        st.sidebar.header("🔎 필터 옵션")

        # 지역 목록 정렬 (주요 도시 우선)
        all_regions = df['지역'].unique()
        major_divisions = [
            "전국", "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
            "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"
        ]
        major_regions_found = [region for region in major_divisions if region in all_regions]
        minor_regions_found = sorted([region for region in all_regions if region not in major_regions_found])
        sorted_region_options = major_regions_found + minor_regions_found

        # Streamlit 지역 선택 멀티-셀렉트 위젯
        selected_regions = st.sidebar.multiselect(
            '지역 선택',
            options=sorted_region_options,
            default=sorted_region_options[:3]
        )

        # Streamlit 날짜 범위 선택 위젯
        min_date = df['날짜'].min().date()
        max_date = df['날짜'].max().date()
        selected_dates = st.sidebar.date_input(
            "날짜 범위 선택",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

        # 날짜 범위가 올바르게 선택되었는지 확인
        if len(selected_dates) != 2:
            st.sidebar.warning("시작 날짜와 종료 날짜를 모두 선택해주세요.")
            st.stop()
        start_date, end_date = selected_dates

        # 4. 선택된 값으로 데이터 필터링
        mask = (df["날짜"] >= pd.to_datetime(start_date)) & \
               (df["날짜"] <= pd.to_datetime(end_date)) & \
               (df["지역"].isin(selected_regions))
        df_sel = df[mask]

        # 5. 그래프 생성 및 출력
        if df_sel.empty:
            st.warning("선택하신 조건에 해당하는 데이터가 없습니다. 다른 필터 값을 선택해주세요.")
        else:
            df_sel_sorted = df_sel.sort_values(by='날짜')

            fig = px.line(
                df_sel_sorted,
                x="매매지수",
                y="전세지수",
                color="지역",
                markers=True,
                hover_data={'날짜': '|%Y-%m-%d', '지역': True} # 날짜 포맷 지정
            )
            
            # 각 지역의 최종점에 지역명 텍스트 추가
            last_points = df_sel_sorted.loc[df_sel_sorted.groupby('지역')['날짜'].idxmax()]
            for _, row in last_points.iterrows():
                fig.add_annotation(
                    x=row['매매지수'], y=row['전세지수'],
                    text=row['지역'], showarrow=False, yshift=10,
                    font=dict(size=12, color="black"),
                    bgcolor="rgba(255, 255, 255, 0.6)"
                )

            # 그래프 레이아웃 설정
            fig.update_layout(
                title=f"부동산 4분면 경로 ({start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')})",
                xaxis_title="매매지수",
                yaxis_title="전세지수",
                height=700,
                legend_title_text='지역'
            )
            
            # st.plotly_chart를 사용해 그래프를 앱에 표시
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("데이터를 분석하려면 먼저 엑셀 파일을 업로드해주세요.")

