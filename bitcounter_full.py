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
# DATI AGGIUNTIVI PER MODELLI TEORICI
# =====================================================
@st.cache_data(ttl=300)
def get_active_addresses():
    r = requests.get(
        "https://api.blockchain.info/charts/addresses-active?timespan=1days&rollingAverage=8hours&format=json",
        timeout=5
    )
    r.raise_for_status()
    data = r.json()
    return data["values"][-1]["y"]

@st.cache_data(ttl=300)
def get_onchain_volume():
    r = requests.get("https://api.blockchain.info/q/24hrbtcsent", timeout=5)
    r.raise_for_status()
    return float(r.text)

# =====================================================
# MODELLI TEORICI DEL PREZZO BTC
# =====================================================
def price_theoretical_s2f(supply: float,
                          block_reward: float = 6.25,
                          blocks_per_year: int = 52560,
                          a: float = 0.4,
                          b: float = 3.3) -> float:
    """
    Stock-to-Flow model:
      flow = block_reward * blocks_per_year
      sf = supply / flow
      P_teorico = a * sf^b
    """
    flow = block_reward * blocks_per_year
    sf = supply / flow
    return a * (sf ** b)

def price_theoretical_metcalfe(active_addresses: float,
                               c: float = 1e-7) -> float:
    """
    Metcalfe's Law:
      P_teorico = c * (N_active)^2
    """
    return c * (active_addresses ** 2)

def price_theoretical_nvt(market_cap: float,
                          on_chain_volume: float) -> float:
    """
    NVT Ratio model:
      nvt = market_cap / on_chain_volume
      P_teorico = market_cap / nvt
    """
    if on_chain_volume == 0:
        return 0.0
    nvt = market_cap / on_chain_volume
    return market_cap / nvt if nvt else 0.0

# =====================================================
# CALCOLI & STIME / RENDER
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

def render_metrics(em, price,
                   theo_ratio, theo_s2f, theo_met, theo_nvt):
    total = 21_000_000
    lost = 4_000_000
    liquid = em - lost
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Supply Massima",    f"{total:,} BTC")
        st.metric("Supply Emessa",     f"{em:,} BTC")
        st.metric("Supply Liquida",    f"{liquid:,} BTC")
        st.metric("BTC Persi (lost)",  f"{lost:,} BTC")
    with col2:
        st.metric("Prezzo Attuale",       f"${price:,.2f}")
        st.metric("Prezzo Ratio-Basic",   f"${theo_ratio:,.2f}")
        st.metric("Prezzo Stock-to-Flow", f"${theo_s2f:,.2f}")
        st.metric("Prezzo Metcalfe",      f"${theo_met:,.2f}")
        st.metric("Prezzo NVT",           f"${theo_nvt:,.2f}")

def render_network():
    diff = get_network_difficulty()
    hashrate = get_network_hashrate() / 1e9
    height = get_block_height()
    next_halving = ((height // 210000) + 1) * 210000
    blocks_remaining = next_halving - height
    halving_time = datetime.datetime.now() + datetime.timedelta(seconds=blocks_remaining * 10 * 60)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Difficoltà",          f"{diff:.2f}")
        st.metric("Hashrate",            f"{hashrate:.2f} GH/s")
    with c2:
        st.metric("Block Height",        f"{height}")
        st.metric("Tempo Medio Blocco",  "10 min (target)")
    with c3:
        st.metric("Prox. Halving",       f"{next_halving}")
        st.metric("Countdown Halving",   format_countdown(halving_time))

def render_mempool():
    mp = get_mempool_data()
    count = mp.get("count")
    vsize = mp.get("vsize")
    total_fee = mp.get("total_fee")
    avg_fee = total_fee / count if count else None
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Tx in Mempool",       count or "N/A")
    with c2:
        st.metric("Dim. Mempool",        f"{vsize} vbytes" if vsize else "N/A")
    with c3:
        st.metric("Fee Media",           f"{avg_fee:.2f} sat" if avg_fee else "N/A")

def render_decentralization():
    nodes = get_node_stats()
    st.metric("Nodi Attivi",            nodes or "N/A")

def render_sentiment_and_news():
    fg = get_fear_greed_index()
    st.metric(
        "Fear & Greed Index",
        f"{fg['value']} ({fg['classification']})",
        delta=fg['timestamp'].strftime("%Y-%m-%d %H:%M")
    )
    st.markdown("**Ultime Notizie su Bitcoin**")
    for item in get_btc_news():
        st.markdown(f"- [{item['title']}]({item['link']})  \n  _{item['pubDate']}_")

def render_charts(em, price,
                  theo_ratio, theo_s2f, theo_met, theo_nvt):
    circ = em
    lost = 4_000_000
    dormant = 1_500_000
    liquid = circ - lost
    real = price
    labels = ["Attuale", "Ratio", "S2F", "Metcalfe", "NVT"]
    vals   = [real, theo_ratio, theo_s2f, theo_met, theo_nvt]
    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots(figsize=(5,4))
        pie_labels = ["Liquidi dormienti", "Dormienti", "Persi"]
        pie_vals   = [liquid - dormant, dormant, lost]
        ax.pie(pie_vals, labels=pie_labels, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")
        st.pyplot(fig)
    with c2:
        fig, ax = plt.subplots(figsize=(6,4))
        ax.bar(labels, vals)
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
        "toolbar_bg":"#f1f3f6",
        "hide_side_toolbar":false,
        "withdateranges":true,
        "allow_symbol_change":true,
        "details":true,
        "container_id":"tradingview_btc"
      });
      </script>
    </div>
    <!-- TradingView Widget END -->
    """
    components.html(widget, height=520)

def main():
    add_background_rain()
    st.title("BITCOUNTER – Real Bitcoin Liquidity Dashboard")

    price = get_btc_price()
    bc = get_blockchain_data()
    if price is None or bc['btc_emitted'] is None:
        st.error("Errore recupero dati.")
        return
    emitted = bc['btc_emitted']

    # ================================
    # NUOVI DATI PER MODELLI TEORICI
    active     = get_active_addresses()
    volume     = get_onchain_volume()
    market_cap = price * emitted

    # Calcoli teorici
    lost        = 4_000_000
    theo_ratio  = price * emitted / (emitted - lost)
    theo_s2f    = price_theoretical_s2f(emitted)
    theo_met    = price_theoretical_metcalfe(active)
    theo_nvt    = price_theoretical_nvt(market_cap, volume)

    st.header("Calcoli e Stime")
    render_metrics(emitted, price, theo_ratio, theo_s2f, theo_met, theo_nvt)

    st.header("Statistiche di Rete")
    render_network()

    st.header("Transazioni & Mempool")
    render_mempool()

    st.header("Decentralizzazione")
    render_decentralization()

    st.header("Sentiment & News")
    render_sentiment_and_news()

    st.header("Grafici Matplotlib")
    render_charts(emitted, price, theo_ratio, theo_s2f, theo_met, theo_nvt)

    st.header("Grafico a Candele TradingView")
    render_tradingview()

if __name__ == "__main__":
    main()
