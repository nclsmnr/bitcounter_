import streamlit as st
import streamlit.components.v1 as components
import requests
import matplotlib.pyplot as plt
import datetime
import xml.etree.ElementTree as ET

# =====================================================
# CONFIGURAZIONE E COSTANTI
# =====================================================
st.set_page_config(
    page_title="BITCOUNTER – Real Bitcoin Liquidity Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# EFFETTO DI PIOGGIA DI BTC IN BACKGROUND
# =====================================================
def add_background_rain():
    html = """
   <style>
  @keyframes fall {{ 
    0%   {{ transform: translateY(-100%); opacity: 0 }} 
    10%  {{ opacity: 1 }} 
    100% {{ transform: translateY(100vh); opacity: 0 }} 
  }}
  .btc {{
    position: absolute;
    top: -10%;
    font-size: 24px;
    color: gold;
    user-select: none;
    animation-name: fall;
    animation-timing-function: linear;
    animation-iteration-count: 1;
  }}
  
</style>

<div id="btc-container" style="position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:-1;"></div>
<script>
// Pioggia di ₿
setInterval(() => {{
  const c = document.getElementById("btc-container");
  const d = document.createElement("div");
  d.className = "btc";
  d.innerText = "₿";
  d.style.left = Math.random()*100 + "%";
  const t = 5 + Math.random()*10;
  d.style.animationDuration = t + "s";
  d.style.animationDelay    = Math.random()*t + "s";
  c.appendChild(d);
  setTimeout(()=>d.remove(), t*1000);
}}, 200);

# =====================================================
# API FETCH + CACHE
# =====================================================
@st.cache_data(ttl=60)
def get_btc_price():
    r = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={"ids":"bitcoin","vs_currencies":"usd"},
        timeout=5
    )
    r.raise_for_status()
    return r.json()["bitcoin"]["usd"]

@st.cache_data(ttl=60)
def get_blockchain_data():
    r = requests.get("https://api.blockchain.info/q/totalbc", timeout=5)
    r.raise_for_status()
    return {"btc_emitted": int(r.text) / 1e8}

@st.cache_data(ttl=60)
def get_network_difficulty():
    r = requests.get("https://blockchain.info/q/getdifficulty", timeout=5)
    r.raise_for_status()
    return float(r.text)

@st.cache_data(ttl=60)
def get_network_hashrate():
    r = requests.get("https://blockchain.info/q/hashrate", timeout=5)
    r.raise_for_status()
    return float(r.text)

@st.cache_data(ttl=60)
def get_block_height():
    r = requests.get("https://blockchain.info/q/getblockcount", timeout=5)
    r.raise_for_status()
    return int(r.text)

@st.cache_data(ttl=60)
def get_mempool_data():
    r = requests.get("https://mempool.space/api/mempool", timeout=5)
    r.raise_for_status()
    return r.json()

@st.cache_data(ttl=60)
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

# =====================================================
# CALCOLI & STIME
# =====================================================
def estimate_real_supply(em, lost=4_000_000, dormant=1_500_000):
    circ = em
    liq = circ - lost
    return {
        "total": 21_000_000,
        "circulating": circ,
        "liquid": liq,
        "lost": lost,
        "dormant": dormant
    }

def estimate_remaining_btc(em):
    return 21_000_000 - em

def estimate_mining_countdown(em):
    reward = 6.25
    remaining = estimate_remaining_btc(em)
    blocks = remaining / reward
    seconds = blocks * 10 * 60
    return datetime.datetime.now() + datetime.timedelta(seconds=seconds)

def format_countdown(dt):
    now = datetime.datetime.now()
    diff = dt - now
    if diff.total_seconds() <= 0:
        return "Terminato"
    days = diff.days
    hours, rem = divmod(diff.seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{days}g {hours}h {minutes}m {secs}s"

# =====================================================
# RENDER SEZIONI
# =====================================================
# (le sezioni rimangono invariate rispetto alla versione precedente)
# ... [omesse per brevità] ...

# =====================================================
# MAIN
# =====================================================
def main():
    add_background_rain()

    st.title("BITCOUNTER – Real Bitcoin Liquidity Dashboard")
    st.info("Dati aggiornati ogni minuto (auto-refresh disattivato per compatibilità grafica)")

    price = get_btc_price()
    bc = get_blockchain_data()
    if price is None or bc['btc_emitted'] is None:
        st.error("Errore recupero dati.")
        return
    emitted = bc['btc_emitted']

    st.header("Calcoli e Stime")
    render_metrics(emitted, price)

    st.header("Statistiche di Rete")
    render_network()

    st.header("Transazioni & Mempool")
    render_mempool()

    st.header("Decentralizzazione")
    render_decentralization()

    st.header("Sentiment & News")
    render_sentiment_and_news()

    st.header("Grafici Matplotlib")
    render_charts(emitted, price)

    st.header("Grafico a Candele TradingView")
    render_tradingview()

if __name__ == "__main__":
    main()











