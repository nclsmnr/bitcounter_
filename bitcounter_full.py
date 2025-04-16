import streamlit as st
import requests
import matplotlib.pyplot as plt
import datetime

# =====================================================
# CONFIGURAZIONE E COSTANTI
# =====================================================
st.set_page_config(page_title="BITCOUNTER", layout="wide", initial_sidebar_state="expanded")
REFRESH_INTERVAL = 60  # Aggiornamento automatico ogni 60 secondi

# =====================================================
# FUNZIONI DI RACCOLTA DATI (Cache TTL = 60 sec)
# =====================================================
@st.cache_data(ttl=60)
def get_btc_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "bitcoin", "vs_currencies": "usd"}
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        return response.json()["bitcoin"]["usd"]
    except Exception as e:
        st.error(f"Errore nel recupero del prezzo BTC: {e}")
        return None

@st.cache_data(ttl=60)
def get_blockchain_data():
    data = {}
    try:
        response = requests.get("https://api.blockchain.info/q/totalbc", timeout=5)
        response.raise_for_status()
        satoshi_total = int(response.text)
        data["btc_emitted"] = satoshi_total / 100_000_000
    except Exception as e:
        st.error(f"Errore nel recupero dati blockchain: {e}")
        data["btc_emitted"] = None
    return data

# =====================================================
# FUNZIONI DI CALCOLO E STIMA
# =====================================================
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
    theoretical = market_cap / liquid_supply if liquid_supply else 0
    return price_now, theoretical

def estimate_remaining_btc(btc_emitted, total_supply=21_000_000):
    return total_supply - btc_emitted

def estimate_mining_countdown(btc_emitted):
    """
    Stima semplificata: si assume un block reward costante di 6.25 BTC
    e 10 minuti per blocco, senza tenere conto dei prossimi halving.
    """
    block_reward = 6.25
    remaining_btc = estimate_remaining_btc(btc_emitted)
    remaining_blocks = remaining_btc / block_reward
    seconds_remaining = remaining_blocks * 10 * 60  # 10 minuti per blocco
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

# =====================================================
# FUNZIONI DI VISUALIZZAZIONE
# =====================================================
def render_metrics(supply_data, price, btc_emitted):
    remaining_btc = estimate_remaining_btc(btc_emitted)
    mining_end = estimate_mining_countdown(btc_emitted)
    
    # Dividi le metriche in due colonne:
    # Colonna sinistra: 5 metriche (Supply Massima, Supply Emessa, Supply Liquida, BTC Persi, Prezzo BTC)
    # Colonna destra: 2 metriche (BTC da Minare, Countdown Fine Mining)
    col_left, col_right = st.columns(2)
    with col_left:
        st.metric("Supply Massima", f"{supply_data['total_theoretical']:,} BTC")
        st.metric("Supply Emessa", f"{supply_data['circulating']:,} BTC")
        st.metric("Supply Liquida", f"{supply_data['liquid']:,} BTC")
        st.metric("BTC Persi", f"{supply_data['lost']:,} BTC")
        st.metric("Prezzo BTC", f"${price:,.2f}")
    with col_right:
        st.metric("BTC da Minare", f"{remaining_btc:,.2f} BTC")
        st.metric("Countdown Fine Mining", format_countdown(mining_end))

def render_pie_chart(supply_data):
    labels = ["BTC Liquidi", "BTC Dormienti", "BTC Persi"]
    values = [
        supply_data["liquid"] - supply_data["dormant"],
        supply_data["dormant"],
        supply_data["lost"]
    ]
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")
    st.subheader("Distribuzione della Supply Effettiva")
    st.pyplot(fig)

def render_price_chart(current_price, theoretical_price):
    labels = ["Prezzo Attuale", "Prezzo Teorico"]
    values = [current_price, theoretical_price]
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(labels, values, color=["blue", "orange"])
    ax.set_ylabel("USD")
    ax.set_title("Confronto Prezzo BTC Reale vs. Teorico")
    st.subheader("Analisi Prezzo BTC")
    st.pyplot(fig)

# =====================================================
# PROGRAMMA PRINCIPALE
# =====================================================
def main():
    # Aggiunge l'effetto di pioggia di BTC in background
    add_background_rain()
    # Inserisce il meta refresh per aggiornamento automatico ogni REFRESH_INTERVAL secondi
    st.markdown(f"<meta http-equiv='refresh' content='{REFRESH_INTERVAL}'>", unsafe_allow_html=True)

    st.title("BITCOUNTER - Real Bitcoin Liquidity Dashboard")
    st.info(f"La pagina si aggiorna automaticamente ogni {REFRESH_INTERVAL} secondi")

    # Recupero dei dati aggiornati
    price = get_btc_price()
    blockchain_data = get_blockchain_data()
    if price is None or blockchain_data["btc_emitted"] is None:
        st.error("Impossibile recuperare i dati necessari. Riprova più tardi.")
        return

    btc_emitted = blockchain_data["btc_emitted"]
    supply_data = estimate_real_supply(btc_emitted)
    current_price, theoretical_price = calculate_theoretical_price(price, supply_data["circulating"], supply_data["liquid"])

    # Visualizzazione dei calcoli: metriche divise in due colonne
    st.header("Calcoli e Stime")
    render_metrics(supply_data, price, btc_emitted)

    # Visualizzazione dei grafici affiancati in due colonne
    st.header("Grafici")
    col1, col2 = st.columns(2)
    with col1:
        render_pie_chart(supply_data)
    with col2:
        render_price_chart(current_price, theoretical_price)

if __name__ == "__main__":
    main()


