import duckdb
import pandas as pd
import streamlit as st

_NUMERIC_COLS = ["tien_thuc_thu", "so_don_cap_moi", "phi_huy"]


def _require_token() -> str:
    try:
        return st.secrets["MOTHERDUCK_TOKEN"]
    except Exception:
        raise EnvironmentError("MOTHERDUCK_TOKEN chưa được cấu hình trong Streamlit secrets.")


def _md_con(token: str) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(f"md:bhtt_data?motherduck_token={token}")


@st.cache_data(ttl=300)
def load_partner_data() -> pd.DataFrame:
    token = _require_token()
    con = duckdb.connect(f"md:bhtt_data?motherduck_token={token}")
    df = con.execute("SELECT * FROM gold.partner_rev_data").df()
    con.close()
    df["ngay_ban_hang"] = pd.to_datetime(df["ngay_ban_hang"])
    for col in _NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["thang"] = df["thang"].astype(int)
    df["nam"]   = df["nam"].astype(int)
    if "nguon" in df.columns:
        df["nguon"] = df["nguon"].fillna("BC").astype(str)
    return df


@st.cache_data(ttl=300)
def load_bhs_data() -> pd.DataFrame:
    con = _md_con(_require_token())
    try:
        df = con.execute(
            "SELECT * FROM bronze.bhs_monthly ORDER BY nam, thang, kenh"
        ).df()
    except Exception:
        return pd.DataFrame(columns=["thang", "nam", "kenh", "doanh_thu"])
    finally:
        con.close()
    df["thang"]     = df["thang"].astype(int)
    df["nam"]       = df["nam"].astype(int)
    df["doanh_thu"] = pd.to_numeric(df["doanh_thu"], errors="coerce").fillna(0)
    return df


@st.cache_data(ttl=300)
def load_telesale_data() -> pd.DataFrame:
    con = _md_con(_require_token())
    try:
        df = con.execute(
            "SELECT * FROM bronze.telesale_monthly ORDER BY nam, thang"
        ).df()
    except Exception:
        return pd.DataFrame(columns=["thang", "nam", "leads", "buyers", "doanh_thu"])
    finally:
        con.close()
    df["thang"]     = df["thang"].astype(int)
    df["nam"]       = df["nam"].astype(int)
    df["leads"]     = pd.to_numeric(df["leads"],     errors="coerce").fillna(0).astype(int)
    df["buyers"]    = pd.to_numeric(df["buyers"],    errors="coerce").fillna(0).astype(int)
    df["doanh_thu"] = pd.to_numeric(df["doanh_thu"], errors="coerce").fillna(0)
    return df


@st.cache_data(ttl=300)
def load_gateway_data() -> pd.DataFrame:
    con = _md_con(_require_token())
    try:
        df = con.execute(
            "SELECT * FROM bronze.gateway_monthly ORDER BY nam, thang, cong"
        ).df()
    except Exception:
        return pd.DataFrame(columns=["thang", "nam", "cong", "so_don", "doanh_thu"])
    finally:
        con.close()
    df["thang"]     = df["thang"].astype(int)
    df["nam"]       = df["nam"].astype(int)
    df["so_don"]    = pd.to_numeric(df["so_don"],    errors="coerce").fillna(0).astype(int)
    df["doanh_thu"] = pd.to_numeric(df["doanh_thu"], errors="coerce").fillna(0)
    return df
