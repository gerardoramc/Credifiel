import streamlit as st
from PIL import Image

# logo = Image.open("assets/credifiel_logo.webp")
# st.sidebar.image(logo, use_container_width=True)

st.title("¡Bienvenido a la aplicación de optimización de cobranzas de Credifiel!")

st.markdown("""
Esta aplicación tiene como objetivo apoyar la toma de decisiones en el proceso de cobro de créditos, utilizando un modelo bayesiano que estima la probabilidad de éxito de un cobro dependiendo de la emisora o estrategia seleccionada.

## ¿Cómo funciona?

Cada emisora corresponde a un banco en convenio con la empresa, y cada uno aplica distintas condiciones y costos al intentar realizar un cobro. Por ejemplo, hay emisoras que solo cobran por el intento si el cobro fue exitoso, mientras que otras generan un cargo incluso si el cobro falla.

El modelo, basado en datos históricos, estima la probabilidad de que un crédito sea cobrado exitosamente con cada emisora. Estas probabilidades se envían luego a un optimizador, que considera restricciones (como si el crédito es elegible para una emisora en particular) y una función objetivo que pondera el costo del intento frente al valor esperado de recuperación. Finalmente, el sistema selecciona la opción que maximiza ese valor esperado para cada crédito.
""")
