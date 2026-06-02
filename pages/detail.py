import sys
from pathlib import Path
_HERE = Path(__file__).parent.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

import pandas as pd
import altair as alt
import streamlit as st

from data_loader import load_partner_data
from ui_helpers import (
    fmt_currency, kpi_card, _fmt_vnd,
    section_head, _chart_title, _chart_sub,
)

_BLUE  = "#1558d6"
_BLUE2 = "#4a7fe8"
_BLUE3 = "#0ea5e9"
_BLUE4 = "#c5d8fb"
_POS   = "#16a34a"
_NEG   = "#dc2626"
_MUTED = "#64748b"
_CARD  = "#ffffff"
_LINE  = "#d0d8e4"
_INK   = "#0d1a2e"

_LINE_COLORS = [_BLUE, _NEG, _BLUE3, _BLUE2, _BLUE4, "#9b72cf", "#4a7fa5"]

_DU_LICH_KEY = "ĐỐI TÁC DU LỊCH"


def render_detail_page() -> None:
    try:
        full_df = load_partner_data()
    except Exception as e:
        st.error(f"Không thể tải dữ liệu: {e}")
        return

    if full_df.empty:
        st.warning("Chưa có dữ liệu. Hãy chạy extract_partner_data.py và build_partner_rev.py trước.")
        return

    # ── Dữ liệu nền ───────────────────────────────────────────────────────────
    current_year = int(full_df["nam"].max())
    df = full_df[full_df["nam"] == current_year].copy()
    df["Tháng"] = df["ngay_ban_hang"].dt.to_period("M").astype(str)
    df["thang_so"] = df["ngay_ban_hang"].dt.month

    tong = df["tien_thuc_thu"].sum()

    # Top partner nhóm
    nhom_rev = (
        df.groupby("nhom_doi_tac", as_index=False)["tien_thuc_thu"].sum()
        .sort_values("tien_thuc_thu", ascending=False)
    )
    top_nhom      = nhom_rev.iloc[0]["nhom_doi_tac"] if len(nhom_rev) else "—"
    top_nhom_rev  = nhom_rev.iloc[0]["tien_thuc_thu"] if len(nhom_rev) else 0
    top_nhom_pct  = top_nhom_rev / tong * 100 if tong else 0

    # Tháng cao nhất
    monthly_total = df.groupby("thang_so", as_index=False)["tien_thuc_thu"].sum()
    best_month_row = monthly_total.sort_values("tien_thuc_thu", ascending=False).iloc[0]
    best_month_val  = best_month_row["tien_thuc_thu"]
    best_month_num  = int(best_month_row["thang_so"])

    so_nhom = df["nhom_doi_tac"].nunique()

    # ── KPI strip ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_card(
            label="Tổng lũy kế T1–T4",
            value=f"{tong / 1e9:,.2f} <span style='font-size:0.9rem;color:{_MUTED};font-weight:600;'>tỷ</span>",
            delta_str="Tổng doanh số đối tác lũy kế",
            delta_color=_MUTED,
            accent_color=_BLUE,
        ), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card(
            label="Đối tác lớn nhất",
            value=f"<span style='font-size:1.2rem;'>{top_nhom}</span>",
            delta_str=f"▲ {top_nhom_pct:.1f}% tỷ trọng",
            delta_color=_POS,
            accent_color=_BLUE2,
            subtitle=f"{top_nhom_rev / 1e9:,.2f} tỷ lũy kế",
        ), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card(
            label=f"DT cao nhất — T{best_month_num}.{current_year}",
            value=f"{best_month_val / 1e9:,.2f} <span style='font-size:0.9rem;color:{_MUTED};font-weight:600;'>tỷ</span>",
            delta_str="Tháng cao điểm trong năm",
            delta_color=_MUTED,
            accent_color=_BLUE3,
        ), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card(
            label="Số nhóm đối tác",
            value=f"{so_nhom} <span style='font-size:0.9rem;color:{_MUTED};font-weight:600;'>nhóm</span>",
            delta_str="iPay, Viettel, Grab, SHB, VPS...",
            delta_color=_MUTED,
            accent_color=_BLUE4,
        ), unsafe_allow_html=True)

    # ── Section 1: Diễn biến doanh thu theo tháng ─────────────────────────────
    section_head("Diễn biến doanh thu theo tháng")

    col_monthly, col_trend = st.columns([1.4, 1])

    with col_monthly:
        _chart_title("Tổng doanh thu đối tác theo tháng")
        _chart_sub(f"Tỷ đồng · {current_year}")

        month_df = (
            df.groupby("thang_so", as_index=False)["tien_thuc_thu"].sum()
            .sort_values("thang_so")
        )
        month_df["Tháng label"] = month_df["thang_so"].apply(lambda m: f"T{m}")
        month_df["label_b"] = (month_df["tien_thuc_thu"] / 1e9).apply(lambda v: f"{v:.2f}")

        bar = (
            alt.Chart(month_df)
            .mark_bar(color=_BLUE, cornerRadiusTopLeft=3, cornerRadiusTopRight=3, size=36)
            .encode(
                x=alt.X("Tháng label:N", title=None, sort=None,
                        axis=alt.Axis(labelFontSize=12, labelColor=_INK)),
                y=alt.Y("tien_thuc_thu:Q", title="Tỷ đồng",
                        axis=alt.Axis(format="~s", labelFontSize=10, labelColor=_MUTED)),
                tooltip=[
                    alt.Tooltip("Tháng label:N", title="Tháng"),
                    alt.Tooltip("tien_thuc_thu:Q", title="Doanh thu", format=",.0f"),
                ],
            )
        )
        text = bar.mark_text(align="center", dy=-8, fontSize=10, color=_INK, fontWeight="bold").encode(
            text="label_b:N"
        )
        st.altair_chart(
            (bar + text).properties(height=260).configure_view(strokeWidth=0),
            width='stretch',
        )

    with col_trend:
        _chart_title("Top 5 đối tác — xu hướng tháng")
        _chart_sub("iPay, Viettel, SHB, VPS, Grab (tỷ đồng)")

        top5_names = nhom_rev.head(5)["nhom_doi_tac"].tolist()
        trend_df = (
            df[df["nhom_doi_tac"].isin(top5_names)]
            .groupby(["thang_so", "nhom_doi_tac"], as_index=False)["tien_thuc_thu"]
            .sum()
            .sort_values("thang_so")
        )
        trend_df["Tháng label"] = trend_df["thang_so"].apply(lambda m: f"T{m}")

        line = (
            alt.Chart(trend_df)
            .mark_line(point=True, strokeWidth=2.2)
            .encode(
                x=alt.X("Tháng label:N", title=None, sort=None,
                        axis=alt.Axis(labelFontSize=11, labelColor=_INK)),
                y=alt.Y("tien_thuc_thu:Q", title="Tỷ đồng",
                        axis=alt.Axis(format="~s", labelFontSize=10, labelColor=_MUTED)),
                color=alt.Color(
                    "nhom_doi_tac:N", title="Nhóm",
                    scale=alt.Scale(domain=top5_names, range=_LINE_COLORS[:len(top5_names)]),
                    legend=alt.Legend(orient="bottom", labelFontSize=10, symbolStrokeWidth=3),
                ),
                tooltip=[
                    alt.Tooltip("Tháng label:N", title="Tháng"),
                    alt.Tooltip("nhom_doi_tac:N", title="Nhóm"),
                    alt.Tooltip("tien_thuc_thu:Q", title="Doanh thu", format=",.0f"),
                ],
            )
            .properties(height=260)
        )
        st.altair_chart(line.configure_view(strokeWidth=0), width='stretch')

    # ── Section 2: Bảng xếp hạng nhóm đối tác ────────────────────────────────
    section_head("Bảng xếp hạng nhóm đối tác")

    # Pivot theo tháng: lấy 4 tháng gần nhất
    pivot_months = sorted(df["thang_so"].unique())
    pivot_df = (
        df.groupby(["nhom_doi_tac", "thang_so"], as_index=False)["tien_thuc_thu"].sum()
    )
    nhom_lk = (
        df.groupby("nhom_doi_tac", as_index=False)["tien_thuc_thu"]
        .sum()
        .rename(columns={"tien_thuc_thu": "lk"})
        .sort_values("lk", ascending=False)
    )

    th = (
        f"font-size:0.65rem;font-weight:700;text-transform:uppercase;"
        f"color:{_BLUE};letter-spacing:0.07em;padding:8px 10px;"
        f"border-bottom:2px solid {_BLUE};"
    )
    month_headers = "".join(
        f'<th style="{th}text-align:right;">T{m}</th>' for m in pivot_months
    )
    table_rows = ""
    col_tong = 0.0
    col_months_sum = {m: 0.0 for m in pivot_months}

    for _, row in nhom_lk.iterrows():
        name = row["nhom_doi_tac"]
        lk   = row["lk"]
        share = lk / tong * 100 if tong else 0
        bar_w = max(share * 1.0, 2)
        col_tong += lk

        month_cells = ""
        for m in pivot_months:
            m_val = pivot_df[(pivot_df["nhom_doi_tac"] == name) & (pivot_df["thang_so"] == m)]["tien_thuc_thu"].sum()
            col_months_sum[m] += m_val
            m_b = m_val / 1e9
            month_cells += (
                f"<td style='text-align:right;padding:8px 10px;"
                f"border-bottom:1px solid {_LINE};"
                f"font-variant-numeric:tabular-nums;font-size:0.78rem;'>"
                f"{'—' if m_b == 0 else f'{m_b:.2f}'}</td>"
            )

        table_rows += (
            f"<tr>"
            f"<td style='text-align:left;font-weight:600;padding:8px 10px;"
            f"border-bottom:1px solid {_LINE};font-size:0.80rem;'>{name}</td>"
            f"{month_cells}"
            f"<td style='text-align:right;padding:8px 10px;border-bottom:1px solid {_LINE};"
            f"font-weight:700;font-size:0.80rem;font-variant-numeric:tabular-nums;'>"
            f"{lk / 1e9:.2f}</td>"
            f"<td style='text-align:right;padding:8px 10px;border-bottom:1px solid {_LINE};white-space:nowrap;'>"
            f"<span style='display:inline-block;width:{bar_w:.0f}px;height:6px;"
            f"background:{_BLUE};border-radius:3px;vertical-align:middle;margin-right:5px;'></span>"
            f"<span style='font-size:0.75rem;font-variant-numeric:tabular-nums;'>{share:.1f}%</span>"
            f"</td>"
            f"</tr>"
        )

    # Total row
    tot_month_cells = "".join(
        f"<td style='text-align:right;padding:8px 10px;font-weight:800;"
        f"font-variant-numeric:tabular-nums;font-size:0.78rem;'>"
        f"{col_months_sum[m] / 1e9:.2f}</td>"
        for m in pivot_months
    )
    tot_style = (
        f"font-weight:800;border-top:2px solid {_BLUE};border-bottom:none;"
        f"background:{_BLUE4};padding:8px 10px;font-variant-numeric:tabular-nums;"
    )
    table_rows += (
        f"<tr style='background:{_BLUE4};'>"
        f"<td style='text-align:left;{tot_style}font-size:0.80rem;color:{_BLUE};'>TỔNG CỘNG</td>"
        f"{tot_month_cells}"
        f"<td style='text-align:right;{tot_style}font-size:0.80rem;color:{_BLUE};'>{col_tong / 1e9:.2f}</td>"
        f"<td style='text-align:right;{tot_style}color:{_BLUE};'>100%</td>"
        f"</tr>"
    )

    st.markdown(
        f'<div style="overflow-x:auto;">'
        f'<table style="width:100%;border-collapse:collapse;">'
        f'<thead><tr>'
        f'<th style="{th}text-align:left;">Nhóm đối tác</th>'
        f'{month_headers}'
        f'<th style="{th}text-align:right;">Lũy kế</th>'
        f'<th style="{th}text-align:right;">Tỷ trọng</th>'
        f'</tr></thead>'
        f'<tbody>{table_rows}</tbody>'
        f'</table></div>',
        unsafe_allow_html=True,
    )

    # ── Section 3: Chi tiết từng đối tác theo tháng ───────────────────────────
    section_head("Chi tiết từng đối tác theo tháng")

    months = sorted(df["thang_so"].unique())

    detail_agg = (
        df.groupby(["nhom_doi_tac", "doi_tac", "thang_so"], as_index=False)["tien_thuc_thu"].sum()
    )
    detail_lk = (
        df.groupby(["nhom_doi_tac", "doi_tac"], as_index=False)["tien_thuc_thu"]
        .sum()
        .rename(columns={"tien_thuc_thu": "lk"})
    )

    # Tổng lũy kế theo nhóm để sort nhóm desc; "ĐỐI TÁC KHÁC" luôn cuối
    nhom_total = detail_lk.groupby("nhom_doi_tac")["lk"].sum().rename("nhom_lk")
    detail_lk  = detail_lk.merge(nhom_total, on="nhom_doi_tac")
    detail_lk["_nhom_khac"] = detail_lk["nhom_doi_tac"].str.upper().str.contains("KHÁC|KHAC", na=False)
    detail_lk["_is_khac"]   = detail_lk["doi_tac"].str.lower().str.contains("khác|khac", na=False)
    detail_lk = detail_lk.sort_values(
        ["_nhom_khac", "nhom_lk", "_is_khac", "lk"], ascending=[True, False, True, False]
    ).drop(columns=["nhom_lk", "_nhom_khac", "_is_khac"])

    # Product breakdown
    _prod_df = df[df["product_group"].str.strip() != ""]
    prod_lk = (
        _prod_df.groupby(["doi_tac", "product_group"], as_index=False)["tien_thuc_thu"]
        .sum()
        .rename(columns={"tien_thuc_thu": "plk"})
        .sort_values(["doi_tac", "plk"], ascending=[True, False])
    )
    prod_agg = (
        _prod_df.groupby(["doi_tac", "product_group", "thang_so"], as_index=False)["tien_thuc_thu"].sum()
    )
    dt_with_products = set(prod_lk["doi_tac"].unique())

    th_s = (
        f"font-size:0.64rem;font-weight:700;text-transform:uppercase;"
        f"color:{_BLUE};letter-spacing:0.09em;padding:7px 10px;"
        f"border-bottom:2px solid {_BLUE};"
    )
    month_headers = "".join(
        f'<th style="{th_s}text-align:right;">T{m}</th>' for m in months
    )

    # CSS để <details> trong <td> không làm vỡ layout
    details_css = (
        "<style>"
        "details.dt-prod summary{cursor:pointer;list-style:none;display:flex;"
        "align-items:center;gap:5px;}"
        "details.dt-prod summary::-webkit-details-marker{display:none;}"
        "details.dt-prod summary::marker{display:none;}"
        "details.dt-prod .arr{font-size:0.68rem;color:#1558d6;transition:transform .15s;}"
        "details.dt-prod[open] .arr{transform:rotate(90deg);}"
        "details.dt-prod .prod-tbl{margin:4px 0 2px 0;border-collapse:collapse;width:100%;}"
        "details.dt-prod .prod-tbl td{padding:3px 6px;font-size:0.72rem;"
        f"color:{_MUTED};border-bottom:1px solid {_LINE};}}"
        "details.dt-prod .prod-tbl td:first-child{padding-left:2px;}"
        "details.dt-prod .prod-tbl td:not(:first-child){text-align:right;"
        "font-variant-numeric:tabular-nums;}"
        "</style>"
    )

    table_rows = ""
    current_nhom = None
    col_totals   = {m: 0.0 for m in months}
    col_total_lk = 0.0

    for row in detail_lk.itertuples(index=False):
        nhom = row.nhom_doi_tac
        dt   = row.doi_tac
        lk   = row.lk
        col_total_lk += lk

        if nhom != current_nhom:
            current_nhom = nhom
            nhom_lk_val = detail_lk[detail_lk["nhom_doi_tac"] == nhom]["lk"].sum()
            table_rows += (
                f"<tr style='background:#eef3ff;'>"
                f"<td colspan='{2 + len(months)}' style='text-align:left;font-weight:700;"
                f"font-size:0.78rem;color:{_BLUE};padding:7px 10px;"
                f"border-top:2px solid {_LINE};'>"
                f"{nhom} &nbsp;—&nbsp; "
                f"<span style='font-weight:400;'>{nhom_lk_val/1e9:.2f} tỷ</span>"
                f"</td></tr>"
            )

        month_cells = ""
        for m in months:
            m_val = detail_agg[
                (detail_agg["doi_tac"] == dt) & (detail_agg["thang_so"] == m)
            ]["tien_thuc_thu"].sum()
            col_totals[m] += m_val
            month_cells += (
                f"<td style='text-align:right;padding:6px 10px;"
                f"border-bottom:1px solid {_LINE};"
                f"font-variant-numeric:tabular-nums;font-size:0.76rem;'>"
                f"{'—' if m_val == 0 else f'{m_val/1e9:.2f}'}</td>"
            )

        if dt in dt_with_products:
            prods = prod_lk[prod_lk["doi_tac"] == dt]
            prod_month_headers = "".join(f"<td><b>T{m}</b></td>" for m in months)
            prod_rows = ""
            for _, pr in prods.iterrows():
                pg  = pr["product_group"]
                plk = pr["plk"]
                pcells = "".join(
                    f"<td>{'—' if pv == 0 else f'{pv/1e9:.2f}'}</td>"
                    for m in months
                    for pv in [prod_agg[
                        (prod_agg["doi_tac"] == dt) & (prod_agg["product_group"] == pg)
                        & (prod_agg["thang_so"] == m)
                    ]["tien_thuc_thu"].sum()]
                )
                prod_rows += (
                    f"<tr><td>{pg}</td>{pcells}"
                    f"<td><b>{plk/1e9:.2f}</b></td></tr>"
                )
            name_cell = (
                f"<td style='text-align:left;padding:6px 10px 6px 14px;"
                f"border-bottom:1px solid {_LINE};font-size:0.78rem;'>"
                f"<details class='dt-prod'>"
                f"<summary><span class='arr'>▶</span>{dt}</summary>"
                f"<table class='prod-tbl'>"
                f"<tr><td><b>Sản phẩm</b></td>{prod_month_headers}<td><b>Lũy kế</b></td></tr>"
                f"{prod_rows}"
                f"</table></details></td>"
            )
        else:
            name_cell = (
                f"<td style='text-align:left;padding:6px 10px 6px 18px;"
                f"border-bottom:1px solid {_LINE};font-size:0.78rem;'>{dt}</td>"
            )

        table_rows += (
            f"<tr>{name_cell}{month_cells}"
            f"<td style='text-align:right;padding:6px 10px;border-bottom:1px solid {_LINE};"
            f"font-weight:700;font-size:0.78rem;font-variant-numeric:tabular-nums;'>"
            f"{lk/1e9:.2f}</td></tr>"
        )

    tot_month_cells = "".join(
        f"<td style='text-align:right;padding:7px 10px;font-weight:800;"
        f"font-variant-numeric:tabular-nums;font-size:0.78rem;'>"
        f"{col_totals[m]/1e9:.2f}</td>"
        for m in months
    )
    tot_s = (
        f"font-weight:800;border-top:2px solid {_BLUE};border-bottom:none;"
        f"background:{_BLUE4};padding:7px 10px;font-variant-numeric:tabular-nums;"
    )
    table_rows += (
        f"<tr style='background:{_BLUE4};'>"
        f"<td style='text-align:left;{tot_s}font-size:0.78rem;color:{_BLUE};'>TỔNG CỘNG</td>"
        f"{tot_month_cells}"
        f"<td style='text-align:right;{tot_s}font-size:0.78rem;color:{_BLUE};'>"
        f"{col_total_lk/1e9:.2f}</td>"
        f"</tr>"
    )

    st.markdown(
        details_css +
        f'<div style="overflow-x:auto;">'
        f'<table style="width:100%;border-collapse:collapse;">'
        f'<thead><tr>'
        f'<th style="{th_s}text-align:left;min-width:200px;">Đối tác</th>'
        f'{month_headers}'
        f'<th style="{th_s}text-align:right;">Lũy kế</th>'
        f'</tr></thead>'
        f'<tbody>{table_rows}</tbody>'
        f'</table></div>',
        unsafe_allow_html=True,
    )

    # ── Section 4: Chi tiết theo ngày ─────────────────────────────────────────
    section_head("Chi tiết theo ngày")

    # Ngày mặc định = T-1 so với ngày có dữ liệu cuối cùng
    _last_date    = df["ngay_ban_hang"].dt.date.max()
    _default_date = _last_date - pd.Timedelta(days=1)
    # Nếu T-1 không có dữ liệu thì fallback về ngày cuối cùng
    _available_dates = set(df["ngay_ban_hang"].dt.date.unique())
    if _default_date not in _available_dates:
        _default_date = _last_date

    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1:
        nhom_options = ["(Tất cả)"] + sorted(df["nhom_doi_tac"].dropna().unique().tolist())
        sel_nhom = st.selectbox("Nhóm đối tác", nhom_options, key="day_nhom")
    with f_col2:
        if sel_nhom == "(Tất cả)":
            df_filtered_nhom = df
            dt_options = ["(Tất cả)"] + sorted(df["doi_tac"].dropna().unique().tolist())
        else:
            df_filtered_nhom = df[df["nhom_doi_tac"] == sel_nhom]
            dt_options = ["(Tất cả)"] + sorted(df_filtered_nhom["doi_tac"].dropna().unique().tolist())
        sel_dt = st.selectbox("Tên đối tác", dt_options, key="day_dt")
    with f_col3:
        sel_date = st.date_input(
            "Ngày",
            value=_default_date,
            min_value=df["ngay_ban_hang"].dt.date.min(),
            max_value=_last_date,
            key="day_date",
            format="DD/MM/YYYY",
        )

    # Áp filter
    if sel_dt != "(Tất cả)":
        day_df = df_filtered_nhom[df_filtered_nhom["doi_tac"] == sel_dt].copy()
    else:
        day_df = df_filtered_nhom.copy()
    day_df = day_df[day_df["ngay_ban_hang"].dt.date == sel_date]

    if day_df.empty:
        st.info(f"Không có dữ liệu ngày {sel_date.strftime('%d/%m/%Y')} cho lựa chọn này.")
    else:
        show_doi_tac_col = sel_dt == "(Tất cả)"
        group_cols = ["ngay_ban_hang", "doi_tac", "product_group"] if show_doi_tac_col \
                     else ["ngay_ban_hang", "product_group"]
        agg_day = (
            day_df.groupby(group_cols, as_index=False)
            .agg(so_don=("so_don_cap_moi", "sum"), doanh_thu=("tien_thuc_thu", "sum"))
            .sort_values(["ngay_ban_hang"] + (["doi_tac"] if show_doi_tac_col else []),
                         ascending=True)
        )
        agg_day["Ngày"] = agg_day["ngay_ban_hang"].dt.strftime("%d/%m/%Y")
        agg_day["Doanh thu (tỷ)"] = (agg_day["doanh_thu"] / 1e9).map(lambda v: f"{v:.4f}")
        agg_day["Số đơn"] = agg_day["so_don"].astype(int)

        rename = {"product_group": "Sản phẩm"}
        if show_doi_tac_col:
            rename["doi_tac"] = "Đối tác"
        display_cols = (
            ["Ngày", "Đối tác", "Sản phẩm", "Số đơn", "Doanh thu (tỷ)"]
            if show_doi_tac_col
            else ["Ngày", "Sản phẩm", "Số đơn", "Doanh thu (tỷ)"]
        )
        agg_day = agg_day.rename(columns=rename)[display_cols]

        _total_don = int(day_df["so_don_cap_moi"].sum())
        _total_rev = day_df["tien_thuc_thu"].sum()
        st.markdown(
            f'<div style="display:flex;gap:24px;margin-bottom:10px;'
            f'padding:10px 14px;background:#eef3ff;border-radius:6px;">'
            f'<span style="font-size:0.78rem;color:{_MUTED};">Tổng đơn: '
            f'<b style="color:{_INK};">{_total_don:,}</b></span>'
            f'<span style="font-size:0.78rem;color:{_MUTED};">Tổng doanh thu: '
            f'<b style="color:{_BLUE};">{_total_rev/1e9:.3f} tỷ</b></span>'
            f'<span style="font-size:0.78rem;color:{_MUTED};">{len(agg_day):,} dòng</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(agg_day, hide_index=True, width="stretch")

