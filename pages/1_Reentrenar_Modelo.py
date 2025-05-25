import streamlit as st

import streamlit as st

st.title("Reentrenamiento del modelo bayesiano")

st.markdown("""
El reentrenamiento del modelo bayesiano permite actualizar las probabilidades de éxito de cobro por emisora utilizando datos históricos más recientes. Este proceso es esencial para asegurar que el modelo refleje los cambios en comportamiento de pago y desempeño de las emisoras a lo largo del tiempo.

## ¿Qué hace este reentrenamiento?

- Recalcula las probabilidades de cobro exitoso para cada emisora, utilizando un modelo bayesiano gaussiano.
- Toma en cuenta el comportamiento pasado de los intentos de cobro registrados en la base de datos histórica.
- Actualiza internamente los parámetros que luego serán utilizados por el optimizador para decidir la mejor estrategia de cobro.

---

⚠️ **Advertencia importante**

Antes de proceder con el reentrenamiento, asegúrate de que:

1. Los datos históricos estén **completos y actualizados** en la fuente de datos.
2. No se estén cargando datos con errores, duplicados o sin limpiar.
3. Comprendes que el modelo actual será **sobrescrito** con los nuevos parámetros calculados.

Este proceso puede afectar directamente las decisiones de cobro para los créditos futuros.  
Si no estás seguro, consulta con el equipo de ciencia de datos antes de continuar.

""")

# Botón para continuar con el reentrenamiento (esto es solo visual, puedes conectarlo a la lógica real)
if st.sidebar.button("Iniciar reentrenamiento"):
    st.success("Reentrenamiento iniciado... (esto es un placeholder)")
