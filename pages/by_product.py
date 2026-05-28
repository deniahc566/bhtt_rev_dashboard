import streamlit as st
import pandas as pd
import altair as alt

from data_loader import load_partner_data
from ui_helpers import (
    render_action_buttons, fmt_currency, kpi_card, yoy_caption,
    _fmt_vnd, _chart_title, channel_display,
)


def render_by_product_page():
    st.markdown(
        '<style>section[data-testid="stMain"]{zoom:1;}</style>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h1 style="font-size:1.4rem;font-weight:700;white-space:nowrap;margin-bottom:0.5rem;">'
        'BÁO CÁO DOANH THU — CHI TIẾT THEO SẢN PHẨM</h1>',
        unsafe_allow_html=True,
    )
    render_action_buttons()

    try:
        full_df = load_partner_data()
    except Exception as e:
        st.error(f"Không thể tải dữ liệu: {e}")
        return

    if full_df.empty:
        st.warning("Chưa có dữ liệu. Hãy chạy extract_partner_data.py và build_partner_rev.py trước.")
        return

    full_df["ten_kenh"] = full_df.apply(
        lambda r: channel_display(r["nguon_kt"], r["ten_nguon_kt"]), axis=1
    )

    # ── Product group selector ─────────────────────────────────────────────────
    group_options = sorted(full_df["product_group"].unique().tolist())
    selected_group = st.selectbox("Chọn nhóm sản phẩm", options=group_options, index=0)
    grp_full = full_df[full_df["product_group"] == selected_group]

    # ── Year filter ────────────────────────────────────────────────────────────
    all_years = sorted(grp_full["nam"].dropna().unique().astype(int).tolist(), reverse=True)
    default_years = [all_years[0]] if all_years else []
    selected_years = st.multiselect(
        "Năm",
        options=all_years,
        default=default_years,
        placeholder="Chọn năm...",
        key="by_product_years",
    )
    df = grp_full[grp_full["nam"].isin(selected_years)] if selected_years else grp_full

    if df.empty:
        st.warning("Không có dữ liệu cho bộ lọc đã chọn.")
        return

    # ── KPI ───────────────────────────────────────────────────────────────────
    tong_tien = df["tien_thuc_thu"].sum()
    tong_don  = int(df["so_don_cap_moi"].sum())

    sorted_months = sorted(df["ngay_ban_hang"].dt.to_period("M").unique())
    last_month = sorted_months[-1]
    last_df = df[df["ngay_ban_hang"].dt.to_period("M") == last_month]
    delta_tien = last_df["tien_thuc_thu"].sum()
    delta_don  = int(last_df["so_don_cap_moi"].sum())

    current_year = selected_years[0] if selected_years else int(df["nam"].max())
    prev_year    = current_year - 1
    yoy_df   = grp_full[grp_full["nam"] == prev_year]
    yoy_tien = yoy_df["tien_thuc_thu"].sum()
    yoy_don  = int(yoy_df["so_don_cap_moi"].sum())

    st.markdown(
        f'<p style="font-size:0.78rem;color:#888;margin-bottom:4px">'
        f'↕ Mũi tên xanh/đỏ: tháng gần nhất ({last_month})</p>',
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    with cols[0]:
        _ds = "+" if delta_tien >= 0 else ""
        st.markdown(kpi_card(
            label="Tổng phí doanh thu",
            value=fmt_currency(tong_tien),
            delta_str=f"{_ds}{fmt_currency(delta_tien)}",
            delta_color="#2e7d32",
            accent_color="#2C4C7B",
            yoy_html=yoy_caption(tong_tien, yoy_tien, fmt_currency, prev_year),
        ), unsafe_allow_html=True)
    with cols[1]:
        st.markdown(kpi_card(
            label="Tổng số hợp đồng",
            value=f"{tong_don:,}",
            delta_str=f"+{delta_don:,}",
            delta_color="#2e7d32",
            accent_color="#6A415E",
            yoy_html=yoy_caption(tong_don, yoy_don, lambda v: f"{int(v):,}", prev_year),
        ), unsafe_allow_html=True)

    # ── Rolling 12-month source ────────────────────────────────────────────────
    _latest = grp_full["ngay_ban_hang"].max()
    _cutoff  = (_latest - pd.DateOffset(months=11)).replace(day=1)
    src12 = grp_full[grp_full["ngay_ban_hang"] >= _cutoff].copy()
    src12["Tháng"] = src12["ngay_ban_hang"].dt.to_period("M").astype(str)
    df["Tháng"]    = df["ngay_ban_hang"].dt.to_period("M").astype(str)

    st.markdown('<div style="margin-top:24px;"></div>', unsafe_allow_html=True)

    # ── Row 1: Revenue by channel | Revenue by LHNV ───────────────────────────
    col_kenh, col_lhnv = st.columns(2)

    with col_kenh:
        _chart_title("Phí doanh thu theo kênh")
        rev_kenh = (
            df.groupby("ten_kenh", as_index=False)["tien_thuc_thu"]
            .sum()
            .sort_values("tien_thuc_thu", ascending=False)
        )
        rev_kenh["label"] = rev_kenh["tien_thuc_thu"].apply(_fmt_vnd)
        kenh_order = rev_kenh["ten_kenh"].tolist()
        chart_kenh = (
            alt.Chart(rev_kenh)
            .mark_bar(color="#2C4C7B", cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
            .encode(
                y=alt.Y("ten_kenh:N", title=None, sort=kenh_order,
                        axis=alt.Axis(labelFontSize=11)),
                x=alt.X("tien_thuc_thu:Q", title="Phí doanh thu (VND)",
                        axis=alt.Axis(format="~s", labelFontSize=10)),
                tooltip=[
                    alt.Tooltip("ten_kenh:N", title="Kênh"),
                    alt.Tooltip("tien_thuc_thu:Q", title="Phí doanh thu", format=",.0f"),
                ],
            )
        )
        text_kenh = chart_kenh.mark_text(align="left", dx=4, fontSize=10, color="#333").encode(text="label:N")
        st.altair_chart(
            (chart_kenh + text_kenh).properties(height=max(200, len(kenh_order) * 36)),
            use_container_width=True,
        )

    with col_lhnv:
        _chart_title("Phí doanh thu theo mã nghiệp vụ (LHNV)")
        rev_lhnv = (
            df.groupby("lhnv", as_index=False)["tien_thuc_thu"]
            .sum()
            .sort_values("tien_thuc_thu", ascending=False)
            .head(15)
        )
        rev_lhnv["label"] = rev_lhnv["tien_thuc_thu"].apply(_fmt_vnd)
        lhnv_order = rev_lhnv["lhnv"].tolist()
        chart_lhnv = (
            alt.Chart(rev_lhnv)
            .mark_bar(color="#6A415E", cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
            .encode(
                y=alt.Y("lhnv:N", title=None, sort=lhnv_order,
                        axis=alt.Axis(labelFontSize=11)),
                x=alt.X("tien_thuc_thu:Q", title="Phí doanh thu (VND)",
                        axis=alt.Axis(format="~s", labelFontSize=10)),
                tooltip=[
                    alt.Tooltip("lhnv:N", title="LHNV"),
                    alt.Tooltip("tien_thuc_thu:Q", title="Phí doanh thu", format=",.0f"),
                ],
            )
        )
        text_lhnv = chart_lhnv.mark_text(align="left", dx=4, fontSize=10, color="#333").encode(text="label:N")
        st.altair_chart(
            (chart_lhnv + text_lhnv).properties(height=max(200, len(lhnv_order) * 36)),
            use_container_width=True,
        )

    # ── Row 2: Monthly multi-line by channel ───────────────────────────────────
    st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
    _chart_title("Xu hướng doanh thu theo tháng — theo kênh (12 tháng gần nhất)")

    top_channels = (
        src12.groupby("ten_kenh")["tien_thuc_thu"]
        .sum()
        .nlargest(6)
        .index.tolist()
    )
    line_src = src12[src12["ten_kenh"].isin(top_channels)]
    line_df = (
        line_src.groupby(["Tháng", "ten_kenh"], as_index=False)["tien_thuc_thu"].sum()
    )
    chart_line = (
        alt.Chart(line_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("Tháng:N", title=None, sort=None,
                    axis=alt.Axis(labelAngle=-45, labelFontSize=10)),
            y=alt.Y("tien_thuc_thu:Q", title="Phí doanh thu (VND)",
                    axis=alt.Axis(format="~s", labelFontSize=10)),
            color=alt.Color("ten_kenh:N", title="Kênh",
                            scale=alt.Scale(scheme="tableau10")),
            tooltip=[
                alt.Tooltip("Tháng:N", title="Tháng"),
                alt.Tooltip("ten_kenh:N", title="Kênh"),
                alt.Tooltip("tien_thuc_thu:Q", title="Phí doanh thu", format=",.0f"),
            ],
        )
        .properties(height=280)
    )
    st.altair_chart(chart_line, use_container_width=True)

    # ── Row 3: Detail table by month + channel ─────────────────────────────────
    st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
    _chart_title("Chi tiết theo tháng và kênh")

    detail = (
        df.groupby(["Tháng", "ten_kenh"], as_index=False)
        .agg(tien_thuc_thu=("tien_thuc_thu", "sum"), so_don=("so_don_cap_moi", "sum"))
        .sort_values(["Tháng", "tien_thuc_thu"], ascending=[True, False])
    )
    detail["Phí doanh thu"] = detail["tien_thuc_thu"].apply(_fmt_vnd)
    detail["Số hợp đồng"]   = detail["so_don"].apply(lambda v: f"{int(v):,}")
    detail = detail[["Tháng", "ten_kenh", "Phí doanh thu", "Số hợp đồng"]].rename(
        columns={"ten_kenh": "Kênh"}
    )
    st.dataframe(detail, use_container_width=True, hide_index=True)
