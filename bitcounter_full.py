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
REFRESH_INTERVAL = 60

# =====================================================
# EFFETTO DI PIOGGIA DI BTC IN BACKGROUND
# =====================================================
def add_background_rain():
    html = """
    <style>
      @keyframes fall {
          0% { transform: translateY(-100%); opacity: 0; }
          10% { opacity: 1; }
          100% { transform: translateY(100vh); opacity: 0; }
      }
      .btc {
          position: absolute;
          top: -10%;
          font-size: 24px;
          color: gold;
          user-select: none;
          animation-name: fall;
          animation-timing-function: linear;
          animation-iteration-count: 1;
      }
      .live-indicator {
          display: inline-block;
          width: 10px;
          height: 10px;
          background-color: #00FF00;
          border-radius: 50%;
          margin-left: 6px;
          animation: blink 1s infinite;
      }
      @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.2; }
      }
    </style>
    <div id="btc-container" style="position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:-1;"></div>
    <script>
    (function(){
      var container = document.getElementById('btc-container');
      function createBTC(){
        var d = document.createElement('div');
        d.className = 'btc';
        d.innerText = '₿';
        d.style.left = Math.random() * 100 + '%';
        var duration = 5 + Math.random() * 10;
        d.style.animationDuration = duration + 's';
        d.style.animationDelay = Math.random() * duration + 's';
        container.appendChild(d);
        setTimeout(function(){ d.remove(); }, duration * 1000);
      }
      setInterval(createBTC, 200);
    })();
    </script>
    """
    st.markdown(html, unsafe_allow_html=True)

# =====================================================
# API FETCH + CACHE (con gestione errori)
# =====================================================
@st.cache_data(ttl=60)
def get_btc_price():
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids":"bitcoin","vs_currencies":"usd"},
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
        return None

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
        data = r.json()["data"][0]
        return {
            "value": int(data["value"]),
            "classification": data["value_classification"],
            "timestamp": datetime.datetime.fromtimestamp(int(data["timestamp"]))
        }
    except Exception:
        return None

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

# =====================================================
# MODELLI TEORICI DEL PREZZO BTC
# =====================================================
def price_theoretical_s2f(supply, block_reward=6.25, blocks_per_year=52560, a=0.4, b=3.3):
    flow = block_reward * blocks_per_year
    sf = supply / flow if flow else 0
    return a * (sf ** b)

def price_theoretical_ratio(price, supply, lost=4_000_000):
    if supply and supply > lost:
        return price * supply / (supply - lost)
    return None

def price_theoretical_metcalfe(active_addresses, c=1e-7):
    if active_addresses:
        return c * (active_addresses ** 2)
    return None

def price_theoretical_nvt(market_cap, on_chain_volume):
    if on_chain_volume:
        nvt = market_cap / on_chain_volume
        return market_cap / nvt if nvt else None
    return None

# =====================================================
# RENDERING
# =====================================================
def format_countdown(dt):
    now = datetime.datetime.now()
    diff = dt - now
    if diff.total_seconds() <= 0:
        return "Terminato"
    days = diff.days
    hours, rem = divmod(diff.seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{days}g {hours}h {minutes}m {secs}s"

# Manteniamo funzioni di rendering originali per metriche di rete, mempool, ecc.
def render_metrics(em, price):
    total = 21_000_000
    lost = 4_000_000
    liquid = em - lost if em else None
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Supply Massima",    f"{total:,} BTC")
        st.metric("Supply Emessa",     f"{em:,} BTC" if em else "N/A")
        st.metric("Supply Liquida",    f"{liquid:,} BTC" if liquid else "N/A")
        st.metric("BTC Persi (lost)",  f"{lost:,} BTC")
    with col2:
        st.metric("Prezzo BTC (reale)", f"${price:,.2f}" if price else "N/A")

# Sezione separata per prezzi teorici
def render_theoretical(price, em, active, volume):
    market_cap = price * em if price and em else None
    theo_ratio = price_theoretical_ratio(price, em)
    theo_s2f   = price_theoretical_s2f(em) if em else None
    theo_met   = price_theoretical_metcalfe(active)
    theo_nvt   = price_theoretical_nvt(market_cap, volume)

    st.header("Prezzo Teorico vs Reale")
    cols = st.columns(5)
    labels = ["Reale", "Ratio‑Basic", "Stock-to-Flow", "Metcalfe", "NVT"]
    values = [price, theo_ratio, theo_s2f, theo_met, theo_nvt]
    for col, label, val in zip(cols, labels, values):
        disp = f"${val:,.2f}" if isinstance(val, (int, float)) else "N/A"
        col.metric(label, disp)

# Restanti funzioni di rendering (network, mempool, decentralizzazione, news, charts, tradingview)
# (Invariate rispetto allo script originale)

def main():
    add_background_rain()
    st.title("BITCOUNTER – Real Bitcoin Liquidity Dashboard")

    price_data = get_btc_price()
    bc = get_blockchain_data()
    price   = price_data if price_data else None
    emitted = bc.get('btc_emitted')

    if price is None or emitted is None:
        st.error("Errore recupero dati BTC.")
        return

    # ================================
    # Sezione Prezzo Reale + Teorico
    # ================================
    render_metrics(emitted, price)

    active = None
    volume = None
    try:
        active = requests.get(
            "https://api.blockchain.info/charts/addresses-active?timespan=1days&rollingAverage=8hours&format=json",
            timeout=5
        ).json()["values"][-1]["y"]
    except:
        pass
    try:
        volume = float(requests.get("https://api.blockchain.info/q/24hrbtcsent", timeout=5).text)
    except:
        pass

    render_theoretical(price, emitted, active, volume)

    # ================================
    # Sezioni restanti
    # ================================
    st.header("Statistiche di Rete")
    diff = get_network_difficulty()
    hashrate = get_network_hashrate()
    height = get_block_height()
    # ... chiama render_network() e le altre funzioni come prima ...

if __name__ == "__main__":
    main()


