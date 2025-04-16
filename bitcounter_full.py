import streamlit as st
import requests
import matplotlib.pyplot as plt
import datetime

# ===============================================
# CONFIGURAZIONE E COSTANTI
# ===============================================
st.set_page_config(page_title="BITCOUNTER", layout="wide", initial_sidebar_state="expanded")
REFRESH_INTERVAL = 10  # in secondi

# ===============================================
# FUNZIONI DI RACCOLTA DATI (CACHED PER TTL=10s)
# ===============================================
@st.cache_data(ttl=10)
def get_btc_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "bitcoin", "vs_currencies": "usd"}
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        return response.json()["bitcoin"]["usd"]
    except Exception as err:
        st.error(f"Errore nel recupero del prezzo BTC: {err}")
        return None

@st.cache_data(ttl=10)
def get_blockchain_data():
    data = {}
    try:
        response = requests.get("https://api.blockchain.info/q/totalbc", timeout=5)
        response.raise_for_status()
        satoshi_total = int(response.text)
        data["btc_emitted"] = satoshi_total / 100_000_000
    except Exception as err:
        st.error(f"Errore nel recupero dati blockchain: {err}")
        data["btc_emitted"] = None
    return data

# ===============================================
# FUNZIONI DI CALCOLO E STIMA
# ===============================================
def estimate_real_supply(btc_emitted, lost_estimate=4_000_000, dormant=1_500_000):
    circulating = btc_emitted
    lost = lost_estimate
    liquid = circulating - lost
    return {
        "total_theoretical": 21_000_000,
        "circulating": circulating,
        "liquid": liquid,
        "lost": lost,
        "dormant": dormant
    }

def calculate_theoretical_price(price_now, circulating, liquid_supply):
    market_cap = price_now * circulating
    return price_now, (market_cap / liquid_supply if liquid_supply else 0)

def estimate_remaining_btc(btc_emitted, total_supply=21_000_000):
    return total_supply - btc_emitted

def estimate_mining_countdown(btc_emitted):
    """
    Stima semplificata: si assume un block reward costante di 6.25 BTC
    e 10 minuti per blocco, senza considerare i prossimi halving.
    """
    block_reward = 6.25
    remaining_btc = estimate_remaining_btc(btc_emitted)
    remaining_blocks = remaining_btc / block_reward
    seconds_remaining = remaining_blocks * 10 * 60
    return datetime.datetime.now() + datetime.timedelta(seconds=seconds_remaining)

def format_countdown(target_time):
    now = datetime.datetime.now()
    diff = target_time - now
    if diff.total_seconds() <= 0:
        return "Mining terminato"
    days = diff.days
    hours, rem = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{days}g {hours}h {minutes}m {seconds}s"

# ===============================================
# FUNZIONI DI VISUALIZZAZIONE
# ===============================================
def render_overview_boxes(supply_data, price, btc_emitted):
    remaining_btc = estimate_remaining_btc(btc_emitted)
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Supply Massima", f"{supply_data['total_theoretical']:,} BTC")
    col2.metric("Supply Emessa", f"{supply_data['circulating']:,} BTC")
    col3.metric("Supply Liquida", f"{supply_data['liquid']:,} BTC")
    col4.metric("BTC Persi", f"{supply_data['lost']:,} BTC")
    col5.metric("Prezzo BTC", f"${price:,.2f}")
    col6.metric("BTC da Minare", f"{remaining_btc:,.2f} BTC")

def render_pie_chart(supply_data):
    labels = ["BTC Liquidi", "BTC Dormienti", "BTC Persi"]
    values = [
        supply_data["liquid"] - supply_data["dormant"],
        supply_data["dormant"],
        supply_data["lost"]
    ]
    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")
    st.subheader("Distribuzione della Supply Effettiva")
    st.pyplot(fig)

def render_price_chart(current_price, theoretical_price):
    labels = ["Prezzo Attuale", "Prezzo Teorico"]
    values = [current_price, theoretical_price]
    fig, ax = plt.subplots()
    ax.bar(labels, values)
    ax.set_ylabel("USD")
    ax.set_title("Confronto Prezzo BTC Reale vs. Teorico")
    st.subheader("Analisi Prezzo BTC")
    st.pyplot(fig)

def render_countdown_timer(target_time):
    countdown = format_countdown(target_time)
    st.metric("Countdown Fine Mining", countdown)

# ===============================================
# PROGRAMMA PRINCIPALE
# ===============================================
def main():
    # Inserisce un meta refresh per ricaricare la pagina automaticamente
    st.markdown(f"<meta http-equiv='refresh' content='{REFRESH_INTERVAL}'>", unsafe_allow_html=True)

    st.title("BITCOUNTER - Real Bitcoin Liquidity Dashboard")
    st.info(f"La pagina si aggiorna automaticamente ogni {REFRESH_INTERVAL} secondi")

    # Recupero dati aggiornati
    price = get_btc_price()
    blockchain_data = get_blockchain_data()
    if price is None or blockchain_data["btc_emitted"] is None:
        st.error("Impossibile recuperare i dati necessari. Riprova più tardi.")
        return

    btc_emitted = blockchain_data["btc_emitted"]

    # Calcoli e stime
    supply_data = estimate_real_supply(btc_emitted)
    current_price, theoretical_price = calculate_theoretical_price(
        price, 
        supply_data["circulating"], 
        supply_data["liquid"]
    )
    mining_end_time = estimate_mining_countdown(btc_emitted)

    # Visualizzazioni
    render_overview_boxes(supply_data, price, btc_emitted)
    render_countdown_timer(mining_end_time)
    render_pie_chart(supply_data)
    render_price_chart(current_price, theoretical_price)

if __name__ == "__main__":
    main()


