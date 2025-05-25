import streamlit as st
from PIL import Image
import base64

st.set_page_config(page_title="Conectar fuentes", layout="wide")

st.markdown("<h2 style='text-align: center;'>Conectar fuente de datos</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Selecciona una fuente para comenzar</p>", unsafe_allow_html=True)
st.markdown("---")

# CSS personalizado para botones con imagen adentro
st.markdown("""
    <style>
    .image-button {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 150px;
        border: none;
        background-color: #f0f2f6;
        border-radius: 12px;
        transition: 0.3s;
        cursor: pointer;
    }
    .image-button:hover {
        background-color: #d6e4f0;
    }
    .image-button img {
        width: 48px;
        height: 48px;
        margin-bottom: 8px;
    }
    .image-button span {
        font-size: 16px;
        color: #333;
    }
    </style>
""", unsafe_allow_html=True)

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
        return f"data:image/png;base64,{encoded}"
# Crear botón HTML con imagen dentro
def data_card(label, image_path, key):
    button_html = f"""
        <form action="" method="post">
            <button class="image-button" name="{key}" type="submit">
                <img src="{get_base64_image(image_path)}" alt="{label}" />
                <span>{label}</span>
            </button>
        </form>
    """
    st.markdown(button_html, unsafe_allow_html=True)
    if st.session_state.get("clicked") == key:
        st.session_state["selected_data_source"] = label

# Manejar clic usando query params o fallback
clicked_key = st.query_params.get("clicked", [None])[0]
if clicked_key:
    st.session_state["clicked"] = clicked_key

# Mostrar las tarjetas en 4 columnas
col1, col2, col3, col4 = st.columns(4)

with col1:
    data_card("Importar CSV", "assets/csv.png", "csv")

with col2:
    data_card("Base de datos SQL", "assets/sql.png", "sql")

with col3:
    data_card("Azure Cloud", "assets/azure.png", "azure")

with col4:
    data_card("API REST", "assets/api.png", "api")

# Acción cuando se selecciona alguna fuente
if "selected_data_source" in st.session_state:
    st.success(f"Has seleccionado: {st.session_state['selected_data_source']}")
