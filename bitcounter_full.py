# BITCOUNTER - Real Bitcoin Liquidity Dashboard (tutto in un unico file per GitHub)

import streamlit as st
import requests
import matplotlib.pyplot as plt

# -------------------------------
# FUNZIONI DI RACCOLTA DATI
# -------------------------------

def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin", "vs_currencies": "usd"}
    res = requests.get(url, params=params)
    return res.json()["bitcoin"]["usd"]

def get_blockchain_data():
    data = {}
    try:
        sats = requests.get("https://api.blockchain.info/q/totalbc").text
        data["btc_emitted"] = int(sats) / 100_000_000
    except Exception as e:
        data["btc_emitted"] = None
    return data

# -------------------------------
# MODELLI E CALCOLI
# -------------------------------

def estimate_real_supply(btc_emitted, lost_estimate=4_000_000):
    circulating = btc_emitted
    lost = lost_estimate
    dormant = 1_500_000
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
    price_if_real = market_cap / liquid_supply
    return price_now, price_if_real

# -------------------------------
# COMPONENTI VISUALI
# -------------------------------

def render_overview_boxes(data, price):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Supply Massima", f"{data['total_theoretical']:,} BTC")
    col2.metric("Supply Emessa", f"{data['circulating']:,} BTC")
    col3.metric("Stima Supply Liquida", f"{data['liquid']:,} BTC")
    col4.metric("BTC Persi Stimati", f"{data['lost']:,} BTC")
    st.markdown(f"**Prezzo BTC attuale:** ${price:,.2f}")

def render_pie_chart(data):
    labels = ["BTC Liquidi", "BTC Dormienti", "BTC Persi"]
    values = [
        data["liquid"] - data["dormant"],
        data["dormant"],
        data["lost"]
    ]
    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")
    st.subheader("Distribuzione della Supply Effettiva")
    st.pyplot(fig)

def render_price_chart(price_now, price_theoretical):
    labels = ["Prezzo Attuale", "Prezzo Teorico (supply liquida)"]
    values = [price_now, price_theoretical]
    fig, ax = plt.subplots()
    ax.bar(labels, values)
    ax.set_ylabel("USD")
    ax.set_title("Confronto Prezzo BTC Reale vs Teorico")
    st.subheader("Prezzo Teorico in base alla Supply Reale")
    st.pyplot(fig)

# -------------------------------
# APP PRINCIPALE
# -------------------------------

def main():
    st.set_page_config(page_title="BITCOUNTER", layout="wide")
    st.title("BITCOUNTER - Real Bitcoin Liquidity Dashboard")

    price = get_btc_price()
    btc_data = get_blockchain_data()
    if btc_data["btc_emitted"] is None:
        st.error("Errore nel recupero dei dati dalla blockchain")
        return

    supply_data = estimate_real_supply(btc_emitted=btc_data["btc_emitted"])

    render_overview_boxes(supply_data, price)
    render_pie_chart(supply_data)

    real, theoretical = calculate_theoretical_price(price, supply_data["circulating"], supply_data["liquid"])
    render_price_chart(real, theoretical)

if __name__ == "__main__":
    main()
