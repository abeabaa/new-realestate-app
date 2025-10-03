import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Page Configuration ---
# Set the layout and title for the Streamlit page.
st.set_page_config(layout="wide", page_title="부동산 4분면 분석 앱")

# --- Title ---
st.title("📈 부동산 4분면 경로 분석")
st.write("매매지수와 전세지수의 변화를 시각적으로 분석하여 시장 동향을 파악합니다.")

# --- Data Caching ---
# Use st.cache_data to load and process data only once.
# This improves performance by avoiding re-computation on every interaction.
@st.cache_data
def load_data(uploaded_file):
    """
    Loads and preprocesses the real estate data from an Excel file.
    """
    try:
        # Read sales and rent index sheets from the uploaded Excel file.
        sale = pd.read_excel(uploaded_file, sheet_name="3.매매지수", skiprows=[0, 2, 3])
        rent = pd.read_excel(uploaded_file, sheet_name="4.전세지수", skiprows=[0, 2, 3])

        # --- Data Cleaning and Transformation ---
        # Drop rows where '구분' (division) is null.
        sale.dropna(subset=['구분'], inplace=True)
        rent.dropna(subset=['구분'], inplace=True)

        # Fill any remaining NaN values with 0.
        sale.fillna(0, inplace=True)
        rent.fillna(0, inplace=True)
        
        # Infer object types to prevent warnings.
        sale = sale.infer_objects(copy=False)
        rent = rent.infer_objects(copy=False)

        # Rename '구분' column to '날짜' (Date).
        sale.rename(columns={'구분': '날짜'}, inplace=True)
        rent.rename(columns={'구분': '날짜'}, inplace=True)

        # Melt the dataframes from wide to long format.
        sale_melt = sale.melt(id_vars=['날짜'], var_name='지역', value_name='매매지수')
        rent_melt = rent.melt(id_vars=['날짜'], var_name='지역', value_name='전세지수')

        # Merge the sales and rent dataframes on '날짜' and '지역'.
        df_merged = pd.merge(sale_melt, rent_melt, on=['날짜', '지역'])

        # Convert the '날짜' column to datetime objects.
        df_merged['날짜'] = pd.to_datetime(df_merged['날짜'])
        
        return df_merged
    except Exception as e:
        st.error(f"파일을 처리하는 중 오류가 발생했습니다: {e}")
        return None

# --- Sidebar for User Inputs ---
st.sidebar.header("⚙️ 분석 설정")
uploaded_file = st.sidebar.file_uploader("📂 주간 시계열 엑셀 파일을 업로드하세요.", type=["xlsx"])
# --- 파일 경로 및 로고 이미지 설정 ---
# 🚨 app.py와 같은 폴더에 파일들이 있어야 합니다.
excel_file_path = "20250922_주간시계열.xlsx"
logo_image_path = "jak_logo.png" # 로고 파일 경로
df = load_data(excel_file_path)

# --- Main Application Logic ---
if uploaded_file is not None:
    df = load_data(excel_file_path)

    if df is not None and not df.empty:
        # Get unique regions and default selections.
        all_regions = sorted(df['지역'].unique())
        default_regions = all_regions[:3] if len(all_regions) >= 3 else all_regions

        # --- Sidebar Widgets for Filtering ---
        selected_regions = st.sidebar.multiselect(
            "📍 지역 선택",
            options=all_regions,
            default=default_regions
        )

        min_date = df['날짜'].min().to_pydatetime()
        max_date = df['날짜'].max().to_pydatetime()

        selected_date_range = st.sidebar.date_input(
            "📅 날짜 범위 선택",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            format="YYYY.MM.DD"
        )
        
        # Ensure two dates are selected for the range.
        if len(selected_date_range) == 2:
            start_date, end_date = selected_date_range
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)

            # --- Data Filtering based on User Input ---
            mask = (
                (df["날짜"] >= start_date) &
                (df["날짜"] <= end_date) &
                (df["지역"].isin(selected_regions))
            )
            df_sel = df[mask]

            # --- Chart Generation ---
            if not df_sel.empty:
                df_sel_sorted = df_sel.sort_values(by='날짜')

                # Create a line chart with markers to show the path of change.
                fig = px.line(
                    df_sel_sorted,
                    x="매매지수",
                    y="전세지수",
                    color="지역",
                    markers=True,
                    hover_data=['날짜', '지역']
                )

                # Find the last data point for each region to add annotations.
                last_points = df_sel_sorted.loc[df_sel_sorted.groupby('지역')['날짜'].idxmax()]

                # Add region name annotations at the end of each line.
                for _, row in last_points.iterrows():
                    fig.add_annotation(
                        x=row['매매지수'],
                        y=row['전세지수'],
                        text=f"<b>{row['지역']}</b>",
                        showarrow=False,
                        yshift=10,
                        font=dict(family="sans-serif", size=12, color="black"),
                        bgcolor="rgba(255, 255, 255, 0.6)"
                    )

                # --- Chart Layout and Display ---
                date_format = "%Y년 %m월 %d일"
                fig.update_layout(
                    title=f"<b>부동산 4분면 경로 ({start_date.strftime(date_format)} ~ {end_date.strftime(date_format)})</b>",
                    xaxis_title="매매지수",
                    yaxis_title="전세지수",
                    height=700,
                    legend_title_text='지역',
                    xaxis=dict(gridcolor='lightgrey'),
                    yaxis=dict(gridcolor='lightgrey'),
                    plot_bgcolor='white'
                )
                
                # Add horizontal and vertical lines at zero.
                fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="black")
                fig.add_vline(x=0, line_width=1, line_dash="dash", line_color="black")

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("선택하신 조건에 해당하는 데이터가 없습니다. 지역이나 날짜 범위를 다시 설정해주세요.")
        else:
            st.info("분석을 시작하려면 날짜 범위를 선택해주세요.")
else:
    st.info("분석을 시작하려면 사이드바에서 엑셀 파일을 업로드하세요.")


