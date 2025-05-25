import streamlit as st
import pandas as pd


st.button("Crear")

@st.cache_data
def load_data_2025():
    data = pd.read_csv("../data/History/ListaCobroDetalle2025.csv")
    return data
