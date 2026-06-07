import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analytics.analytics import (
    load_transactions, get_summary, get_category_breakdown,
    get_monthly_trend, get_daily_spending, detect_anomalies, get_top_expenses
)

API_URL = "http://localhost:8000"

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinLens · Expense Tracker",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── THEME & CUSTOM CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

:root {
    --bg: #0d0f14;
    --surface: #13161e;
    --surface2: #1a1f2e;
    --accent: #7DF9C2;
    --accent2: #5B8EF0;
    --accent3: #F0825B;
    --text: #E8EAF2;
    --muted: #6b7280;
    --border: rgba(125,249,194,0.12);
    --card-shadow: 0 4px 32px rgba(0,0,0,0.4);
}

html, body, [class*="css"] {
    font-family: 'DM Mono', monospace;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* Hide default header */
header[data-testid="stHeader"] { display: none; }
.block-container { padding-top: 1.5rem !important; }

/* Cards */
.fin-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    box-shadow: var(--card-shadow);
    position: relative;
    overflow: hidden;
}
.fin-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
}

/* Metric cards */
.metric-val {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -1px;
    line-height: 1;
}
.metric-label {
    font-size: 0.72rem;
    color: var(--muted);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}
.metric-positive { color: var(--accent); }
.metric-negative { color: var(--accent3); }
.metric-neutral  { color: var(--accent2); }

/* Section headers */
.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Page title */
.page-title {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -1px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* Alert box */
.anomaly-card {
    background: rgba(240,130,91,0.08);
    border: 1px solid rgba(240,130,91,0.3);
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.82rem;
}

/* Streamlit widgets tweaks */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
    font-family: 'DM Mono', monospace !important;
}
.stButton > button {
    background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    color: #0d0f14 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.4rem !important;
    letter-spacing: 0.04em;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* Dataframe */
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }

/* Divider */
hr { border-color: var(--border) !important; }

/* Tab styling */
.stTabs [data-baseweb="tab-list"] { gap: 4px; background: var(--surface) !important; border-radius: 10px; padding: 4px; }
.stTabs [data-baseweb="tab"] { border-radius: 8px !important; color: var(--muted) !important; font-family: 'DM Mono', monospace !important; }
.stTabs [aria-selected="true"] { background: var(--surface2) !important; color: var(--accent) !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='DM Mono, monospace', color='#E8EAF2', size=11),
    margin=dict(l=10, r=10, t=30, b=10),
    colorway=['#7DF9C2','#5B8EF0','#F0825B','#C77DFF','#FFD166','#06D6A0'],
    legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(size=10)),
    xaxis=dict(gridcolor='rgba(255,255,255,0.05)', zerolinecolor='rgba(255,255,255,0.05)'),
    yaxis=dict(gridcolor='rgba(255,255,255,0.05)', zerolinecolor='rgba(255,255,255,0.05)')
)

# ── SESSION STATE ────────────────────────────────────────────────────────────
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = ""

# ── API HELPERS ───────────────────────────────────────────────────────────────
def api_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

def fetch_transactions():
    try:
        r = requests.get(f"{API_URL}/transactions/", headers=api_headers())
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []

