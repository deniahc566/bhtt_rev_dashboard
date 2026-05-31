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

from data_loader import load_partner_data, load_bhs_data, load_telesale_data, load_gateway_data
from ui_helpers import (
    kpi_card,
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


def render_overview_page() -> None:
    try:
        full_df = load_partner_data()
    except Exception as e:
        st.error(f"Không thể tải dữ liệu đối tác: {e}")
        return

    if full_df.empty:
        st.warning("Chưa có dữ liệu. Hãy chạy extract_partner_data.py và build_partner_rev.py trước.")
        return

    bhs_df      = load_bhs_data()
    telesale_df = load_telesale_data()
    gateway_df  = load_gateway_data()

    # ── Xác định năm / tháng hiện tại ─────────────────────────────────────────
    current_year = int(full_df["nam"].max())
    prev_year    = current_year - 1
    df_cy = full_df[full_df["nam"] == current_year].copy()
    df_py = full_df[full_df["nam"] == prev_year].copy()

    tong_cy = df_cy["tien_thuc_thu"].sum()
    tong_py = df_py["tien_thuc_thu"].sum()
    yoy_pct = (tong_cy - tong_py) / abs(tong_py) * 100 if tong_py else 0
    yoy_arrow = "▲" if yoy_pct >= 0 else "▼"
    yoy_color = _POS if yoy_pct >= 0 else _NEG

    sorted_months = sorted(df_cy["ngay_ban_hang"].dt.to_period("M").unique())
    last_month    = sorted_months[-1] if sorted_months else None
    df_last = df_cy[df_cy["ngay_ban_hang"].dt.to_period("M") == last_month] if last_month else pd.DataFrame()
    tong_last = df_last["tien_thuc_thu"].sum()

    if last_month:
        _prev_month_py = last_month.asfreq("M") - 12
        df_last_py = df_py[df_py["ngay_ban_hang"].dt.to_period("M") == _prev_month_py]
        tong_last_py = df_last_py["tien_thuc_thu"].sum()
    else:
        tong_last_py = 0
    last_yoy = (tong_last - tong_last_py) / abs(tong_last_py) * 100 if tong_last_py else 0
    last_yoy_arrow = "▲" if last_yoy >= 0 else "▼"
    last_yoy_color = _POS if last_yoy >= 0 else _NEG
    last_label = f"T{last_month.month}.{last_month.year}" if last_month else "—"
    last_py_label = f"T{last_month.month}.{prev_year}" if last_month else "—"

    # ── Tính BHS từ DB ─────────────────────────────────────────────────────────
    bhs_cy = bhs_df[bhs_df["nam"] == current_year] if not bhs_df.empty else pd.DataFrame()
    bhs_py = bhs_df[bhs_df["nam"] == prev_year]    if not bhs_df.empty else pd.DataFrame()
    _bhs_total_cy = bhs_cy["doanh_thu"].sum() if not bhs_cy.empty else 0
    _bhs_total_py = bhs_py["doanh_thu"].sum() if not bhs_py.empty else 0
    _bhs_yoy_pct  = (_bhs_total_cy - _bhs_total_py) / abs(_bhs_total_py) * 100 if _bhs_total_py else 0
    _bhs_yoy_arrow = "▲" if _bhs_yoy_pct >= 0 else "▼"
    _bhs_yoy_color = _POS if _bhs_yoy_pct >= 0 else _NEG

    # ── KPI strip ─────────────────────────────────────────────────────────────
    _total_cy = tong_cy + _bhs_total_cy
    _total_py = tong_py + _bhs_total_py
    _total_yoy_pct   = (_total_cy - _total_py) / abs(_total_py) * 100 if _total_py else 0
    _total_yoy_arrow = "▲" if _total_yoy_pct >= 0 else "▼"
    _total_yoy_color = _POS if _total_yoy_pct >= 0 else _NEG
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_card(
            label=f"DT lũy kế {current_year}",
            value=f"{_total_cy / 1e9:,.2f} <span style='font-size:0.9rem;color:{_MUTED};font-weight:600;'>tỷ</span>",
            delta_str=f"{_total_yoy_arrow} {_total_yoy_pct:+.1f}% YoY",
            delta_color=_total_yoy_color,
            accent_color=_BLUE,
            subtitle=f"Cùng kỳ {prev_year}: {_total_py / 1e9:,.2f} tỷ",
        ), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card(
            label=f"DT thực hiện {last_label}",
            value=f"{tong_last / 1e9:,.2f} <span style='font-size:0.9rem;color:{_MUTED};font-weight:600;'>tỷ</span>",
            delta_str=f"{last_yoy_arrow} {last_yoy:+.1f}% vs {last_py_label}",
            delta_color=last_yoy_color,
            accent_color=_BLUE2,
            subtitle=f"{last_py_label}: {tong_last_py / 1e9:,.2f} tỷ",
        ), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card(
            label="Phòng Phát triển đối tác",
            value=f"{tong_cy / 1e9:,.2f} <span style='font-size:0.9rem;color:{_MUTED};font-weight:600;'>tỷ</span>",
            delta_str=f"{yoy_arrow} {yoy_pct:+.1f}% YoY",
            delta_color=yoy_color,
            accent_color=_BLUE3,
            subtitle=f"{tong_cy / _total_cy * 100:.1f}% tổng doanh thu lũy kế" if _total_cy else "—",
        ), unsafe_allow_html=True)
    with c4:
        if _bhs_total_cy > 0:
            st.markdown(kpi_card(
                label="Phòng Bảo hiểm số",
                value=f"{_bhs_total_cy / 1e9:,.2f} <span style='font-size:0.9rem;color:{_MUTED};font-weight:600;'>tỷ</span>",
                delta_str=f"{_bhs_yoy_arrow} {_bhs_yoy_pct:+.1f}% YoY",
                delta_color=_bhs_yoy_color,
                accent_color=_BLUE4,
                subtitle=f"{_bhs_total_cy / _total_cy * 100:.1f}% tổng doanh thu lũy kế" if _total_cy else "—",
            ), unsafe_allow_html=True)
        else:
            st.markdown(kpi_card(
                label="Phòng Bảo hiểm số",
                value="—",
                delta_str="Chưa có dữ liệu",
                delta_color=_MUTED,
                accent_color=_BLUE4,
                subtitle="Chạy extract_manual_data.py để nạp",
            ), unsafe_allow_html=True)

    # ── Section 1: Cơ cấu doanh thu ──────────────────────────────────────────
    section_head(f"Cơ cấu doanh thu lũy kế {current_year}")

    col_bar, col_donut = st.columns([1.4, 1])

    with col_bar:
        _chart_title("Top đối tác — Phòng Phát triển đối tác")
        _chart_sub(f"Doanh thu lũy kế T1–{last_label} (tỷ đồng)")
        rev_nhom = (
            df_cy.groupby("nhom_doi_tac", as_index=False)["tien_thuc_thu"]
            .sum()
            .sort_values("tien_thuc_thu", ascending=False)
        )
        rev_nhom["label_b"] = (rev_nhom["tien_thuc_thu"] / 1e9).apply(lambda v: f"{v:.2f} tỷ")
        n = len(rev_nhom)
        colors = [_BLUE if i == 0 else (_BLUE2 if i < 3 else _BLUE3) for i in range(n)]
        rev_nhom["_color"] = colors
        nhom_order = rev_nhom["nhom_doi_tac"].tolist()

        base = alt.Chart(rev_nhom).encode(
            y=alt.Y("nhom_doi_tac:N", title=None, sort=nhom_order,
                    axis=alt.Axis(labelFontSize=11, labelColor=_INK)),
            x=alt.X("tien_thuc_thu:Q", title="Doanh thu (VND)",
                    scale=alt.Scale(domainMax=int(rev_nhom["tien_thuc_thu"].max() * 1.35)),
                    axis=alt.Axis(format="~s", labelFontSize=10, labelColor=_MUTED)),
            color=alt.Color("_color:N", scale=None, legend=None),
            tooltip=[
                alt.Tooltip("nhom_doi_tac:N", title="Nhóm"),
                alt.Tooltip("tien_thuc_thu:Q", title="Doanh thu", format=",.0f"),
            ],
        )
        bars = base.mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3)
        text = base.mark_text(align="left", dx=4, fontSize=10, color=_INK, clip=False).encode(
            text="label_b:N"
        )
        st.altair_chart(
            (bars + text).properties(height=max(220, n * 34)).configure_view(strokeWidth=0),
            width='stretch',
        )

    with col_donut:
        _chart_title("Đóng góp theo khối")
        _chart_sub("Tỷ trọng doanh thu lũy kế")
        donut_rows = [{"Phòng": "Phòng Phát triển đối tác", "Doanh thu": tong_cy, "_color": _BLUE}]
        if _bhs_total_cy > 0:
            donut_rows.append({"Phòng": "Phòng Bảo hiểm số", "Doanh thu": _bhs_total_cy, "_color": _BLUE3})
        donut_df = pd.DataFrame(donut_rows)
        donut = (
            alt.Chart(donut_df)
            .mark_arc(innerRadius=70, outerRadius=120, cornerRadius=2)
            .encode(
                theta=alt.Theta("Doanh thu:Q"),
                color=alt.Color("_color:N", scale=None, legend=None),
                tooltip=[
                    alt.Tooltip("Phòng:N", title="Phòng"),
                    alt.Tooltip("Doanh thu:Q", title="Doanh thu", format=",.0f"),
                ],
            )
        )
        legend_html = "".join(
            f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">'
            f'<span style="width:12px;height:12px;border-radius:2px;background:{r["_color"]};flex-shrink:0;"></span>'
            f'<span style="font-size:0.72rem;color:{_INK};">{r["Phòng"]} — <b>{r["Doanh thu"]/1e9:.2f} tỷ</b></span>'
            f'</div>'
            for r in donut_rows
        )
        st.altair_chart(
            donut.properties(height=260).configure_view(strokeWidth=0),
            width='stretch',
        )
        st.markdown(
            f'<div style="margin-top:-8px;padding:0 8px;">{legend_html}</div>',
            unsafe_allow_html=True,
        )

    # ── Section 2: Phòng Bảo hiểm số ─────────────────────────────────────────
    section_head("Phòng Bảo hiểm số — phân rã theo kênh")

    if bhs_cy.empty:
        st.warning("Chưa có dữ liệu BHS — chạy extract_manual_data.py và upload file Excel.")
    else:
        col_ch_bar, col_ch_tbl = st.columns(2)

        # Pivot: kenh x nam → doanh_thu
        bhs_pivot = (
            bhs_df[bhs_df["nam"].isin([current_year, prev_year])]
            .groupby(["kenh", "nam"], as_index=False)["doanh_thu"].sum()
        )
        bhs_pivot["rev_b"] = bhs_pivot["doanh_thu"] / 1e9
        bhs_pivot["Năm"] = bhs_pivot["nam"].apply(
            lambda y: f"Lũy kế {y}"
        )

        with col_ch_bar:
            _chart_title("Doanh thu theo kênh — lũy kế")
            _chart_sub(f"Lũy kế {current_year} vs {prev_year} (tỷ đồng)")
            ch_chart = (
                alt.Chart(bhs_pivot)
                .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
                .encode(
                    x=alt.X("kenh:N", title=None,
                            axis=alt.Axis(labelFontSize=11, labelColor=_INK)),
                    y=alt.Y("rev_b:Q", title="Tỷ đồng",
                            axis=alt.Axis(labelFontSize=10, labelColor=_MUTED)),
                    color=alt.Color(
                        "Năm:N",
                        scale=alt.Scale(
                            domain=[f"Lũy kế {current_year}", f"Lũy kế {prev_year}"],
                            range=[_BLUE, _BLUE4],
                        ),
                        legend=alt.Legend(orient="bottom", labelFontSize=11, symbolSize=80),
                    ),
                    xOffset="Năm:N",
                    tooltip=[
                        alt.Tooltip("kenh:N", title="Kênh"),
                        alt.Tooltip("Năm:N"),
                        alt.Tooltip("rev_b:Q", title="Tỷ đồng", format=".3f"),
                    ],
                )
                .properties(height=240)
            )
            st.altair_chart(ch_chart.configure_view(strokeWidth=0), width='stretch')

        with col_ch_tbl:
            _chart_title("Bảng chi tiết kênh")
            _chart_sub(f"Lũy kế {current_year} · {prev_year} · tăng trưởng")
            pill_css = (
                "display:inline-block;padding:2px 7px;border-radius:10px;"
                "font-size:0.72rem;font-weight:700;"
            )
            # Build per-channel summary
            kenh_cy = bhs_cy.groupby("kenh")["doanh_thu"].sum()
            kenh_py = bhs_py.groupby("kenh")["doanh_thu"].sum() if not bhs_py.empty else pd.Series(dtype=float)
            all_kenh = sorted(set(kenh_cy.index) | set(kenh_py.index))

            rows_html = ""
            th = (
                f"font-size:0.65rem;font-weight:700;text-transform:uppercase;"
                f"color:{_MUTED};letter-spacing:0.07em;padding:8px 10px;"
                f"border-bottom:2px solid {_INK};"
            )
            for kenh in all_kenh:
                v_cy = kenh_cy.get(kenh, 0)
                v_py = kenh_py.get(kenh, 0)
                if v_py:
                    pct = (v_cy - v_py) / abs(v_py) * 100
                    growth = f"{pct:+.1f}%"
                    d = "up" if pct >= 0 else "down"
                else:
                    growth, d = "N/A", "up"
                pill_style = (
                    f"background:#dcfce7;color:{_POS};" if d == "up"
                    else f"background:#fee2e2;color:{_NEG};"
                )
                rows_html += (
                    f"<tr>"
                    f"<td style='text-align:left;font-weight:600;padding:8px 10px;"
                    f"border-bottom:1px solid {_LINE};'>{kenh}</td>"
                    f"<td style='text-align:right;padding:8px 10px;border-bottom:1px solid {_LINE};"
                    f"font-variant-numeric:tabular-nums;'>{v_cy/1e9:.3f}</td>"
                    f"<td style='text-align:right;padding:8px 10px;border-bottom:1px solid {_LINE};"
                    f"font-variant-numeric:tabular-nums;'>{v_py/1e9:.3f}</td>"
                    f"<td style='text-align:right;padding:8px 10px;border-bottom:1px solid {_LINE};'>"
                    f"<span style='{pill_css}{pill_style}'>{growth}</span></td>"
                    f"</tr>"
                )
            st.markdown(
                f'<table style="width:100%;border-collapse:collapse;font-size:0.80rem;">'
                f'<thead><tr>'
                f'<th style="{th}text-align:left;">Kênh</th>'
                f'<th style="{th}text-align:right;">LK {current_year}</th>'
                f'<th style="{th}text-align:right;">LK {prev_year}</th>'
                f'<th style="{th}text-align:right;">Tăng trưởng</th>'
                f'</tr></thead>'
                f'<tbody>{rows_html}</tbody>'
                f'</table>',
                unsafe_allow_html=True,
            )

    # ── Section 3: Cổng thanh toán ────────────────────────────────────────────
    section_head("Cổng thanh toán")

    col_gw_bar, col_gw_tbl = st.columns(2)

    # Gateway
    gw_cy = gateway_df[gateway_df["nam"] == current_year] if not gateway_df.empty else pd.DataFrame()
    with col_gw_bar:
        if gw_cy.empty:
            st.warning("Chưa có dữ liệu cổng thanh toán.")
        else:
            gw_agg = gw_cy.groupby("cong", as_index=False).agg(
                rev=("doanh_thu", "sum"),
                orders=("so_don", "sum"),
            )
            gw_agg["rev_b"] = gw_agg["rev"] / 1e9
            gw_order = gw_agg.sort_values("rev_b", ascending=False)["cong"].tolist()
            colors_gw = [_BLUE, _BLUE2, _BLUE3, _BLUE4]
            gw_agg["_color"] = [colors_gw[i % len(colors_gw)] for i in range(len(gw_agg))]

            _chart_title("Cổng thanh toán — DT lũy kế")
            _chart_sub(f"Lũy kế {current_year} (tỷ đồng)")
            gw_chart = (
                alt.Chart(gw_agg)
                .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
                .encode(
                    x=alt.X("cong:N", title=None, sort=gw_order,
                            axis=alt.Axis(labelFontSize=11, labelColor=_INK)),
                    y=alt.Y("rev_b:Q", title="Tỷ đồng",
                            axis=alt.Axis(labelFontSize=10, labelColor=_MUTED)),
                    color=alt.Color("_color:N", scale=None, legend=None),
                    tooltip=[
                        alt.Tooltip("cong:N", title="Cổng"),
                        alt.Tooltip("rev_b:Q", title="Tỷ đồng", format=".2f"),
                    ],
                )
                .properties(height=200)
            )
            st.altair_chart(gw_chart.configure_view(strokeWidth=0), width='stretch')

    with col_gw_tbl:
        if gw_cy.empty:
            st.empty()
        else:
            _gw_total_orders = int(gw_agg["orders"].sum())
            _gw_total_rev_b  = gw_agg["rev_b"].sum()
            _chart_title("Cổng thanh toán — số đơn")
            _chart_sub(f"Số đơn lũy kế {current_year} · {_gw_total_orders:,} đơn")
            th2 = (
                f"font-size:0.65rem;font-weight:700;text-transform:uppercase;"
                f"color:{_MUTED};letter-spacing:0.07em;padding:8px 8px;"
                f"border-bottom:2px solid {_INK};"
            )
            td_r = f"text-align:right;padding:7px 8px;border-bottom:1px solid {_LINE};font-variant-numeric:tabular-nums;"
            td_l = f"text-align:left;font-weight:600;padding:7px 8px;border-bottom:1px solid {_LINE};"
            gw_rows = "".join(
                f"<tr><td style='{td_l}'>{row['cong']}</td>"
                f"<td style='{td_r}'>{int(row['orders']):,}</td>"
                f"<td style='{td_r}'>{row['rev_b']:.2f} tỷ</td></tr>"
                for _, row in gw_agg.sort_values("rev_b", ascending=False).iterrows()
            )
            td_tot = (
                f"font-weight:800;border-top:2px solid {_INK};border-bottom:none;"
                f"background:{_CARD};padding:7px 8px;font-variant-numeric:tabular-nums;"
            )
            st.markdown(
                f'<table style="width:100%;border-collapse:collapse;font-size:0.78rem;">'
                f'<thead><tr>'
                f'<th style="{th2}text-align:left;">Cổng</th>'
                f'<th style="{th2}text-align:right;">Đơn LK</th>'
                f'<th style="{th2}text-align:right;">DT LK</th>'
                f'</tr></thead>'
                f'<tbody>{gw_rows}'
                f'<tr>'
                f'<td style="text-align:left;{td_tot}">Tổng</td>'
                f'<td style="text-align:right;{td_tot}">{_gw_total_orders:,}</td>'
                f'<td style="text-align:right;{td_tot}">{_gw_total_rev_b:.2f} tỷ</td>'
                f'</tr>'
                f'</tbody></table>',
                unsafe_allow_html=True,
            )
