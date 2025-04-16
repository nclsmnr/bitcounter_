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
# FUNZIONI API
# =====================================================
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

# =====================================================
# CALCOLI & STIME
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

# =====================================================
# FUNZIONI DI RENDER
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

def render_network():
    st.info("Funzione di rete placeholder")

def render_mempool():
    st.info("Funzione mempool placeholder")

def render_decentralization():
    st.info("Funzione decentralizzazione placeholder")

def render_sentiment_and_news():
    st.info("Funzione sentiment/news placeholder")

def render_charts(em, price):
    st.info("Funzione grafici matplotlib placeholder")

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
    if price is None or bc['btc_emitted'] is None:
        st.error("Errore recupero dati.")
        return
    emitted = bc['btc_emitted']

    with st.expander("Calcoli e Stime", expanded=False):
        render_metrics(emitted, price)

    with st.expander("Statistiche di Rete", expanded=False):
        render_network()

    with st.expander("Transazioni & Mempool", expanded=False):
        render_mempool()

    with st.expander("Decentralizzazione", expanded=False):
        render_decentralization()

    with st.expander("Sentiment & News", expanded=False):
        render_sentiment_and_news()

    with st.expander("Grafici Matplotlib", expanded=False):
        render_charts(emitted, price)

    with st.expander("Grafico a Candele TradingView", expanded=False):
        render_tradingview()

if __name__ == "__main__":
    main()





































































