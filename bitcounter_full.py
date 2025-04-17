import streamlit as st
import streamlit.components.v1 as components
import requests
import matplotlib.pyplot as plt
import datetime
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np

# ----------------------------
# Configurazione pagina Streamlit
# ----------------------------
st.set_page_config(
    page_title="BITCOUNTER – Real Bitcoin Liquidity Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)
REFRESH_INTERVAL = 60

# ----------------------------
# Funzioni placeholder per recupero dati (da integrare con API)
# ----------------------------

def get_btc_circulating_supply():
    return 19600000  # BTC in circolazione

def get_btc_annual_mining_rate():
    return 328500  # BTC minati annualmente

def get_active_users():
    return 900000  # utenti attivi giornalieri (wallet)

def get_liquid_supply():
    return 7500000  # BTC liquidi stimati

def get_stablecoin_demand_proxy():
    return 30000000000  # Domanda in stablecoin (USD)

def get_days_since_genesis():
    genesis_block_date = datetime.date(2009, 1, 3)
    today = datetime.date.today()
    return (today - genesis_block_date).days

# ----------------------------
# API FETCH + CACHE
# ----------------------------
@st.cache_data(ttl=60)
def get_btc_price():
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin", "vs_currencies": "usd"},
            timeout=5
        )
        r.raise_for_status()
        return r.json()["bitcoin"]["usd"]
    except Exception:
        return None

@st.cache_data(ttl=300)
def get_blockchain_data():
    try:
        r = requests.get("https://api.blockchain.info/q/totalbc", timeout=5)
        r.raise_for_status()
        return {"btc_emitted": int(r.text) / 1e8}
    except Exception:
        return {"btc_emitted": None}

@st.cache_data(ttl=300)
def get_network_difficulty():
    try:
        r = requests.get("https://blockchain.info/q/getdifficulty", timeout=5)
        r.raise_for_status()
        return float(r.text)
    except Exception:
        return None

@st.cache_data(ttl=300)
def get_network_hashrate():
    try:
        r = requests.get("https://blockchain.info/q/hashrate", timeout=5)
        r.raise_for_status()
        return float(r.text)
    except Exception:
        return None

@st.cache_data(ttl=300)
def get_block_height():
    try:
        r = requests.get("https://blockchain.info/q/getblockcount", timeout=5)
        r.raise_for_status()
        return int(r.text)
    except Exception:
        return None

@st.cache_data(ttl=300)
def get_mempool_data():
    try:
        r = requests.get("https://mempool.space/api/mempool", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}

@st.cache_data(ttl=300)
def get_node_stats():
    try:
        r = requests.get("https://bitnodes.io/api/v1/snapshots/latest/", timeout=5)
        r.raise_for_status()
        return r.json().get("total_nodes")
    except Exception:
        return None

@st.cache_data(ttl=300)
def get_fear_greed_index():
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1&format=json", timeout=5)
        r.raise_for_status()
        data = r.json().get("data", [{}])[0]
        return {
            "value": int(data.get("value", 0)),
            "classification": data.get("value_classification", "N/A"),
            "timestamp": datetime.datetime.fromtimestamp(int(data.get("timestamp", 0)))
        }
    except Exception:
        return {"value": None, "classification": None, "timestamp": datetime.datetime.now()}

@st.cache_data(ttl=300)
def get_btc_news(count=5):
    try:
        rss_url = "https://news.google.com/rss/search?q=bitcoin&hl=en-US&gl=US&ceid=US:en"
        r = requests.get(rss_url, timeout=5)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        items = root.findall(".//item")[:count]
        news = []
        for item in items:
            news.append({
                "title": item.find("title").text,
                "link": item.find("link").text,
                "pubDate": item.find("pubDate").text
            })
        return news
    except Exception:
        return []

# ----------------------------
# Modelli di valutazione
# ----------------------------

def stock_to_flow_model():
    s2f = get_btc_circulating_supply() / get_btc_annual_mining_rate()
    return np.exp(3 * np.log(s2f) + 2)

def metcalfe_model():
    users = get_active_users()
    return 1e-5 * users ** 2

def liquidity_model():
    return get_stablecoin_demand_proxy() / get_liquid_supply()

def log_regression_model():
    t = get_days_since_genesis()
    return np.exp(0.5 * np.log(t) + 4)

def composite_price_model(alpha=0.25, beta=0.25, gamma=0.30, delta=0.20):
    p_s2f = stock_to_flow_model()
    p_metcalfe = metcalfe_model()
    p_liquidity = liquidity_model()
    p_log = log_regression_model()
    composite = alpha * p_s2f + beta * p_metcalfe + gamma * p_liquidity + delta * p_log
    return composite, {
        "Stock-to-Flow": p_s2f,
        "Metcalfe": p_metcalfe,
        "Liquidity": p_liquidity,
        "Log Regression": p_log
    }

# ----------------------------
# Effetto pioggia BTC sul background
# ----------------------------

