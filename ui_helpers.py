import streamlit as st
from data_loader import load_partner_data

PARTNER_CHANNEL_DISPLAY: dict[str, str] = {
    "SHINHAN":    "Shinhan Bank",
    "SHINHAN_CB": "Shinhan Bank (Cyber)",
    "VPBANK":     "VPBank",
    "VPBANK_T":   "VPBank (Tài sản)",
    "ABBANK":     "ABBank",
    "IPAY_TL":    "Kênh IPAY",
    "WEB_APP":    "Web/App",
    "TVV":        "Tư vấn viên",
    "BHTT_TSC":   "TSC",
    "THANGLONG":  "Thăng Long",
    "LITE_EXPL":  "Lite Exploration",
    "LITE_X":     "Lite X",
}

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


def fmt_currency(value: float) -> str:
    billions = value / 1_000_000_000
    if billions >= 1:
        return f"{billions:,.2f} tỷ"
    return f"{value / 1_000_000:,.1f} tr"


def _fmt_vnd(v: float) -> str:
    if abs(v) >= 1_000_000_000:
        return f"{v / 1_000_000_000:.2f} tỷ"
    return f"{v / 1_000_000:.2f} triệu"


def yoy_caption(current_val: float, yoy_val: float, fmt_fn, prev_year: int) -> str:
    if yoy_val == 0:
        return f'<span style="font-size:0.56rem;color:{_MUTED}">Cùng kỳ {prev_year}: N/A</span>'
    pct   = (current_val - yoy_val) / abs(yoy_val)
    arrow = "▲" if pct > 0 else "▼"
    color = _POS if pct > 0 else _NEG
    return (
        f'<span style="font-size:0.56rem;color:{_MUTED}">Cùng kỳ {prev_year}: {fmt_fn(yoy_val)}&nbsp;&nbsp;</span>'
        f'<span style="font-size:0.56rem;font-weight:700;color:{color}">{arrow} {pct:+.1%}</span>'
    )


def kpi_card(
    label: str,
    value: str,
    delta_str: str,
    delta_color: str,
    accent_color: str = _BLUE,
    yoy_html: str = "",
    tooltip: str = "",
    subtitle: str = "",
) -> str:
    _label_html = label
    if tooltip:
        _label_html += (
            f'&nbsp;<abbr title="{tooltip}" '
            f'style="font-size:0.65rem;color:#aaa;cursor:help;text-decoration:none;">ℹ</abbr>'
        )
    sidebar = f'<div style="width:4px;border-radius:2px;background:{accent_color};flex-shrink:0;"></div>'
    parts = [
        f'<div style="background:{_CARD};border:1.5px solid {_LINE};border-radius:4px;'
        f'padding:16px 16px 13px 16px;box-shadow:0 1px 4px rgba(0,0,0,0.06);'
        f'display:flex;gap:10px;align-items:stretch;min-height:120px;">',
        sidebar,
        f'<div style="flex:1;min-width:0;">',
        f'<div style="font-size:0.55rem;font-weight:700;color:{_MUTED};text-transform:uppercase;'
        f'letter-spacing:0.10em;margin-bottom:8px;">{_label_html}</div>',
        f'<div style="font-size:1.5rem;font-weight:600;color:{_INK};line-height:1.05;'
        f'letter-spacing:-0.01em;">{value}</div>',
    ]
    if subtitle:
        parts.append(f'<div style="font-size:0.56rem;color:{_MUTED};margin-top:2px;">{subtitle}</div>')
    parts.append(
        f'<div style="margin-top:7px;font-size:0.72rem;font-weight:700;color:{delta_color};">{delta_str}</div>'
    )
    if yoy_html:
        parts.append(f'<div style="margin-top:3px;">{yoy_html}</div>')
    parts += ['</div>', '</div>']
    return "".join(parts)


def section_head(title: str, tag: str = "") -> None:
    tag_html = (
        f'<span style="font-size:0.69rem;font-weight:700;color:{_BLUE};'
        f'letter-spacing:0.10em;white-space:nowrap;">{tag}</span>'
        if tag else ""
    )
    st.markdown(
        f'<div style="display:flex;align-items:baseline;gap:12px;margin:32px 0 14px;">'
        f'<h2 style="font-size:1.18rem;font-weight:600;color:{_INK};'
        f'letter-spacing:-0.01em;white-space:nowrap;margin:0;">{title}</h2>'
        f'<div style="flex:1;height:1.5px;background:{_LINE};"></div>'
        f'{tag_html}'
        f'</div>',
        unsafe_allow_html=True,
    )



def _chart_title(text: str) -> None:
    st.markdown(
        f'<p style="font-size:0.78rem;font-weight:700;color:{_INK};'
        f'letter-spacing:0.06em;text-transform:uppercase;'
        f'margin:0 0 2px 0;line-height:1.3;">{text}</p>',
        unsafe_allow_html=True,
    )


def _chart_sub(text: str) -> None:
    st.markdown(
        f'<p style="font-size:0.67rem;color:{_MUTED};margin:0 0 10px 0;">{text}</p>',
        unsafe_allow_html=True,
    )


def channel_display(nguon_kt: str, ten_nguon_kt: str) -> str:
    if nguon_kt in PARTNER_CHANNEL_DISPLAY:
        return PARTNER_CHANNEL_DISPLAY[nguon_kt]
    return ten_nguon_kt or nguon_kt


def render_action_buttons() -> None:
    if st.button("⟳ Làm mới dữ liệu", width="stretch",
                 help="Xóa cache và tải lại dữ liệu mới nhất từ MotherDuck"):
        load_partner_data.clear()
        st.rerun()
