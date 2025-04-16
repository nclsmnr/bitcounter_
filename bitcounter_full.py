import streamlit as st
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
REFRESH_INTERVAL = 60  # Aggiornamento automatico ogni 60 secondi

# =====================================================
# EFFETTO DI PIOGGIA DI BTC IN BACKGROUND
# =====================================================
def add_background_rain():
    html_code = """
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
    <div id="btc-container" style="position: fixed; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:-1;"></div>
    <script>
      (function() {
          var container = document.getElementById('btc-container');
          function createBTC() {
              var btc = document.createElement('div');
              btc.className = 'btc';
              btc.innerHTML = '₿';
              btc.style.left = Math.random() * 100 + '%';
              var duration = 5 + Math.random() * 10;
              btc.style.animationDuration = duration + 's';
              btc.style.animationDelay = (Math.random() * duration) + 's';
              container.appendChild(btc);
              setTimeout(function() { btc.remove(); }, duration * 1000);
          }
          setInterval(createBTC, 200);
      })();
    </script>
    """
    st.markdown(html_code, unsafe_allow_html=True)

# =====================================================
# API DATA FETCH (CACHE TTL)
# =====================================================
@st.cache_data(ttl=60)
def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin", "vs_currencies": "usd"}
    r = requests.get(url, params=params, timeout=5)
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
        title = item.find("title").text
        link  = item.find("link").text
        pubDate = item.find("pubDate").text
        news.append({"title": title, "link": link, "pubDate": pubDate})
    return news

# =====================================================
# CALCOLI E STIME
# =====================================================
def estimate_real_supply(emitted, lost=4_000_000, dormant=1_500_000):
    circ   = emitted
    liq    = circ - lost
    return {
        "total": 21_000_000,
        "circulating": circ,
        "liquid": liq,
        "lost": lost,
        "dormant": dormant
    }

def estimate_remaining_btc(emitted):
    return 21_000_000 - emitted

def estimate_mining_countdown(emitted):
    reward = 6.25
    blocks = estimate_remaining_btc(emitted) / reward
    secs   = blocks * 10 * 60
    return datetime.datetime.now() + datetime.timedelta(seconds=secs)

def format_countdown(dt):
    diff = dt - datetime.datetime.now()
    if diff.total_seconds() <= 0:
        return "Term. halving/mining"
    d,h,r = diff.days, *divmod(diff.seconds,3600)
    m,s   = divmod(r,60)
    return f"{d}g {h}h {m}m {s}s"

# =====================================================
# RENDERING SEZIONI
# =====================================================
def render_metrics(emitted, price):
    supply = estimate_real_supply(emitted)
    end_mining = estimate_mining_countdown(emitted)
    left, right = st.columns(2)
    with left:
        st.metric("Supply Massima", f"{supply['total']:,} BTC")
        st.metric("Supply Emessa", f"{supply['circulating']:,} BTC")
        st.metric("Supply Liquida", f"{supply['liquid']:,} BTC")
        st.metric("BTC Persi", f"{supply['lost']:,} BTC")
        st.metric("Prezzo BTC", f"${price:,.2f}")
    with right:
        st.metric("BTC da Minare", f"{estimate_remaining_btc(emitted):,.2f} BTC")
        st.metric("Countdown Fine Mining", format_countdown(end_mining))

def render_network():
    diff   = get_network_difficulty()
    hr     = get_network_hashrate()
    height = get_block_height()
    # prossimo halving
    next_h = ((height//210000)+1)*210000
    to_h   = next_h - height
    dt_h   = datetime.datetime.now() + datetime.timedelta(seconds=to_h*10*60)
    left, mid, right = st.columns(3)
    with left:
        st.metric("Difficoltà", f"{diff:.2f}")
        st.metric("Hashrate", f"{hr/1e9:.2f} GH/s")
    with mid:
        st.metric("Block Height", f"{height}")
        st.metric("Tempo Medio Blocco", "10 min (target)")
    with right:
        st.metric("Prox. Halving", f"{next_h}")
        st.metric("Countdown Halving", format_countdown(dt_h))

def render_mempool():
    mp = get_mempool_data()
    count = mp.get("count")
    vsize = mp.get("vsize")
    fee   = mp.get("total_fee")
    avg_fee = fee/count if count else None
    c1,c2,c3 = st.columns(3)
    with c1: st.metric("Tx in Mempool", count or "N/A")
    with c2: st.metric("Dimensione Mempool", f"{vsize} vbytes" if vsize else "N/A")
    with c3: st.metric("Fee Media", f"{avg_fee:.2f} sat" if avg_fee else "N/A")

def render_decentralization():
    nodes = get_node_stats()
    st.metric("Nodi Attivi", nodes or "N/A")

def render_sentiment_and_news():
    fg = get_fear_greed_index()
    st.metric(
        "Fear & Greed Index",
        f"{fg['value']} ({fg['classification']})",
        delta=str(fg['timestamp'].strftime("%Y-%m-%d %H:%M"))
    )
    st.markdown("**Ultime Notizie su Bitcoin**")
    for item in get_btc_news():
        st.markdown(f"- [{item['title']}]({item['link']})  \n  _{item['pubDate']}_")

def render_charts(emitted, price):
    supply = estimate_real_supply(emitted)
    real, theo = price, price * supply["circulating"] / supply["liquid"]
    c1,c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots(figsize=(5,4))
        labels = ["Liquidi","Dormienti","Persi"]
        vals = [supply["liquid"]-supply["dormant"], supply["dormant"], supply["lost"]]
        ax.pie(vals, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")
        st.pyplot(fig)
    with c2:
        fig, ax = plt.subplots(figsize=(5,4))
        ax.bar(["Attuale","Teorico"], [real, theo], color=["blue","orange"])
        ax.set_ylabel("USD")
        ax.set_title("Prezzo BTC")
        st.pyplot(fig)

# =====================================================
# MAIN
# =====================================================
def main():
    add_background_rain()
    st.markdown(f"<meta http-equiv='refresh' content='{REFRESH_INTERVAL}'>", unsafe_allow_html=True)

    st.title("BITCOUNTER – Real Bitcoin Liquidity Dashboard")
    st.info(f"Aggiornamento ogni {REFRESH_INTERVAL} s")

    # dati base
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

    st.header("Grafici")
    render_charts(emitted, price)

if __name__ == "__main__":
    main()