def add_background_rain():
    html = """
    <style>/* omitted for brevity */</style>
    <div id=\"btc-container\"></div>
    <script>/* omitted for brevity */</script>
    """
    st.markdown(html, unsafe_allow_html=True)

# ----------------------------
# Utilities
# ----------------------------
def format_countdown(dt):
    now = datetime.datetime.now()
    diff = dt - now
    if diff.total_seconds() <= 0:
        return "Terminato"
    days = diff.days
    hours, rem = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{days}g {hours}h {minutes}m {seconds}s"

# ----------------------------
# Rendering functions
# ----------------------------
def render_metrics(em, price):
    circ = em or 0
    lost = 4_000_000
    dormant = 1_500_000
    liquid = max(circ - lost, 0)
    total = 21_000_000
    remaining = max(total - circ, 0)
    end_time = datetime.datetime.now() + datetime.timedelta(seconds=(remaining / 6.25) * 600)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Supply Massima", f"{total:,} BTC")
        st.metric("Supply Emessa", f"{circ:,} BTC")
        st.metric("Supply Liquida", f"{liquid:,} BTC")
        st.metric("BTC Persi", f"{lost:,} BTC")
        if price is not None:
            st.markdown(f"<span style='font-size: 1.1rem; font-weight: bold;'>Prezzo BTC:</span> ${price:,.2f} <span class='live-indicator'></span>", unsafe_allow_html=True)
        else:
            st.metric("Prezzo BTC", "N/A")
    with col2:
        st.metric("BTC da Minare", f"{remaining:,.2f} BTC")
        st.metric("Countdown Mining", format_countdown(end_time))

def render_network():
    diff = get_network_difficulty() or 0
    hashrate = (get_network_hashrate() or 0) / 1e9
    height = get_block_height() or 0
    next_halving = ((height // 210000) + 1) * 210000
    blocks_remaining = max(next_halving - height, 0)
    halving_time = datetime.datetime.now() + datetime.timedelta(seconds=blocks_remaining * 10 * 60)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Difficoltà", f"{diff:.2f}")
        st.metric("Hashrate", f"{hashrate:.2f} GH/s")
    with c2:
        st.metric("Block Height", f"{height}")
        st.metric("Tempo Medio Blocco", "10 min (target)")
    with c3:
        st.metric("Prox. Halving", f"{next_halving}")
        st.metric("Countdown Halving", format_countdown(halving_time))

def render_mempool():
    mp = get_mempool_data() or {}
    count = mp.get("count")
    vsize = mp.get("vsize")
    total_fee = mp.get("total_fee")
    avg_fee = (total_fee / count) if count else None
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Tx in Mempool", count or "N/A")
    with c2:
        st.metric("Dim. Mempool", f"{vsize} vbytes" if vsize else "N/A")
    with c3:
        st.metric("Fee Media", f"{avg_fee:.2f} sat" if avg_fee else "N/A")

def render_decentralization():
    nodes = get_node_stats() or 0
    st.metric("Nodi Attivi", nodes)

def render_sentiment_and_news():
    fg = get_fear_greed_index() or {"value":None, "classification":"N/A", "timestamp":datetime.datetime.now()}
    val = fg.get("value")
    cls = fg.get("classification")
    ts = fg.get("timestamp")
    st.metric(
        "Fear & Greed Index",
        f"{val} ({cls})" if val is not None else "N/A",
        delta=ts.strftime("%Y-%m-%d %H:%M")
    )
    st.markdown("**Ultime Notizie su Bitcoin**")
    for item in get_btc_news():
        title = item.get("title") or ""
        link = item.get("link") or ""
        pub = item.get("pubDate") or ""
        st.markdown(f"- [{title}]({link})  _{pub}_")

def render_charts(em, price):
    circ = em or 0
    lost = 4_000_000
    dormant = 1_500_000
    liquid = max(circ - lost, 0)
    real = price or 0
    theo = (price * circ / liquid) if liquid>0 and price else 0
    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots(figsize=(5,4))
        labels = ["Liquidi", "Dormienti", "Persi"]
        vals = [liquid - dormant, dormant, lost]
        ax.pie(vals, labels=labels, autopct="%1.1f%%", startangle=90)\n        ax.axis("equal")
        st.pyplot(fig)
    with c2:
        fig, ax = plt.subplots(figsize=(5,4))
        ax.bar(["Attuale", "Teorico"], [real, theo])
        ax.set_ylabel("USD")
        st.pyplot(fig)

def render_tradingview():
    widget = """
    <!-- TradingView Widget BEGIN -->
    <div class="tradingview-widget-container">
      <div id="tradingview_btc"></div>
      <script src="https://s3.tradingview.com/tv.js"></script>
      <script>
      new TradingView.widget({
        "width":"100%","height":500,
        "symbol":"COINBASE:BTCUSD",
        "interval":"60","timezone":"Etc/UTC",
        "theme":"light","style":"1","locale":"it",
        "toolbar_bg":"#f1




