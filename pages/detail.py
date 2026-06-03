import sys
import json as _json
from pathlib import Path
_HERE = Path(__file__).parent.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

import pandas as pd
import altair as alt
import streamlit as st
import streamlit.components.v1 as _cmp

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
            month_cells += (
                f"<td style='text-align:right;padding:8px 10px;"
                f"border-bottom:1px solid {_LINE};"
                f"font-variant-numeric:tabular-nums;font-size:0.78rem;'>"
                f"{'—' if m_val == 0 else fmt_currency(m_val)}</td>"
            )

        table_rows += (
            f"<tr>"
            f"<td style='text-align:left;font-weight:600;padding:8px 10px;"
            f"border-bottom:1px solid {_LINE};font-size:0.80rem;'>{name}</td>"
            f"{month_cells}"
            f"<td style='text-align:right;padding:8px 10px;border-bottom:1px solid {_LINE};"
            f"font-weight:700;font-size:0.80rem;font-variant-numeric:tabular-nums;'>"
            f"{fmt_currency(lk)}</td>"
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
        f"{fmt_currency(col_months_sum[m])}</td>"
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
        f"<td style='text-align:right;{tot_style}font-size:0.80rem;color:{_BLUE};'>{fmt_currency(col_tong)}</td>"
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
        f"border-bottom:2px solid {_BLUE};white-space:nowrap;"
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
                f"<span style='font-weight:400;'>{fmt_currency(nhom_lk_val)}</span>"
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
                f"font-variant-numeric:tabular-nums;font-size:0.76rem;white-space:nowrap;'>"
                f"{'—' if m_val == 0 else fmt_currency(m_val)}</td>"
            )

        if dt in dt_with_products:
            prods = prod_lk[prod_lk["doi_tac"] == dt]
            prod_month_headers = "".join(f"<td><b>T{m}</b></td>" for m in months)
            prod_rows = ""
            for _, pr in prods.iterrows():
                pg  = pr["product_group"]
                plk = pr["plk"]
                pcells = "".join(
                    f"<td>{'—' if pv == 0 else fmt_currency(pv)}</td>"
                    for m in months
                    for pv in [prod_agg[
                        (prod_agg["doi_tac"] == dt) & (prod_agg["product_group"] == pg)
                        & (prod_agg["thang_so"] == m)
                    ]["tien_thuc_thu"].sum()]
                )
                prod_rows += (
                    f"<tr><td>{pg}</td>{pcells}"
                    f"<td><b>{fmt_currency(plk)}</b></td></tr>"
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
            f"font-weight:700;font-size:0.78rem;font-variant-numeric:tabular-nums;white-space:nowrap;'>"
            f"{fmt_currency(lk)}</td></tr>"
        )

    tot_month_cells = "".join(
        f"<td style='text-align:right;padding:7px 10px;font-weight:800;"
        f"font-variant-numeric:tabular-nums;font-size:0.78rem;white-space:nowrap;'>"
        f"{fmt_currency(col_totals[m])}</td>"
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
        f"{fmt_currency(col_total_lk)}</td>"
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

def render_daily_page() -> None:
    try:
        full_df = load_partner_data()
    except Exception as e:
        st.error(f"Không thể tải dữ liệu: {e}")
        return

    if full_df.empty:
        st.warning("Chưa có dữ liệu.")
        return

    current_year = int(full_df["nam"].max())
    df = full_df[full_df["nam"] == current_year].copy()

    # ── Chi tiết theo ngày ─────────────────────────────────────────────────────

    # Pre-aggregate by (date, nhom_doi_tac, doi_tac, product_group)
    _day_src = df.copy()
    _day_src["date"] = df["ngay_ban_hang"].dt.strftime("%Y-%m-%d")
    _day_agg = (
        _day_src.groupby(["date", "nhom_doi_tac", "doi_tac", "product_group"], as_index=False)
        .agg(rev=("tien_thuc_thu", "sum"), don=("so_don_cap_moi", "sum"))
        .sort_values("date")
    )

    _months_in_data = sorted(_day_agg["date"].str[:7].unique().tolist())
    _last_date_s = _day_agg["date"].max()
    _min_date_s  = _day_agg["date"].min()

    _nhom_list = sorted(_day_agg["nhom_doi_tac"].dropna().unique().tolist())
    _nhom_to_dt: dict = {}
    for _nhom in _nhom_list:
        _nhom_to_dt[_nhom] = sorted(
            _day_agg[_day_agg["nhom_doi_tac"] == _nhom]["doi_tac"].dropna().unique().tolist()
        )
    _prod_list = sorted(_day_agg["product_group"].dropna().unique().tolist())

    _rows_json       = _json.dumps(_day_agg.to_dict(orient="records"), ensure_ascii=False)
    _nhom_list_json  = _json.dumps(_nhom_list, ensure_ascii=False)
    _nhom_to_dt_json = _json.dumps(_nhom_to_dt, ensure_ascii=False)
    _months_json     = _json.dumps(_months_in_data, ensure_ascii=False)
    _prod_list_json  = _json.dumps(_prod_list, ensure_ascii=False)

    _HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:13px;color:#0d1a2e;background:#fff;padding:0 4px;}

.filter-bar{display:flex;flex-wrap:wrap;gap:8px;align-items:flex-end;padding:14px 16px;background:#f8fafd;border:1.5px solid #d0d8e4;margin-bottom:14px;}
.filter-group{display:flex;flex-direction:column;gap:4px;}
.filter-group label{font-size:10px;font-weight:700;letter-spacing:0.09em;text-transform:uppercase;color:#64748b;}
.filter-group input[type=date]{height:32px;border:1.5px solid #d0d8e4;padding:0 8px;font-size:12px;color:#0d1a2e;outline:none;min-width:120px;}
.filter-group input[type=date]:focus{border-color:#1558d6;}
.filter-group select{height:32px;border:1.5px solid #d0d8e4;padding:0 8px;font-size:12px;color:#0d1a2e;outline:none;background:#fff;min-width:140px;}
.filter-group select:focus{border-color:#1558d6;}

.pills{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px;}
.pill{display:inline-flex;align-items:center;gap:6px;padding:5px 14px;font-size:12px;background:#eef3ff;border:1px solid #c5d8fb;}
.pill .plabel{color:#64748b;font-weight:600;}
.pill .pval{color:#1558d6;font-weight:700;}

.charts-row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:16px;}
.chart-card{background:#fff;border:1.5px solid #d0d8e4;padding:14px 16px;}
.chart-card h4{font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#0d1a2e;margin-bottom:10px;}

.tbl-wrap{border:1.5px solid #d0d8e4;}
.tbl-wrap table{width:100%;border-collapse:collapse;}
.tbl-wrap thead th{background:#f1f5fb;font-size:10px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#64748b;padding:8px 12px;border-bottom:1.5px solid #d0d8e4;white-space:nowrap;}
.tbl-wrap thead th.sticky{position:sticky;top:0;z-index:1;background:#f1f5fb;}
.tbl-wrap tbody tr:hover{background:#f8fafd;}
.tbl-wrap tbody td{padding:7px 12px;border-bottom:1px solid #e8edf5;font-size:12px;vertical-align:middle;white-space:nowrap;}
.tbl-wrap tbody tr:last-child td{border-bottom:none;}
.tbl-scroll{max-height:600px;overflow-y:auto;}
td.num{text-align:right;font-variant-numeric:tabular-nums;}
.pill-up{display:inline-block;background:#dcfce7;color:#16a34a;font-weight:700;font-size:10px;padding:2px 7px;}
.pill-dn{display:inline-block;background:#fee2e2;color:#dc2626;font-weight:700;font-size:10px;padding:2px 7px;}
.pill-eq{display:inline-block;background:#f1f5f9;color:#64748b;font-weight:700;font-size:10px;padding:2px 7px;}
</style>
</head>
<body>
<div id="app"></div>
<script>
const ALL_ROWS   = __ROWS_JSON__;
const NHOM_LIST  = __NHOM_LIST_JSON__;
const NHOM_TO_DT = __NHOM_TO_DT_JSON__;
const ALL_MONTHS = __MONTHS_JSON__;
const PROD_LIST  = __PROD_LIST_JSON__;
const LAST_DATE  = "__LAST_DATE__";
const MIN_DATE   = "__MIN_DATE__";

let state = {
  dateFrom: LAST_DATE,
  dateTo:   LAST_DATE,
  nhom: "", dt: "", prod: "",
};

function fmtRev(v) {
  if (v === 0) return "0 đ";
  const a = Math.abs(v);
  if (a >= 1e9) return (v/1e9).toLocaleString("vi-VN",{minimumFractionDigits:2,maximumFractionDigits:2})+" tỷ";
  if (a >= 1e6) return (v/1e6).toLocaleString("vi-VN",{minimumFractionDigits:1,maximumFractionDigits:1})+" triệu";
  if (a >= 1e3) return (v/1e3).toLocaleString("vi-VN",{minimumFractionDigits:0,maximumFractionDigits:0})+" nghìn";
  return v.toLocaleString("vi-VN")+" đ";
}
function fmtRevM(v) {
  if (v===0) return "0";
  const a=Math.abs(v);
  if (a>=1e9) return (v/1e9).toFixed(2)+" tỷ";
  if (a>=1e6) return (v/1e6).toFixed(1)+" tr";
  if (a>=1e3) return (v/1e3).toFixed(0)+" k";
  return v.toString();
}
function fmtDate(s){if(!s)return"";const[y,m,d]=s.split("-");return d+"/"+m;}
function fmtDateFull(s){if(!s)return"";const[y,m,d]=s.split("-");return d+"/"+m+"/"+y;}
function pctStr(a,b){if(b===0)return null;return((a-b)/Math.abs(b)*100).toFixed(1);}

function filteredRows() {
  return ALL_ROWS.filter(r => {
    if (r.date < state.dateFrom || r.date > state.dateTo) return false;
    if (state.nhom && r.nhom_doi_tac  !== state.nhom) return false;
    if (state.dt   && r.doi_tac       !== state.dt)   return false;
    if (state.prod && r.product_group !== state.prod) return false;
    return true;
  });
}

function byDate(rows) {
  const map = {};
  rows.forEach(r => {
    if (!map[r.date]) map[r.date]={date:r.date,rev:0,don:0};
    map[r.date].rev+=r.rev; map[r.date].don+=r.don;
  });
  return Object.values(map).sort((a,b)=>a.date.localeCompare(b.date));
}

let chartRev=null, chartDon=null;
function drawCharts(daily) {
  const labels=daily.map(d=>fmtDate(d.date));
  const revs=daily.map(d=>d.rev), dons=daily.map(d=>d.don);
  const avgRev=revs.length?revs.reduce((a,b)=>a+b,0)/revs.length:0;
  const avgDon=dons.length?dons.reduce((a,b)=>a+b,0)/dons.length:0;

  if(chartRev)chartRev.destroy();
  chartRev=new Chart(document.getElementById("chartRev").getContext("2d"),{
    data:{labels,datasets:[
      {type:"bar",label:"Doanh thu",data:revs,backgroundColor:"rgba(21,88,214,0.65)",borderRadius:3},
      {type:"line",label:"TB/ngày",data:revs.map(()=>avgRev),borderColor:"#dc2626",borderWidth:1.5,borderDash:[4,3],pointRadius:0,tension:0}
    ]},
    options:{responsive:true,maintainAspectRatio:false,animation:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>ctx.dataset.label+": "+fmtRev(ctx.parsed.y)}}},
      scales:{x:{grid:{display:false},ticks:{font:{size:10},maxRotation:45,minRotation:0}},
              y:{ticks:{font:{size:10},callback:v=>fmtRevM(v)},grid:{color:"#e8edf5"}}}
    }
  });

  if(chartDon)chartDon.destroy();
  chartDon=new Chart(document.getElementById("chartDon").getContext("2d"),{
    data:{labels,datasets:[
      {type:"bar",label:"Số đơn",data:dons,backgroundColor:"rgba(14,165,233,0.65)",borderRadius:3},
      {type:"line",label:"TB/ngày",data:dons.map(()=>avgDon),borderColor:"#dc2626",borderWidth:1.5,borderDash:[4,3],pointRadius:0,tension:0}
    ]},
    options:{responsive:true,maintainAspectRatio:false,animation:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>ctx.dataset.label+": "+ctx.parsed.y.toLocaleString("vi-VN")}}},
      scales:{x:{grid:{display:false},ticks:{font:{size:10},maxRotation:45,minRotation:0}},
              y:{ticks:{font:{size:10}},grid:{color:"#e8edf5"}}}
    }
  });
}

function render() {
  const rows=filteredRows(), daily=byDate(rows);
  const totRev=rows.reduce((s,r)=>s+r.rev,0);
  const totDon=rows.reduce((s,r)=>s+r.don,0);
  const nDays=daily.length, avgDay=nDays?totRev/nDays:0;

  document.getElementById("pills").innerHTML=
    '<div class="pill"><span class="plabel">Tổng DT</span><span class="pval">'+fmtRev(totRev)+'</span></div>'+
    '<div class="pill"><span class="plabel">Tổng đơn</span><span class="pval" style="color:#16a34a">'+totDon.toLocaleString("vi-VN")+'</span></div>'+
    '<div class="pill"><span class="plabel">TB/ngày</span><span class="pval">'+fmtRev(avgDay)+'</span></div>'+
    '<div class="pill"><span class="plabel">'+nDays+' ngày</span></div>';

  drawCharts(daily);

  const dailyDesc=[...daily].reverse();
  const byDateMap={};
  daily.forEach((d,i)=>{byDateMap[d.date]={rev:d.rev,don:d.don,prev:i>0?daily[i-1].rev:null};});

  let tbRows="";
  dailyDesc.forEach(d=>{
    const prev=byDateMap[d.date].prev;
    let cmpHtml='<span class="pill-eq">—</span>';
    if(prev!==null){
      const pct=pctStr(d.rev,prev);
      if(pct!==null){
        if(parseFloat(pct)>0)      cmpHtml='<span class="pill-up">▲ +'+pct+'%</span>';
        else if(parseFloat(pct)<0) cmpHtml='<span class="pill-dn">▼ '+pct+'%</span>';
        else                       cmpHtml='<span class="pill-eq">= 0%</span>';
      }
    }
    const rpd=d.don>0?fmtRev(d.rev/d.don):"—";
    tbRows+='<tr><td>'+fmtDateFull(d.date)+'</td><td class="num">'+fmtRev(d.rev)+'</td>'+
            '<td class="num">'+d.don.toLocaleString("vi-VN")+'</td><td class="num">'+rpd+'</td>'+
            '<td style="text-align:center;">'+cmpHtml+'</td></tr>';
  });
  document.getElementById("tbl-body").innerHTML=tbRows||'<tr><td colspan="5" style="text-align:center;color:#64748b;padding:16px;">Không có dữ liệu</td></tr>';
}

function buildDtOptions(nhom) {
  const sel=document.getElementById("selDt");
  const opts=nhom?(NHOM_TO_DT[nhom]||[]):[...new Set(ALL_ROWS.map(r=>r.doi_tac))].sort();
  sel.innerHTML='<option value="">(Tất cả đối tác)</option>'+
    opts.map(d=>'<option value="'+d+'"'+(state.dt===d?' selected':'')+'>'+d+'</option>').join("");
}

function buildProdOptions(nhom, dt) {
  const sel=document.getElementById("selProd");
  if(!sel) return;
  const prods=[...new Set(
    ALL_ROWS
      .filter(r=>(!nhom||r.nhom_doi_tac===nhom)&&(!dt||r.doi_tac===dt))
      .map(r=>r.product_group)
      .filter(Boolean)
  )].sort();
  const prev=state.prod;
  sel.innerHTML='<option value="">(Tất cả sản phẩm)</option>'+
    prods.map(p=>'<option value="'+p+'"'+(prev===p?' selected':'')+'>'+p+'</option>').join("");
  if(!prods.includes(prev)) state.prod="";
}

function syncMonthSelect() {
  const sel=document.getElementById("selMonth");
  if(!sel)return;
  // find which month matches current dateFrom if exact month range
  let matched="";
  ALL_MONTHS.forEach(m=>{
    const [y,mo]=m.split("-");
    const lastDay=new Date(parseInt(y),parseInt(mo),0).getDate();
    if(state.dateFrom===m+"-01"&&state.dateTo===m+"-"+String(lastDay).padStart(2,"0")) matched=m;
  });
  sel.value=matched;
}

function applyMonth(m) {
  if(!m){
    state.dateFrom=MIN_DATE; state.dateTo=LAST_DATE;
  } else {
    const [y,mo]=m.split("-");
    const lastDay=new Date(parseInt(y),parseInt(mo),0).getDate();
    state.dateFrom=m+"-01";
    state.dateTo=m+"-"+String(lastDay).padStart(2,"0");
  }
  document.getElementById("inpFrom").value=state.dateFrom;
  document.getElementById("inpTo").value=state.dateTo;
}

function init() {
  state.dateFrom=LAST_DATE; state.dateTo=LAST_DATE;
  const app=document.getElementById("app");
  const monthOpts='<option value="">(Tất cả tháng)</option>'+
    ALL_MONTHS.map(m=>{const[y,mo]=m.split("-");return'<option value="'+m+'">T'+parseInt(mo)+'/'+y+'</option>';}).join("");
  const nhomOpts='<option value="">(Tất cả nhóm)</option>'+
    NHOM_LIST.map(n=>'<option value="'+n+'">'+n+'</option>').join("");

  app.innerHTML=`
    <div class="filter-bar">
      <div class="filter-group">
        <label>Từ ngày</label>
        <input type="date" id="inpFrom" value="${state.dateFrom}" min="${MIN_DATE}" max="${LAST_DATE}">
      </div>
      <div class="filter-group">
        <label>Đến ngày</label>
        <input type="date" id="inpTo" value="${state.dateTo}" min="${MIN_DATE}" max="${LAST_DATE}">
      </div>
      <div class="filter-group">
        <label>Tháng nhanh</label>
        <select id="selMonth">${monthOpts}</select>
      </div>
      <div class="filter-group">
        <label>Nhóm sản phẩm</label>
        <select id="selProd"><option value="">(Tất cả sản phẩm)</option></select>
      </div>
      <div class="filter-group">
        <label>Nhóm đối tác</label>
        <select id="selNhom">${nhomOpts}</select>
      </div>
      <div class="filter-group">
        <label>Tên đối tác</label>
        <select id="selDt"><option value="">(Tất cả đối tác)</option></select>
      </div>
    </div>
    <div class="pills" id="pills"></div>
    <div class="charts-row">
      <div class="chart-card">
        <h4>Doanh thu theo ngày</h4>
        <div style="height:180px;"><canvas id="chartRev"></canvas></div>
      </div>
      <div class="chart-card">
        <h4>Số đơn theo ngày</h4>
        <div style="height:180px;"><canvas id="chartDon"></canvas></div>
      </div>
    </div>
    <div class="tbl-wrap">
      <div class="tbl-scroll">
        <table>
          <thead><tr>
            <th class="sticky">Ngày</th>
            <th class="sticky" style="text-align:right;">DT</th>
            <th class="sticky" style="text-align:right;">Số đơn</th>
            <th class="sticky" style="text-align:right;">DT/đơn</th>
            <th class="sticky" style="text-align:center;">So hôm trước</th>
          </tr></thead>
          <tbody id="tbl-body"></tbody>
        </table>
      </div>
    </div>
  `;

  // find current month in data and pre-select it
  const curMonth=ALL_MONTHS.length?ALL_MONTHS[ALL_MONTHS.length-1]:"";
  if(curMonth){
    document.getElementById("selMonth").value=curMonth;
    applyMonth(curMonth);
    document.getElementById("inpFrom").value=state.dateFrom;
    document.getElementById("inpTo").value=state.dateTo;
  }

  buildDtOptions("");
  buildProdOptions("", "");

  document.getElementById("inpFrom").addEventListener("change",e=>{
    state.dateFrom=e.target.value; syncMonthSelect(); render();
  });
  document.getElementById("inpTo").addEventListener("change",e=>{
    state.dateTo=e.target.value; syncMonthSelect(); render();
  });
  document.getElementById("selMonth").addEventListener("change",e=>{
    applyMonth(e.target.value); render();
  });
  document.getElementById("selProd").addEventListener("change",e=>{
    state.prod=e.target.value; render();
  });
  document.getElementById("selNhom").addEventListener("change",e=>{
    state.nhom=e.target.value; state.dt=""; state.prod="";
    buildDtOptions(state.nhom); buildProdOptions(state.nhom, ""); render();
  });
  document.getElementById("selDt").addEventListener("change",e=>{
    state.dt=e.target.value; state.prod="";
    buildProdOptions(state.nhom, state.dt); render();
  });

  render();
}
init();
</script>
</body>
</html>"""

    _html = (
        _HTML_TEMPLATE
        .replace("__ROWS_JSON__",       _rows_json)
        .replace("__NHOM_LIST_JSON__",  _nhom_list_json)
        .replace("__NHOM_TO_DT_JSON__", _nhom_to_dt_json)
        .replace("__MONTHS_JSON__",     _months_json)
        .replace("__PROD_LIST_JSON__",  _prod_list_json)
        .replace("__LAST_DATE__",       _last_date_s)
        .replace("__MIN_DATE__",        _min_date_s)
    )
    _cmp.html(_html, height=1080, scrolling=False)

