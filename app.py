# --- 그래프 시각화 (끝점 화살표 버전) ---
if df_filtered.empty:
    st.warning("선택한 조건에 맞는 데이터가 없습니다.")
else:
    # 1. 필터링된 전체 데이터를 사용 (샘플링 없이 부드러운 선 표시)
    df_sel_sorted = df_filtered.sort_values(by=['지역', '날짜'])

    # 2. 기본 라인 그래프 (Plotly 기본 기능을 사용하여 매우 빠름)
    fig = px.line(
        df_sel_sorted, 
        x="매매지수", 
        y="전세지수", 
        color="지역",
        hover_data=['날짜', '지역'],
        color_discrete_map=color_map,
        markers=True # 각 주차별 포인트는 점으로 표시
    )

    # 3. 각 지역의 마지막 지점에 '방향 화살표'와 '지역명' 추가
    for region in selected_regions:
        reg_data = df_sel_sorted[df_sel_sorted['지역'] == region]
        if len(reg_data) >= 2:
            last = reg_data.iloc[-1]   # 최신 데이터
            prev = reg_data.iloc[-2]   # 바로 직전 데이터 (방향 결정용)
            reg_color = color_map.get(region, "#000000")
            
            # 화살표 추가 (직전 데이터에서 현재 데이터 방향으로)
            fig.add_annotation(
                x=last['매매지수'],
                y=last['전세지수'],
                ax=prev['매매지수'],
                ay=prev['전세지수'],
                xref="x", yref="y",
                axref="x", ayref="y",
                text="", 
                showarrow=True,
                arrowhead=3,      # 화살촉 모양
                arrowsize=1.5,    # 화살촉 크기
                arrowwidth=2.5,   # 화살촉 두께
                arrowcolor=reg_color
            )
            
            # 지역 이름 라벨
            fig.add_annotation(
                x=last['매매지수'],
                y=last['전세지수'],
                text=f"<b>{region}</b>",
                showarrow=False,
                yshift=18,        # 화살표와 겹치지 않게 위로 올림
                font=dict(size=13, color=reg_color),
                bgcolor="rgba(255, 255, 255, 0.8)"
            )

    # 그래프 레이아웃 최적화
    fig.update_layout(
        title=f"부동산 4분면 지수 경로 ({start_date} ~ {end_date})",
        xaxis_title="매매지수",
        yaxis_title="전세지수",
        height=750,
        template="plotly_white",
        hovermode="closest"
    )

    # 가독성을 위한 그리드 설정
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='f0f0f0')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='f0f0f0')

    st.plotly_chart(fig, use_container_width=True)
