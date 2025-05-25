import streamlit as st
import pandas as pd
import pickle
import plotly.express as px
import numpy as np
import plotly.graph_objects as go


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

if st.button("Crear Asignación", use_container_width = True):
    with open("optimizer/clients.pkl", "rb") as f:
        credits = pickle.load(f)

    base_df, hit_costs_df, probabilities_df, profits_df = extract_dfs(credits)
    emisora_df = load_emisora_cat()
    st.session_state["probabilities_df"] = pd.merge(probabilities_df,emisora_df, left_on= "emisora",right_on="idEmisora").drop(["emisora"], axis=1)
    st.session_state["profits_df"] = pd.merge(profits_df,emisora_df, left_on= "emisora",right_on="idEmisora").drop(["emisora"], axis=1)
    st.session_state["base_df"] = pd.merge(base_df,emisora_df, left_on= "best_emisora",right_on="idEmisora").drop(["best_emisora"], axis=1)
    st.session_state["hit_costs_df"] = pd.merge(hit_costs_df, emisora_df, left_on= "emisora",right_on="idEmisora").drop(["emisora"], axis=1)
    st.session_state["data_loaded"] = True

# --- Show filters and data only if loaded ---
if st.session_state["data_loaded"]:
    base_df = st.session_state["base_df"]
    probabilities_df = st.session_state["probabilities_df"]
    profits_df = st.session_state["profits_df"]
    hit_costs_df = st.session_state["hit_costs_df"]

    bank = st.selectbox("Seleccione Banco", ["Todos"] + sorted(base_df["bank"].unique().tolist()))
    emisora = st.selectbox("Seleccione Emisora", ["Todas"] + sorted(base_df["NombreEmisora"].unique().tolist()))
    # Apply filters if a specific value is selected
    filtered_df = base_df
    if bank != "Todos":
        filtered_df = filtered_df[filtered_df['bank'] == bank]

    if emisora != "Todas":
        filtered_df = filtered_df[filtered_df['NombreEmisora'] == emisora]

    
    selected_emisoras = filtered_df['NombreEmisora'].unique()
    selected_emisoras_num = filtered_df['idEmisora'].unique()

    # Filter probabilities_df where emisora is in selected_emisoras
    filtered_probabilities_df = probabilities_df[probabilities_df['NombreEmisora'].isin(selected_emisoras)]
    filtered_profits_df = profits_df[profits_df['NombreEmisora'].isin(selected_emisoras)]

    # Merge to bring in NombreEmisora (since probabilities_df only has 'emisora')
    # Make sure 'emisora' <-> 'NombreEmisora' relation exists in filtered_df
    # Now group by NombreEmisora and compute median probability
    median_probs = (
        filtered_probabilities_df
        .groupby('NombreEmisora')['probability']
        .median()
        .reset_index()
        .sort_values(by='probability', ascending=False)
    )

    # Plot using Plotly
    fig = px.bar(
        median_probs,
        x='NombreEmisora',
        y='probability',
        title='Mediana de Probabilidad de Domiciliado Exitoso por Emisora',
        labels={'NombreEmisora': 'Emisora', 'probability': 'Mediana Probabilidad de Éxito'},
    )

    st.plotly_chart(fig, use_container_width=True)

    # Step 1: Compute sum of profits per emisora
    sum_profits = (
        filtered_profits_df
        .groupby('NombreEmisora')['profit']
        .sum()
        .reset_index()
        .sort_values(by='profit', ascending=False)
    )

    # Step 2: Bin the profit sums
    bins = np.histogram_bin_edges(sum_profits['profit'], bins='auto')
    sum_profits['bin'] = pd.cut(sum_profits['profit'], bins=bins)

    # Step 3: Group by bin and collect emisoras per bin
    # Step 3: Group by bin and collect emisoras per bin (one per line for tooltip)
    grouped = sum_profits.groupby('bin').agg({
        'NombreEmisora': lambda x: '<br>'.join(x),
        'profit': 'count'  # Number of emisoras in the bin
    }).reset_index()

    # Step 4: Add custom hover text
    grouped['hover'] = grouped.apply(
        lambda row: f"Emisoras:<br>{row['NombreEmisora']}<br><br>Count: {row['profit']}", axis=1
    )


    # Step 5: Plot using go.Bar
    fig = go.Figure(
        data=[
            go.Bar(
                x=grouped['bin'].astype(str),
                y=grouped['profit'],
                hovertext=grouped['hover'],
                hoverinfo='text',
            )
        ]
    )

    fig.update_layout(
        title='Distribución de la Suma del Valor Esperado por Emisora',
        xaxis_title='Bin de Suma del Valor Esperado',
        yaxis_title='Número de Emisoras',
    )

    st.plotly_chart(fig, use_container_width=True)

    sum_hit_costs = (
        hit_costs_df
        .groupby('NombreEmisora')['Costo_Hit_Win_x']
        .sum()
        .reset_index()
        .sort_values(by='Costo_Hit_Win_x', ascending=False)
    )

    fig = px.bar(
        sum_hit_costs,
        x='NombreEmisora',
        y='Costo_Hit_Win_x',
        title='Suma de Costo por Hit Exitoso por Emisora',
        labels={'NombreEmisora': 'Emisora', 'Costo_Hit_Win_x': 'Suma de Costo Hit Éxito'},
    )

    st.plotly_chart(fig, use_container_width=True)

    sum_hit_costs = (
        hit_costs_df
        .groupby('NombreEmisora')['Costo_Hit_Miss_x']
        .sum()
        .reset_index()
        .sort_values(by='Costo_Hit_Miss_x', ascending=True)
    )

    fig = px.bar(
        sum_hit_costs,
        x='NombreEmisora',
        y='Costo_Hit_Miss_x',
        title='Suma de Costo por Hit Fallido por Emisora',
        labels={'NombreEmisora': 'Emisora', 'Costo_Hit_Miss_x': 'Suma de Costo Hit Fallido'},
    )

    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(filtered_df)



