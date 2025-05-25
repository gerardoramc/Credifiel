import streamlit as st
import pandas as pd
import pickle

@st.cache_data
def load_data_2025():
    return pd.read_csv("data/History/ListaCobroDetalle2025.csv")

@st.cache_data
def load_cobrables():
    return pd.read_csv("data/credits.csv")

@st.cache_data
def load_emisora_cat():
    return pd.read_csv("data/EmisoraBancoPrecios.csv")


@st.cache_data
def extract_dfs(clients):
    records = []
    hit_costs_records = []
    probabilities_records = []
    profits_records = []

    for client_id, data in clients.items():
        records.append({
            "client_id": client_id,
            "bank": data['bank'],
            "payment": data['payment'],
            "best_emisora": data['best_emisora']
        })
        for emisora, val in data['hit_costs'].items():
            hit_costs_records.append({
                "client_id": client_id,
                "emisora": emisora,
                **val
            })
        for emisora, prob in data['probabilities'].items():
            probabilities_records.append({
                "client_id": client_id,
                "emisora": emisora,
                "probability": prob
            })
        for emisora, profit in data['profits'].items():
            profits_records.append({
                "client_id": client_id,
                "emisora": emisora,
                "profit": profit
            })

    base_df = pd.DataFrame(records)
    hit_costs_df = pd.DataFrame(hit_costs_records)
    probabilities_df = pd.DataFrame(probabilities_records)
    profits_df = pd.DataFrame(profits_records)

    return base_df, hit_costs_df, probabilities_df, profits_df

# --- Button logic using session_state ---
if "data_loaded" not in st.session_state:
    st.session_state["data_loaded"] = False

if st.button("Crear"):
    with open("optimizer/clients.pkl", "rb") as f:
        credits = pickle.load(f)

    base_df, hit_costs_df, probabilities_df, profits_df = extract_dfs(credits)
    st.session_state["base_df"] = base_df
    st.session_state["data_loaded"] = True

# --- Show filters and data only if loaded ---
if st.session_state["data_loaded"]:
    base_df = st.session_state["base_df"]

    bank = st.selectbox("Seleccione Banco", ["Todos"] + sorted(base_df["bank"].unique().tolist()))
    if bank != "Todos":
        filtered_df = base_df[base_df['bank'] == bank]
    else:
        filtered_df = base_df

    st.dataframe(filtered_df)
