import pandas as pd
import ipywidgets as iw
import plotly.express as px
from ipywidgets import interactive_output
from IPython.display import display

# --- 1. 파일 불러오기 및 데이터 전처리 ---
# 파일 경로를 원래대로 직접 지정합니다.
# 이 경로에 분석할 엑셀 파일이 있어야 합니다.
file_path = "C:/Users/terra/OneDrive/바탕 화면/부동산4분면/20250818_주간시계열.xlsx"

try:
    # 매매지수와 전세지수 데이터를 엑셀 파일에서 읽어옵니다.
    sale = pd.read_excel(file_path, sheet_name="3.매매지수", skiprows=[0, 2, 3])
    rent = pd.read_excel(file_path, sheet_name="4.전세지수", skiprows=[0, 2, 3])

    # '구분' 열에 데이터가 없는 행을 제거합니다.
    sale.dropna(subset=['구분'], inplace=True)
    rent.dropna(subset=['구분'], inplace=True)

    # 비어있는 값(NaN)을 0으로 채웁니다.
    sale.fillna(0, inplace=True)
    rent.fillna(0, inplace=True)
    
    # 경고 방지를 위해 데이터 타입을 추론하여 설정합니다.
    sale = sale.infer_objects(copy=False)
    rent = rent.infer_objects(copy=False)

    # '구분' 열의 이름을 '날짜'로 변경합니다.
    sale.rename(columns={'구분': '날짜'}, inplace=True)
    rent.rename(columns={'구분': '날짜'}, inplace=True)

    # 데이터를 '긴' 형태로 변환합니다 (Melt).
    sale_melt = sale.melt(id_vars=['날짜'], var_name='지역', value_name='매매지수')
    rent_melt = rent.melt(id_vars=['날짜'], var_name='지역', value_name='전세지수')

    # 매매와 전세 데이터를 '날짜'와 '지역'을 기준으로 합칩니다.
    df = pd.merge(sale_melt, rent_melt, on=['날짜', '지역'])

    # '날짜' 열을 날짜/시간 형식으로 변환합니다.
    df['날짜'] = pd.to_datetime(df['날짜'])

    # --- 2. 사용자 입력을 위한 위젯 생성 ---
    startdate = iw.DatePicker(
        description='시작날짜',
        value=df['날짜'].min().date(), # 기본값으로 가장 빠른 날짜 설정
        disabled=False
    )

    enddate = iw.DatePicker(
        description='종료날짜',
        value=df['날짜'].max().date(), # 기본값으로 가장 마지막 날짜 설정
        disabled=False
    )

    region = iw.SelectMultiple(
        options=sorted(df['지역'].unique()), # 지역 목록을 가나다순으로 정렬
        value=sorted(df['지역'].unique())[:3], # 기본 선택값으로 처음 3개 지역 설정
        description='지역 선택',
        disabled=False,
        rows=10 # 위젯의 높이를 10줄로 설정
    )

    # --- 3. 그래프를 그리는 함수 정의 ---
    def plot_quadrant_chart(startdate, enddate, region):
        if not startdate or not enddate or not region:
            print("날짜와 지역을 선택하세요.")
            return

        # 위젯 값(datetime.date)을 pandas가 인식할 수 있는 datetime 형식으로 변환
        start_dt = pd.to_datetime(startdate)
        end_dt = pd.to_datetime(enddate)
        
        # 선택된 조건으로 데이터 필터링
        mask = (df["날짜"] >= start_dt) & (df["날짜"] <= end_dt) & (df["지역"].isin(region))
        df_sel = df[mask]

        if df_sel.empty:
            print("선택한 조건에 맞는 데이터가 없습니다.")
            return
            
        # 날짜순으로 데이터 정렬
        df_sel_sorted = df_sel.sort_values(by='날짜')

        # Plotly Express를 사용하여 경로 그래프 생성
        fig = px.line(
            df_sel_sorted,
            x="매매지수",
            y="전세지수",
            color="지역",
            markers=True,
            hover_data={'날짜': '|%Y-%m-%d', '지역': True}
        )

        # 각 지역의 마지막 지점을 찾아 주석(Annotation) 추가
        last_points = df_sel_sorted.loc[df_sel_sorted.groupby('지역')['날짜'].idxmax()]
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

        # 그래프 레이아웃 업데이트
        date_format = "%Y년 %m월 %d일"
        fig.update_layout(
            title=f"<b>부동산 4분면 경로 ({start_dt.strftime(date_format)} ~ {end_dt.strftime(date_format)})</b>",
            xaxis_title="매매지수",
            yaxis_title="전세지수",
            height=700,
            legend_title_text='지역',
            xaxis=dict(gridcolor='lightgrey'),
            yaxis=dict(gridcolor='lightgrey'),
            plot_bgcolor='white'
        )

        # 0을 기준으로 수평/수직선 추가
        fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="black")
        fig.add_vline(x=0, line_width=1, line_dash="dash", line_color="black")
        
        fig.show()

    # --- 4. 위젯과 함수 연결 및 표시 ---
    # 위젯 UI 구성
    ui = iw.HBox([iw.VBox([startdate, enddate]), region])
    
    # 위젯의 값 변경에 따라 함수가 실행되도록 연결
    out = interactive_output(plot_quadrant_chart, {
        "startdate": startdate,
        "enddate": enddate,
        "region": region
    })

    # UI와 결과 출력
    display(ui, out)

except FileNotFoundError:
    print(f"오류: '{file_path}' 경로에서 파일을 찾을 수 없습니다. 파일 경로를 확인해주세요.")
except Exception as e:
    print(f"데이터를 처리하는 중 오류가 발생했습니다: {e}")
