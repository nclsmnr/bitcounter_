import streamlit as st
import streamlit.components.v1 as components
import requests
import matplotlib.pyplot as plt
import datetime
import xml.etree.ElementTree as ET

# =====================================================
# CONFIGURAZIONE STREAMLIT
# =====================================================
st.set_page_config(
    page_title="BITCOUNTER – Real Bitcoin Liquidity Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# COSTANTI DI REFRESH
# =====================================================
REFRESH_INTERVAL = 60  # in secondi
REFRESH_MS = REFRESH_INTERVAL * 1000  # in millisecondi per JS

# =====================================================
# HTML + JS: METRICHE DINAMICHE + PIOGGIA DI ₿
# =====================================================
metrics_and_rain = f"""
<style>
  @keyframes fall {{
    0% {{ transform: translateY(-100%); opacity: 0 }}
    10% {{ opacity: 1 }}
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
  .metrics-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    background: rgba(0,0,0,0.05);
    padding: 1rem;
    border-radius: 8px;
  }}
</style>

<div id="btc-container" style="position:fixed; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:-1;"></div>

<script>
// Pioggia di ₿
setInterval(() => {{
  const c = document.getElementById("btc-container");
  const d = document.createElement("div");
  d.className = "btc";
  d.innerText = "₿";
  d.style.left = Math.random() * 100 + "%";
  const t = 5 + Math.random() * 10;
  d.style.animationDuration = t + "s";
  d.style.animationDelay = Math.random() * t + "s";
  c.appendChild(d);
  setTimeout(() => d.remove(), t * 1000);
}}, 200);

// Fetch metriche ogni {REFRESH_MS} ms
async function updateMetrics() {{
  try {{
    // Prezzo BTC USD
    let p = await fetch("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd");
    p = (await p.json()).bitcoin.usd;
    document.getElementById("m_price").innerText = p.toLocaleString() + " USD";

    // Supply emessa
    let e = await fetch("https://api.blockchain.info/q/totalbc");
    e = parseInt(await e.text()) / 1e8;
    document.getElementById("m_emitted").innerText = e.toLocaleString() + " BTC";
    document.getElementById("m_remaining").innerText = (21000000 - e).toLocaleString() + " BTC";

    // Difficoltà
    let d = await fetch("https://blockchain.info/q/getdifficulty");
    d = parseFloat(await d.text());
    document.getElementById("m_diff").innerText = d.toFixed(2);

    // Hashrate
    let h = await fetch("https://blockchain.info/q/hashrate");
    h = parseFloat(await h.text()) / 1e9;
    document.getElementById("m_hash").innerText = h.toFixed(2) + " GH/s";

    // Block height
    let bh = await fetch("https://blockchain.info/q/getblockcount");
    bh = parseInt(await bh.text());
    document.getElementById("m_height").innerText = bh;

    // Mempool
    let m = await fetch("https://mempool.space/api/mempool");
    m = await m.json();
    document.getElementById("m_mempool_count").innerText = m.count;
    document.getElementById("m_mempool_fee").innerText = (m.total_fee / m.count).toFixed(0) + " sat";

    // Fear & Greed Index
    let fg = await fetch("https://api.alternative.me/fng/?limit=1&format=json");
    fg = (await fg.json()).data[0];
    document.getElementById("m_fng").innerText = fg.value + " (" + fg.value_classification + ")";
  }} catch (e) {{
    console.error("Errore fetch metriche:", e);
  }}
}}

updateMetrics();
setInterval(updateMetrics, {REFRESH_MS});
</script>

<div class="metrics-grid">
  <div><strong>Prezzo BTC:</strong> <span id="m_price">…</span></div>
  <div><strong>Supply Emessa:</strong> <span id="m_emitted">…</span></div>
  <div><strong>BTC da Minare:</strong> <span id="m_remaining">…</span></div>
  <div><strong>Difficoltà:</strong> <span id="m_diff">…</span></div>
  <div><strong>Hash Rate:</strong> <span id="m_hash">…</span></div>
  <div><strong>Block Height:</strong> <span id="m_height">…</span></div>
  <div><strong>Tx in Mempool:</strong> <span id="m_mempool_count">…</span></div>
  <div><strong>Fee Media:</strong> <span id="m_mempool_fee">…</span></div>
  <div><strong>Fear & Greed:</strong> <span id="m_fng">…</span></div>
</div>
"""

# =====================================================
# WIDGET CANDLESTICK TRADINGVIEW
# =====================================================
tradingview_html = """
<!-- TradingView Widget BEGIN -->
<div class="tradingview-widget-container">
  <div id="tradingview_btc"></div>
  <script src="https://s3.tradingview.com/tv.js"></script>
  <script>
    new TradingView.widget({
      "width": "100%",
      "height": 600,
      "symbol": "COINBASE:BTCUSD",
      "interval": "60",
      "timezone": "Etc/UTC",
      "theme": "light",
      "style": "1",
      "locale": "it",
      "toolbar_bg": "#f1f3f6",
      "withdateranges": true,
      "allow_symbol_change": true,
      "details": true,
      "container_id": "tradingview_btc"
    });
  </script>
</div>
<!-- TradingView Widget END -->
"""

# =====================================================
# FUNZIONE PYTHON: ULTIME NOTIZIE
# =====================================================
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
# FUNZIONE PYTHON: GRAFICI MATPLOTLIB
# =====================================================
def estimate_real_supply(em, lost=4_000_000, dormant=1_500_000):
    circ = em
    liq = circ - lost
    return {"total":21_000_000, "circulating":circ, "liquid":liq, "lost":lost, "dormant":dormant}


def render_charts(em, price):
    sup = estimate_real_supply(em)
    real = price
    theo = price * sup["circulating"] / sup["liquid"]
    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots(figsize=(5,4))
        labels = ["Liquidi", "Dormienti", "Persi"]
        vals = [sup["liquid"] - sup["dormant"], sup["dormant"], sup["lost"]]
        ax.pie(vals, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")
        st.subheader("Supply Effettiva")
        st.pyplot(fig)
    with col2:
        fig, ax = plt.subplots(figsize=(5,4))
        ax.bar(["Attuale", "Teorico"], [real, theo], color=["blue","orange"])
        ax.set_ylabel("USD")
        ax.set_title("Prezzo BTC vs Teorico")
        st.subheader("Prezzo Reale vs Teorico")
        st.pyplot(fig)

# =====================================================
# MAIN
# =====================================================
def main():
    st.title("BITCOUNTER – Real Bitcoin Liquidity Dashboard")

    # Inietta HTML/JS per metriche live + pioggia di ₿
    components.html(metrics_and_rain, height=350, scrolling=False)

    # TradingView candlestick widget
    components.html(tradingview_html, height=630)

    # Sezione: Ultime Notizie
    st.header("Ultime Notizie su Bitcoin")
    for item in get_btc_news():
        st.markdown(f"- [{item['title']}]({item['link']})  \n  _{item['pubDate']}_")

    # Sezione: Grafici Matplotlib
    st.header("Grafici Matplotlib")
    # Recupero dati correnti per i grafici
    price_data = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={"ids":"bitcoin","vs_currencies":"usd"}
    ).json()["bitcoin"]["usd"]
    emitted_data = int(requests.get(
        "https://api.blockchain.info/q/totalbc", timeout=5
    ).text) / 1e8
    render_charts(emitted_data, price_data)

if __name__ == "__main__":
    main()










