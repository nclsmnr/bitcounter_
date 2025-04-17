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
        return [{
            "title": i.find("title").text,
            "link":  i.find("link").text,
            "pubDate": i.find("pubDate").text
        } for i in items]
    except Exception:
        return []

# =====================================================
# DATI AGGIUNTIVI PER MODELLI TEORICI
# =====================================================
@st.cache_data(ttl=300)
def get_active_addresses():
    try:
        r = requests.get(
            "https://api.blockchain.info/charts/addresses-active?timespan=1days&rollingAverage=8hours&format=json",
            timeout=5
        )
        r.raise_for_status()
        return r.json()["values"][-1]["y"]
    except Exception:
        return None

@st.cache_data(ttl=300)
def get_onchain_volume():
    try:
        r = requests.get("https://api.blockchain.info/q/24hrbtcsent", timeout=5)
        r.raise_for_status()
        return float(r.text)
    except Exception:
        return None

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

# Sezione metriche reali
def render_metrics(em, price):
    total = 21_000_000
    lost = 4_000_000
    liquid = em - lost if em else None
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Supply Massima", f"{total:,} BTC")
        st.metric("Supply Emessa",  f"{em:,} BTC" if em else "N/A")
        st.metric("Supply Liquida", f"{liquid:,} BTC" if liquid else "N/A")
        st.metric("BTC Persi",      f"{lost:,} BTC")
    with col2:
        st.metric("Prezzo Attuale BTC", f"${price:,.2f}" if price else "N/A")

# Sezione prezzi teorici
def render_theoretical(price, em, active, volume):
    market_cap = price * em if price and em else None
    theo_ratio = price_theoretical_ratio(price, em)
    theo_s2f   = price_theoretical_s2f(em) if em else None
    theo_met   = price_theoretical_metcalfe(active)
    theo_nvt   = price_theoretical_nvt(market_cap, volume)

    st.header("Prezzo Teorico vs Reale")
    cols = st.columns(5)
    labels = ["Reale", "Ratio-Basic", "Stock-to-Flow", "Metcalfe", "NVT"]
    values = [price, theo_ratio, theo_s2f, theo_met, theo_nvt]
    for col, label, val in zip(cols, labels, values):
        disp = f"${val:,.2f}" if isinstance(val, (int, float)) else "N/A"
        col.metric(label, disp)

# Sezione network
def render_network():
    diff = get_network_difficulty()
    hashrate = get_network_hashrate()
    height = get_block_height()
    next_halving = ((height // 210000) + 1) * 210000 if height else None
    blocks_remaining = next_halving - height if height else None
    halving_time = (datetime.datetime.now() + datetime.timedelta(seconds=blocks_remaining * 10 * 60)) if blocks_remaining else None
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Difficoltà", f"{diff:.2f}" if diff else "N/A")
        st.metric("Hashrate", f"{hashrate/1e9:.2f} GH/s" if hashrate else "N/A")
    with c2:
        st.metric("Block Height", f"{height}" if height else "N/A")
        st.metric("Tempo Medio Blocco", "10 min (target)")
    with c3:
        st.metric("Prox. Halving", f"{next_halving}" if next_halving else "N/A")
        st.metric("Countdown Halving", format_countdown(halving_time) if halving_time else "N/A")

# Sezione mempool
def render_mempool():
    mp = get_mempool_data() or {}
    count = mp.get("count")
    vsize = mp.get("vsize")
    total_fee = mp.get("total_fee")
    avg_fee = (total_fee/count) if count else None
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Tx in Mempool", count or "N/A")
    with c2:
        st.metric("Dimensione Mempool", f"{vsize} vbytes" if vsize else "N/A")
    with c3:
        st.metric("Fee Media", f"{avg_fee:.2f} sat" if avg_fee else "N/A")

# Sezione decentralizzazione
def render_decentralization():
    nodes = get_node_stats()
    st.metric("Nodi Attivi", nodes or "N/A")

# Sezione sentiment & news
def render_sentiment_and_news():
    fg = get_fear_greed_index()
    if fg:
        st.metric("Fear & Greed Index", f"{fg['value']} ({fg['classification']})",
                  delta=fg['timestamp'].strftime("%Y-%m-%d %H:%M"))
    st.markdown("**Ultime Notizie su Bitcoin**")
    for item in get_btc_news():
        st.markdown(f"- [{item['title']}]({item['link']})  _{item['pubDate']}_")

# Sezione chart
def render_charts(em, price, theo_vals=None):
    circ = em
    lost = 4_000_000
    dormant = 1_500_000
    liquid = circ - lost if circ else None
    # Pie chart
    fig1, ax1 = plt.subplots(figsize=(5,4))
    labels_pie = ["Liquidi non dormienti", "Dormienti", "Persi"]
    vals_pie   = [liquid - dormant if liquid else 0, dormant, lost]
    ax1.pie(vals_pie, labels=labels_pie, autopct="%1.1f%%", startangle=90)
    ax1.axis('equal')
    st.pyplot(fig1)

    # Bar chart teorici
    if theo_vals:
        fig2, ax2 = plt.subplots(figsize=(6,4))
        labels, vals = zip(*theo_vals.items())
        ax2.bar(labels, vals)
        ax2.set_ylabel("USD")
        st.pyplot(fig2)

# Sezione TradingView
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

# =====================================================
# MAIN
# =====================================================
def main():
    add_background_rain()
    st.title("BITCOUNTER – Real Bitcoin Liquidity Dashboard")

    price = get_btc_price()
    bc = get_blockchain_data()
    emitted = bc.get('btc_emitted')

    if price is None or emitted is None:
        st.error("Errore recupero dati BTC.")
        return

    # Prezzo reale
    render_metrics(emitted, price)

    # Dati aggiuntivi per modelli teorici
    active = get_active_addresses()
    volume = get_onchain_volume()
    market_cap = price * emitted if price and emitted else None

    # Calcola valori teorici in dict
    theo_vals = {
        "Reale": price,
        "Ratio-Basic": price_theoretical_ratio(price, emitted) or 0,
        "S2F": price_theoretical_s2f(emitted),
        "Metcalfe": price_theoretical_metcalfe(active) or 0,
        "NVT": price_theoretical_nvt(market_cap, volume) or 0
    }

    # Prezzi teorici
    render_theoretical(price, emitted, active, volume)

    # Altre sezioni
    st.header("Statistiche di Rete")
    render_network()

    st.header("Transazioni & Mempool")
    render_mempool()

    st.header("Decentralizzazione")
    render_decentralization()

    st.header("Sentiment & News")
    render_sentiment_and_news()

    st.header("Grafici Matplotlib")
    render_charts(emitted, price, theo_vals)

    st.header("Grafico a Candele TradingView")
    render_tradingview()

if __name__ == "__main__":
    main()
