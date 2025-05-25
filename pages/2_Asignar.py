import streamlit as st
import pandas as pd
import pickle
import plotly.express as px
import numpy as np
import plotly.graph_objects as go

# ------------------ Loaders ------------------
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

# ------------------ Botón de carga ------------------
if "data_loaded" not in st.session_state:
    st.session_state["data_loaded"] = False

if st.button("Crear Asignación", use_container_width=True):
    with open("optimizer/clients.pkl", "rb") as f:
        credits = pickle.load(f)

    base_df, hit_costs_df, probabilities_df, profits_df = extract_dfs(credits)
    emisora_df = load_emisora_cat()

    st.session_state["probabilities_df"] = pd.merge(probabilities_df, emisora_df, left_on="emisora", right_on="idEmisora").drop(["emisora"], axis=1)
    st.session_state["profits_df"] = pd.merge(profits_df, emisora_df, left_on="emisora", right_on="idEmisora").drop(["emisora"], axis=1)
    st.session_state["base_df"] = pd.merge(base_df, emisora_df, left_on="best_emisora", right_on="idEmisora")
    st.session_state["hit_costs_df"] = pd.merge(hit_costs_df, emisora_df, left_on="emisora", right_on="idEmisora").drop(["emisora"], axis=1)
    st.session_state["data_loaded"] = True


# ------------------ Visualización ------------------
if st.session_state["data_loaded"]:
    base_df = st.session_state["base_df"]
    probabilities_df = st.session_state["probabilities_df"]
    profits_df = st.session_state["profits_df"]
    hit_costs_df = st.session_state["hit_costs_df"]

    bank = st.selectbox("Seleccione Banco", ["Todos"] + sorted(base_df["bank"].unique().tolist()))
    emisora = st.selectbox("Seleccione Emisora", ["Todas"] + sorted(base_df["NombreEmisora"].unique().tolist()))

    filtered_df = base_df
    if bank != "Todos":
        filtered_df = filtered_df[filtered_df['bank'] == bank]
    if emisora != "Todas":
        filtered_df = filtered_df[filtered_df['NombreEmisora'] == emisora]

    selected_emisoras = filtered_df['NombreEmisora'].unique()

    # --- Gráfica: Mediana de probabilidad por emisora ---
    filtered_probabilities_df = probabilities_df[probabilities_df['NombreEmisora'].isin(selected_emisoras)]
    median_probs = (
        filtered_probabilities_df
        .groupby('NombreEmisora')['probability']
        .median()
        .reset_index()
        .sort_values(by='probability', ascending=False)
    )
    fig_median_prob = px.bar(
        median_probs,
        x='NombreEmisora',
        y='probability',
        title='Mediana de Probabilidad de Domiciliado Exitoso por Emisora',
        labels={'NombreEmisora': 'Emisora', 'probability': 'Mediana Probabilidad de Éxito'},
    )

    # --- Gráfica: Distribución de ganancias esperadas ---
    filtered_profits_df = profits_df[profits_df['NombreEmisora'].isin(selected_emisoras)]
    sum_profits = (
        filtered_profits_df
        .groupby('NombreEmisora')['profit']
        .sum()
        .reset_index()
        .sort_values(by='profit', ascending=False)
    )
    bins = np.histogram_bin_edges(sum_profits['profit'], bins='auto')
    sum_profits['bin'] = pd.cut(sum_profits['profit'], bins=bins)
    grouped = sum_profits.groupby('bin').agg({
        'NombreEmisora': lambda x: '<br>'.join(x),
        'profit': 'count'
    }).reset_index()
    grouped['hover'] = grouped.apply(
        lambda row: f"Emisoras:<br>{row['NombreEmisora']}<br><br>Count: {row['profit']}", axis=1
    )
    fig_profit_dist = go.Figure(
        data=[
            go.Bar(
                x=grouped['bin'].astype(str),
                y=grouped['profit'],
                hovertext=grouped['hover'],
                hoverinfo='text',
            )
        ]
    )
    fig_profit_dist.update_layout(
        title='Distribución de la Suma del Valor Esperado por Emisora',
        xaxis_title='Bin de Suma del Valor Esperado',
        yaxis_title='Número de Emisoras',
    )

    # --- Gráfica: Costo por Hit Exitoso ---
    sum_hit_success = (
        hit_costs_df
        .groupby('NombreEmisora')['Costo_Hit_Win_x']
        .sum()
        .reset_index()
        .sort_values(by='Costo_Hit_Win_x', ascending=False)
    )
    fig_hit_win = px.bar(
        sum_hit_success,
        x='NombreEmisora',
        y='Costo_Hit_Win_x',
        title='Suma de Costo por Hit Exitoso por Emisora',
        labels={'NombreEmisora': 'Emisora', 'Costo_Hit_Win_x': 'Suma de Costo Hit Éxito'},
    )

    # --- Gráfica: Costo por Hit Fallido ---
    sum_hit_fail = (
        hit_costs_df
        .groupby('NombreEmisora')['Costo_Hit_Miss_x']
        .sum()
        .reset_index()
        .sort_values(by='Costo_Hit_Miss_x', ascending=True)
    )
    fig_hit_fail = px.bar(
        sum_hit_fail,
        x='NombreEmisora',
        y='Costo_Hit_Miss_x',
        title='Suma de Costo por Hit Fallido por Emisora',
        labels={'NombreEmisora': 'Emisora', 'Costo_Hit_Miss_x': 'Suma de Costo Hit Fallido'},
    )

    # --- Mostrar en diseño compacto ---
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_median_prob, use_container_width=True)
    with col2:
        st.plotly_chart(fig_profit_dist, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(fig_hit_win, use_container_width=True)
    with col4:
        st.plotly_chart(fig_hit_fail, use_container_width=True)

    # --- Mostrar tabla ---
    st.subheader("Detalle de Asignación")
    st.dataframe(filtered_df)
