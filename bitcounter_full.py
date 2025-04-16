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
    page_title="BITCOUNTER", 
    layout="wide", 
    initial_sidebar_state="expanded"
)
REFRESH_INTERVAL = 60  # auto-refresh ogni 60s

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
    </style>
    <div id="btc-container" style="position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:-1;"></div>
    <script>
    (function(){
      var c = document.getElementById('btc-container');
      function createBTC(){
        var d = document.createElement('div');
        d.className='btc';
        d.innerHTML='₿';
        d.style.left = Math.random()*100+'%';
        var t = 5 + Math.random()*10;
        d.style.animationDuration = t + 's';
        d.style.animationDelay = Math.random()*t + 's';
        c.appendChild(d);
        setTimeout(()=>d.remove(), t*1000);
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

@st.cache_data(ttl=60)
def get_blockchain_data():
    r = requests.get("https://api.blockchain.info/q/totalbc", timeout=5)
    r.raise_for_status()
    return {"btc_emitted": int(r.text)/1e8}

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
    d = r.json()["data"][0]
    return {
        "value": int(d["value"]),
        "classification": d["value_classification"],
        "timestamp": datetime.datetime.fromtimestamp(int(d["timestamp"]))
    }

@st.cache_data(ttl=300)
def get_btc_news(count=5):
    rss = "https://news.google.com/rss/search?q=bitcoin&hl=en-US&gl=US&ceid=US:en"
    r = requests.get(rss, timeout=5)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    items = root.findall(".//item")[:count]
    news = []
    for it in items:
        news.append({
            "title": it.find("title").text,
            "link": it.find("link").text,
            "pubDate": it.find("pubDate").text
        })
    return news

# =====================================================
# CALCOLI & STIME
# =====================================================
def estimate_real_supply(em, lost=4_000_000, dormant=1_500_000):
    circ = em
    liq  = circ - lost
    return {"total":21_000_000,"circulating":circ,"liquid":liq,"lost":lost,"dormant":dormant}

def estimate_remaining_btc(em):
    return 21_000_000 - em

def estimate_mining_countdown(em):
    reward = 6.25
    blocks = estimate_remaining_btc(em) / reward
    secs   = blocks * 10 * 60
    return datetime.datetime.now() + datetime.timedelta(seconds=secs)

def format_countdown(dt):
    now  = datetime.datetime.now()
    diff = dt - now
    if diff.total_seconds() <= 0:
        return "Terminato"
    days = diff.days
    hours, rem    = divmod(diff.seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{days}g {hours}h {minutes}m {secs}s"

# =====================================================
# RENDER SEZIONI
# =====================================================
def render_metrics(em, price):
    sup = estimate_real_supply(em)
    end = estimate_mining_countdown(em)
    l, r = st.columns(2)
    with l:
        st.metric("Supply Massima", f"{sup['total']:,} BTC")
        st.metric("Supply Emessa", f"{sup['circulating']:,} BTC")
        st.metric("Supply Liquida", f"{sup['liquid']:,} BTC")
        st.metric("BTC Persi", f"{sup['lost']:,} BTC")
        st.metric("Prezzo BTC", f"${price:,.2f}")
    with r:
        st.metric("BTC da Minare", f"{estimate_remaining_btc(em):,.2f} BTC")
        st.metric("Countdown Mining", format_countdown(end))

def render_network():
    diff   = get_network_difficulty()
    hr     = get_network_hashrate() / 1e9
    height = get_block_height()
    next_h = ((height // 210000) + 1) * 210000
    rem    = next_h - height
    dt_h   = datetime.datetime.now() + datetime.timedelta(seconds=rem * 10 * 60)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Difficoltà", f"{diff:.2f}")
        st.metric("Hashrate", f"{hr:.2f} GH/s")
    with c2:
        st.metric("Block Height", f"{height}")
        st.metric("Tempo Medio Blocco", "10 min (target)")
    with c3:
        st.metric("Prox. Halving", f"{next_h}")
        st.metric("Countdown Halving", format_countdown(dt_h))

def render_mempool():
    mp  = get_mempool_data()
    cnt = mp.get("count")
    vsz = mp.get("vsize")
    fee = mp.get("total_fee")
    avg = fee / cnt if cnt else None
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Tx in Mempool", cnt or "N/A")
    with c2:
        st.metric("Dim. Mempool", f"{vsz} vbytes" if vsz else "N/A")
    with c3:
        st.metric("Fee Media", f"{avg:.2f} sat" if avg else "N/A")

def render_decentralization():
    nodes = get_node_stats()
    st.metric("Nodi Attivi", nodes or "N/A")

def render_sentiment_and_news():
    fg = get_fear_greed_index()
    st.metric(
        "Fear & Greed Index",
        f"{fg['value']} ({fg['classification']})",
        delta=fg["timestamp"].strftime("%Y-%m-%d %H:%M")
    )
    st.markdown("**Ultime Notizie su Bitcoin**")
    for ni in get_btc_news():
        st.markdown(f"- [{ni['title']}]({ni['link']})  \n  _{ni['pubDate']}_")

def render_charts(em, price):
    sup   = estimate_real_supply(em)
    real  = price
    theo  = price * sup["circulating"] / sup["liquid"]
    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots(figsize=(5, 4))
        labels = ["Liquidi", "Dormienti", "Persi"]
        vals   = [sup["liquid"] - sup["dormant"], sup["dormant"], sup["lost"]]
        ax.pie(vals, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")
        st.pyplot(fig)
    with c2:
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.bar(["Attuale", "Teorico"], [real, theo], color=["blue", "orange"])
        ax.set_ylabel("USD")
        ax.set_title("Prezzo BTC")
        st.pyplot(fig)

def render_tradingview():
    widget = """
    <!-- TradingView Widget BEGIN -->
    <div class="tradingview-widget-container">
      <div id="tradingview_btc"></div>
      <script src="https://s3.tradingview.com/tv.js"></script>
      <script>
      new TradingView.widget({
        "width":"100%",
        "height":500,
        "symbol":"COINBASE:BTCUSD",
        "interval":"60",
        "timezone":"Etc/UTC",
        "theme":"light",
        "style":"1",
        "locale":"it",
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
    st.markdown(f"<meta http-equiv='refresh' content='{REFRESH_INTERVAL}'>", unsafe_allow_html=True)

    st.title("BITCOUNTER – Real Bitcoin Liquidity Dashboard")
    st.info(f"Aggiornamento ogni {REFRESH_INTERVAL} s")

    price = get_btc_price()
    bc    = get_blockchain_data()
    if price is None or bc["btc_emitted"] is None:
        st.error("Errore recupero dati.")
        return
    emitted = bc["btc_emitted"]

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







