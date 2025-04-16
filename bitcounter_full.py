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
    <div id=\"btc-container\" style=\"position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:-1;\"></div>
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

# =====================================================
# ALTRI DATI STATICI
# =====================================================
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

# =====================================================
# CALCOLI & STIME / RENDER (omessi per brevità)
# =====================================================
def render_metrics(em, price):
    circ = em
    lost = 4_000_000
    dormant = 1_500_000
    liquid = circ - lost
    total = 21_000_000
    remaining = total - circ
    end_time = datetime.datetime.now() + datetime.timedelta(seconds=(remaining / 6.25) * 600)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Supply Massima", f"{total:,} BTC")
        st.metric("Supply Emessa", f"{circ:,} BTC")
        st.metric("Supply Liquida", f"{liquid:,} BTC")
        st.metric("BTC Persi", f"{lost:,} BTC")
        st.markdown(f"<span style='font-size: 1.1rem; font-weight: bold;'>Prezzo BTC:</span> ${price:,.2f} <span class='live-indicator'></span>", unsafe_allow_html=True)
    with col2:
        st.metric("BTC da Minare", f"{remaining:,.2f} BTC")
        st.metric("Countdown Mining", format_countdown(end_time))

# =====================================================
# MAIN
# =====================================================
def main():
    add_background_rain()

    st.title("BITCOUNTER – Real Bitcoin Liquidity Dashboard")

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












