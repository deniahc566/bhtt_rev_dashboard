import sys
import base64
from pathlib import Path

_HERE = Path(__file__).parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from pages.overview import render_overview_page
from pages.detail   import render_detail_page
from ui_helpers     import render_action_buttons

_BLUE  = "#1558d6"
_LINE  = "#d0d8e4"
_INK   = "#0d1a2e"

st.set_page_config(
    page_title="VBI Đối tác Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
    <style>
    [data-testid='stSidebarNav'] { display: none; }
    #MainMenu, footer { visibility: hidden; }

    [data-testid="stSidebar"] {
        background-color: #005992 !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding: 0 !important;
    }

    /* Tab styling */
    [data-baseweb="tab-list"] {
        gap: 0 !important;
        border-bottom: 1.5px solid #d8d1bd !important;
        background: transparent !important;
    }
    [data-baseweb="tab"] {
        font-size: 13px !important;
        font-weight: 700 !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
        padding: 14px 24px !important;
        color: #6c6754 !important;
        background: transparent !important;
        border-radius: 0 !important;
        border: none !important;
    }
    [data-baseweb="tab"]:hover { color: #0d1a2e !important; }
    [aria-selected="true"][data-baseweb="tab"] {
        color: #1558d6 !important;
        background: transparent !important;
        border-bottom: 3px solid #1558d6 !important;
    }
    [data-baseweb="tab-highlight"] { display: none !important; }
    [data-baseweb="tab-border"] { display: none !important; }

    /* Tighten main padding */
    section[data-testid="stMain"] .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# ── Auth ──────────────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    _lock_svg = (
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" '
        'xmlns="http://www.w3.org/2000/svg">'
        '<path d="M12 17C10.89 17 10 16.1 10 15C10 13.89 10.89 13 12 13'
        'C13.1 13 14 13.9 14 15C14 16.1 13.1 17 12 17M18 20V10H6V20H18'
        'M18 8C19.1 8 20 8.89 20 10V20C20 21.1 19.1 22 18 22H6'
        'C4.89 22 4 21.1 4 20V10C4 8.9 4.89 8 6 8H7V6'
        'C7 3.24 9.24 1 12 1C14.76 1 17 3.24 17 6V8H18'
        'M12 3C10.34 3 9 4.34 9 6V8H15V6C15 4.34 13.66 3 12 3Z" '
        'fill="#000000"/></svg>'
    )
    _lock_icon = "data:image/svg+xml;base64," + base64.b64encode(_lock_svg.encode()).decode()

    st.markdown(f"""
        <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}
        .stApp {{
            background: linear-gradient(180deg, #83CCF1 0%, #F2F4F8 70.9%);
        }}
        .main .block-container {{
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            max-width: 100% !important;
        }}
        [data-testid="stForm"] {{
            position: relative !important;
            z-index: 10 !important;
            width: 611px !important;
            background: linear-gradient(180deg, #C7F0FE 0%, #FEFEFE 62.78%) !important;
            box-shadow: 0 4px 10px 1px rgba(0, 0, 0, 0.15) !important;
            border-radius: 50px !important;
            padding: 73px 88px 95px !important;
            border: none !important;
            margin: 60px auto 0 !important;
        }}
        [data-baseweb="input"] {{
            position: relative !important;
            background: #ffffff !important;
            border: 1px solid #83CCF1 !important;
            border-radius: 15px !important;
            height: 52px !important;
        }}
        [data-baseweb="input"]::before {{
            content: "" !important;
            position: absolute !important;
            left: 14px !important;
            top: 50% !important;
            transform: translateY(-50%) !important;
            width: 22px !important;
            height: 22px !important;
            background-image: url("{_lock_icon}") !important;
            background-size: contain !important;
            background-repeat: no-repeat !important;
            pointer-events: none !important;
            z-index: 1 !important;
        }}
        [data-baseweb="input"] input {{
            padding-left: 44px !important;
            background: transparent !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            color: #000 !important;
        }}
        [data-testid="stFormSubmitButton"] {{ margin-top: 71px !important; }}
        [data-testid="stFormSubmitButton"] > button {{
            width: auto !important;
            padding: 0 32px !important;
            height: 48px !important;
            background: linear-gradient(90deg, #98EEFF 0%, #C6F6FF 100%) !important;
            color: #000000 !important;
            border: none !important;
            border-radius: 15px !important;
            font-size: 20px !important;
            font-weight: 600 !important;
        }}
        </style>
        <div style="position:fixed;inset:0;overflow:hidden;pointer-events:none;z-index:0;">
            <div style="position:absolute;width:1441px;height:1330px;left:-405px;top:-376px;
                background:linear-gradient(90deg,#98EEFF 0%,#F2F4F8 100%);
                border-radius:50px;transform:rotate(90deg);"></div>
        </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        st.markdown("""
            <div style="text-align:center;">
                <p style="font-size:28px;font-weight:600;color:#000;margin:0 0 43px;line-height:1.2;">
                    Báo cáo doanh thu VBI — Đối tác
                </p>
                <p style="font-size:15px;font-weight:600;color:#999;margin:0 0 20px;">
                    Nhập mật khẩu để đăng nhập
                </p>
            </div>
        """, unsafe_allow_html=True)
        pwd = st.text_input("Mật khẩu", placeholder="Nhập mật khẩu", type="password",
                            label_visibility="collapsed")
        submitted = st.form_submit_button("Đăng nhập")
        if submitted:
            if pwd == st.secrets["APP_PASSWORD"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Mật khẩu không đúng.")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="padding:24px 20px 20px;border-bottom:1px solid rgba(255,255,255,0.15);margin-bottom:16px;">
            <div style="color:rgba(255,255,255,0.6);font-size:10px;font-weight:700;
                letter-spacing:0.18em;text-transform:uppercase;margin-bottom:6px;">
                VietinBank Insurance
            </div>
            <span style="color:white;font-size:17px;font-weight:700;line-height:1.2;">
                Ban Bảo hiểm<br>Trực tuyến
            </span>
        </div>
    """, unsafe_allow_html=True)
    render_action_buttons()

# ── Header ─────────────────────────────────────────────────────────────────────
import datetime
_now = datetime.date.today()
_period_label = f"T{_now.month} / {_now.year}"

st.markdown(
    f'<div style="display:flex;justify-content:space-between;align-items:flex-end;'
    f'border-bottom:2.5px solid {_INK};padding-bottom:18px;margin-bottom:4px;flex-wrap:wrap;gap:12px;">'
    f'<div>'
    f'<div style="font-size:0.67rem;font-weight:700;letter-spacing:0.22em;text-transform:uppercase;'
    f'color:{_BLUE};margin-bottom:6px;">VietinBank Insurance · Ban Bảo hiểm Trực tuyến</div>'
    f'<h1 style="font-size:2.0rem;font-weight:600;color:{_INK};letter-spacing:-0.02em;'
    f'margin:0;line-height:1.05;">Báo cáo <strong style="font-style:normal;font-weight:700;color:{_BLUE};">Doanh số</strong>'
    f' Ban BHTT</h1>'
    f'</div>'
    f'<div style="text-align:right;">'
    f'<div style="font-size:1.6rem;font-weight:600;color:{_INK};line-height:1;">{_period_label}</div>'
    f'<div style="font-size:0.67rem;letter-spacing:0.14em;text-transform:uppercase;'
    f'color:#6c6754;margin-top:5px;">Lũy kế T1–T{_now.month} · So cùng kỳ {_now.year - 1}</div>'
    f'</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["① Tổng quan doanh số", "② Chi tiết đối tác"])

with tab1:
    render_overview_page()

with tab2:
    render_detail_page()
