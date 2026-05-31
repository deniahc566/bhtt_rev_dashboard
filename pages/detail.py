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
        .sort_values(["nhom_doi_tac", "lk"], ascending=[True, False])
    )

    th_s = (
        f"font-size:0.64rem;font-weight:700;text-transform:uppercase;"
        f"color:{_BLUE};letter-spacing:0.09em;padding:7px 10px;"
        f"border-bottom:2px solid {_BLUE};"
    )
    month_headers = "".join(
        f'<th style="{th_s}text-align:right;">T{m}</th>' for m in months
    )

    table_rows = ""
    current_nhom = None
    col_totals   = {m: 0.0 for m in months}
    col_total_lk = 0.0

    for _, row in detail_lk.iterrows():
        nhom = row["nhom_doi_tac"]
        dt   = row["doi_tac"]
        lk   = row["lk"]
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

        table_rows += (
            f"<tr>"
            f"<td style='text-align:left;padding:6px 10px 6px 18px;"
            f"border-bottom:1px solid {_LINE};font-size:0.78rem;'>{dt}</td>"
            f"{month_cells}"
            f"<td style='text-align:right;padding:6px 10px;border-bottom:1px solid {_LINE};"
            f"font-weight:700;font-size:0.78rem;font-variant-numeric:tabular-nums;'>"
            f"{lk/1e9:.2f}</td>"
            f"</tr>"
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

