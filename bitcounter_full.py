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
    r = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={"ids": "bitcoin", "vs_currencies": "usd"},
        timeout=5
    )
    r.raise_for_status()
    return r.json()["bitcoin"]["usd"]

@st.cache_data(ttl=300)
def get_blockchain_data():
    r = requests.get("https://api.blockchain.info/q/totalbc", timeout=5)
    r.raise_for_status()
    return {"btc_emitted": int(r.text) / 1e8}

@st.cache_data(ttl=300)
def get_network_difficulty():
    r = requests.get("https://blockchain.info/q/getdifficulty", timeout=5)
    r.raise_for_status()
    return float(r.text)

@st.cache_data(ttl=300)
def get_network_hashrate():
    r = requests.get("https://blockchain.info/q/hashrate", timeout=5)
    r.raise_for_status()
    return float(r.text)

@st.cache_data(ttl=300)
def get_block_height():
    r = requests.get("https://blockchain.info/q/getblockcount", timeout=5)
    r.raise_for_status()
    return int(r.text)

@st.cache_data(ttl=300)
def get_mempool_data():
    r = requests.get("https://mempool.space/api/mempool", timeout=5)
    r.raise_for_status()
    return r.json()

@st.cache_data(ttl=300)
def get_node_stats():
    r = requests.get("https://bitnodes.io/api/v1/snapshots/latest/", timeout=5)
    r.raise_for_status()
    return r.json().get("total_nodes")

@st.cache_data(ttl=300)
def get_fear_greed_index():
    r = requests.get("https://api.alternative.me/fng/?limit=1&format=json", timeout=5)
    r.raise_for_status()
    data = r.json()["data"][0]
    return {
        "value": int(data["value"]),
        "classification": data["value_classification"],
        "timestamp": datetime.datetime.fromtimestamp(int(data["timestamp"]))
    }

@st.cache_data(ttl=300)
def get_btc_news(count=5):
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
    return composite, {"Stock-to-Flow": p_s2f, "Metcalfe": p_metcalfe, "Liquidity": p_liquidity, "Log Regression": p_log}

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
# Renderer e utilities
# ----------------------------
def format_countdown(dt):
    diff = dt - datetime.datetime.now()
    if diff.total_seconds() <= 0:
        return "Terminato"
    days, rem = diff.days, diff.seconds
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{days}g {hours}h {minutes}m {seconds}s"

# Rendering functions as in the original...
# ... (render_metrics, render_network, render_mempool, render_decentralization,
#     render_sentiment_and_news, render_charts, render_tradingview)

# ----------------------------
# Main
# ----------------------------
def main():
    add_background_rain()
    st.header("Calcoli e Stime")
    price = get_btc_price()
    bc = get_blockchain_data()
    emitted = bc.get('btc_emitted', 0)

    render_metrics(emitted, price)
    render_network()
    render_mempool()
    render_decentralization()
    render_sentiment_and_news()
    render_charts(emitted, price)
    render_tradingview()

if __name__ == "__main__":
    main()