# ── AUTH PAGE ─────────────────────────────────────────────────────────────────
def auth_page():
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown('<div class="page-title">💠 FinLens</div>', unsafe_allow_html=True)
        st.markdown('<p style="color:#6b7280;font-size:0.85rem;margin-bottom:1.5rem">Smart expense tracking & analytics</p>', unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

        with tab_login:
            st.markdown('<div class="fin-card">', unsafe_allow_html=True)
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Sign In →", use_container_width=True):
                try:
                    r = requests.post(f"{API_URL}/auth/login",
                        data={"username": username, "password": password})
                    if r.status_code == 200:
                        st.session_state.token = r.json()["access_token"]
                        st.session_state.username = username
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                except:
                    st.error("Cannot connect to API. Start the backend first.")
            st.markdown('</div>', unsafe_allow_html=True)

        with tab_register:
            st.markdown('<div class="fin-card">', unsafe_allow_html=True)
            new_user = st.text_input("Username", key="reg_user")
            new_email = st.text_input("Email", key="reg_email")
            new_pass = st.text_input("Password", type="password", key="reg_pass")
            if st.button("Create Account →", use_container_width=True):
                try:
                    r = requests.post(f"{API_URL}/auth/register",
                        json={"username": new_user, "email": new_email, "password": new_pass})
                    if r.status_code == 201:
                        st.success("Account created! Sign in now.")
                    else:
                        st.error(r.json().get("detail", "Error"))
                except:
                    st.error("Cannot connect to API.")
            st.markdown('</div>', unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown(f'<div class="page-title" style="font-size:1.4rem">💠 FinLens</div>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:#6b7280;font-size:0.78rem;margin-bottom:1.2rem">Logged in as <span style="color:#7DF9C2">{st.session_state.username}</span></p>', unsafe_allow_html=True)
        st.markdown("---")

        page = st.radio("Navigation", ["📊 Dashboard", "➕ Add Transaction", "📋 Transactions", "⚠️ Anomalies"], label_visibility="collapsed")

        st.markdown("---")
        if st.button("Sign Out", use_container_width=True):
            st.session_state.token = None
            st.session_state.username = ""
            st.rerun()
        return page

# ── DASHBOARD PAGE ────────────────────────────────────────────────────────────
def dashboard_page(df, summary):
    st.markdown('<div class="page-title">Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#6b7280;font-size:0.82rem;margin-bottom:1.5rem">Your financial overview at a glance</p>', unsafe_allow_html=True)

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'''<div class="fin-card">
            <div class="metric-label">Total Income</div>
            <div class="metric-val metric-positive">₹{summary["total_income"]:,.0f}</div>
        </div>''', unsafe_allow_html=True)
    with c2:
        st.markdown(f'''<div class="fin-card">
            <div class="metric-label">Total Expense</div>
            <div class="metric-val metric-negative">₹{summary["total_expense"]:,.0f}</div>
        </div>''', unsafe_allow_html=True)
    with c3:
        color = "metric-positive" if summary["net_balance"] >= 0 else "metric-negative"
        st.markdown(f'''<div class="fin-card">
            <div class="metric-label">Net Balance</div>
            <div class="metric-val {color}">₹{summary["net_balance"]:,.0f}</div>
        </div>''', unsafe_allow_html=True)
    with c4:
        st.markdown(f'''<div class="fin-card">
            <div class="metric-label">Savings Rate</div>
            <div class="metric-val metric-neutral">{summary["savings_rate"]:.1f}%</div>
        </div>''', unsafe_allow_html=True)

    if df.empty:
        st.info("No transactions yet. Add some to see your analytics!")
        return

    col_l, col_r = st.columns([1.1, 1])

    with col_l:
        st.markdown('<div class="section-title">📈 Monthly Cash Flow</div>', unsafe_allow_html=True)
        monthly = get_monthly_trend(df)
        if not monthly.empty:
            fig = px.bar(monthly, x='month', y='amount', color='type',
                         barmode='group',
                         color_discrete_map={'income': '#7DF9C2', 'expense': '#F0825B'})
            fig.update_layout(**PLOTLY_LAYOUT, height=270)
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-title">🍩 Expense Breakdown</div>', unsafe_allow_html=True)
        cat = get_category_breakdown(df)
        if not cat.empty:
            fig2 = px.pie(cat, values='amount', names='category', hole=0.62)
            fig2.update_layout(**PLOTLY_LAYOUT, height=270, showlegend=True)
            fig2.update_traces(textinfo='percent', textfont_size=10,
                               marker=dict(line=dict(color='#0d0f14', width=2)))
            st.plotly_chart(fig2, use_container_width=True)

    col_bl, col_br = st.columns([1, 1.1])

    with col_bl:
        st.markdown('<div class="section-title">🔝 Top Expenses</div>', unsafe_allow_html=True)
        top = get_top_expenses(df)
        if not top.empty:
            top['date'] = pd.to_datetime(top['date']).dt.strftime('%b %d')
            st.dataframe(top.style.format({'amount': '₹{:,.0f}'}),
                         use_container_width=True, hide_index=True, height=220)

    with col_br:
        st.markdown('<div class="section-title">📅 Daily Spending</div>', unsafe_allow_html=True)
        daily = get_daily_spending(df)
        if not daily.empty:
            fig3 = px.area(daily, x='date', y='amount',
                           color_discrete_sequence=['#5B8EF0'])
            fig3.update_traces(fill='tozeroy', fillcolor='rgba(91,142,240,0.12)', line_width=2)
            fig3.update_layout(**PLOTLY_LAYOUT, height=220)
            st.plotly_chart(fig3, use_container_width=True)

# ── ADD TRANSACTION PAGE ──────────────────────────────────────────────────────
def add_transaction_page():
    st.markdown('<div class="page-title">Add Transaction</div>', unsafe_allow_html=True)

    EXPENSE_CATS = ["Food & Dining", "Transport", "Shopping", "Entertainment",
                    "Healthcare", "Education", "Utilities", "Rent", "Other"]
    INCOME_CATS  = ["Salary", "Freelance", "Investment", "Gift", "Other"]

    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.markdown('<div class="fin-card">', unsafe_allow_html=True)
        title = st.text_input("Transaction Title")
        amount = st.number_input("Amount (₹)", min_value=0.01, step=10.0)
        txn_type = st.selectbox("Type", ["expense", "income"])
        categories = EXPENSE_CATS if txn_type == "expense" else INCOME_CATS
        category = st.selectbox("Category", categories)
        txn_date = st.date_input("Date", value=date.today())
        note = st.text_input("Note (optional)")

        if st.button("Add Transaction →", use_container_width=True):
            if not title:
                st.warning("Please enter a title.")
            else:
                payload = {
                    "title": title, "amount": amount, "type": txn_type,
                    "category": category, "note": note,
                    "date": datetime.combine(txn_date, datetime.min.time()).isoformat()
                }
                r = requests.post(f"{API_URL}/transactions/", json=payload, headers=api_headers())
                if r.status_code == 201:
                    st.success("✅ Transaction added!")
                else:
                    st.error("Failed to add transaction.")
        st.markdown('</div>', unsafe_allow_html=True)

# ── TRANSACTIONS PAGE ─────────────────────────────────────────────────────────
def transactions_page(df, raw):
    st.markdown('<div class="page-title">Transactions</div>', unsafe_allow_html=True)
    if df.empty:
        st.info("No transactions found.")
        return

    col1, col2 = st.columns(2)
    with col1:
        type_filter = st.selectbox("Filter by Type", ["All", "income", "expense"])
    with col2:
        cats = ["All"] + sorted(df['category'].unique().tolist())
        cat_filter = st.selectbox("Filter by Category", cats)

    filtered = df.copy()
    if type_filter != "All":
        filtered = filtered[filtered['type'] == type_filter]
    if cat_filter != "All":
        filtered = filtered[filtered['category'] == cat_filter]

    display = filtered[['date','title','category','type','amount','note']].copy()
    display['date'] = pd.to_datetime(display['date']).dt.strftime('%b %d, %Y')
    display['amount'] = display['amount'].apply(lambda x: f"₹{x:,.2f}")

    st.dataframe(display, use_container_width=True, hide_index=True, height=400)
    st.caption(f"Showing {len(display)} of {len(df)} transactions")

    st.markdown("---")
    st.markdown('<div class="section-title">🗑 Delete Transaction</div>', unsafe_allow_html=True)
    ids = [t['id'] for t in raw]
    titles = [f"#{t['id']} — {t['title']} (₹{t['amount']})" for t in raw]
    if ids:
        selected = st.selectbox("Select transaction to delete", titles)
        idx = titles.index(selected)
        if st.button("Delete Selected"):
            r = requests.delete(f"{API_URL}/transactions/{ids[idx]}", headers=api_headers())
            if r.status_code == 200:
                st.success("Deleted successfully.")
                st.rerun()
            else:
                st.error("Failed to delete.")

# ── ANOMALIES PAGE ────────────────────────────────────────────────────────────
def anomalies_page(df):
    st.markdown('<div class="page-title">Anomaly Detection</div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#6b7280;font-size:0.82rem;margin-bottom:1.2rem">Transactions that deviate significantly from your spending patterns (2σ threshold)</p>', unsafe_allow_html=True)
    anomalies = detect_anomalies(df)
    if not anomalies:
        st.success("✅ No unusual spending detected. Your finances look healthy!")
        return
    st.warning(f"⚠️ {len(anomalies)} unusual transaction(s) detected")
    for a in anomalies:
        dt = pd.to_datetime(a['date']).strftime('%b %d, %Y') if a.get('date') else 'N/A'
        st.markdown(f'''<div class="anomaly-card">
            <strong style="color:#F0825B">{a["title"]}</strong> &nbsp;·&nbsp;
            <span style="color:#7DF9C2">₹{a["amount"]:,.2f}</span> &nbsp;·&nbsp;
            <span style="color:#6b7280">{a["category"]}</span> &nbsp;·&nbsp;
            <span style="color:#6b7280">{dt}</span>
        </div>''', unsafe_allow_html=True)

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    if not st.session_state.token:
        auth_page()
        return

    page = render_sidebar()
    raw = fetch_transactions()
    df = load_transactions(raw)
    summary = get_summary(df)

    if page == "📊 Dashboard":
        dashboard_page(df, summary)
    elif page == "➕ Add Transaction":
        add_transaction_page()
    elif page == "📋 Transactions":
        transactions_page(df, raw)
    elif page == "⚠️ Anomalies":
        anomalies_page(df)

if __name__ == "__main__":
    main()