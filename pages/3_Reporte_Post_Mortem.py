import streamlit as st
import os
import pandas as pd
from datetime import datetime

st.title("Subida de nuevos datos para predicción")

st.markdown("""
Esta sección está diseñada para que los operadores carguen nuevos datos cada 15 días. El archivo debe ser un **CSV sin preprocesar**, pero debe respetar el formato y las columnas esperadas por el sistema.

## ¿Cómo funciona?

1. El operador carga el archivo CSV con los créditos recientes a evaluar.
2. El sistema procesa automáticamente estos datos para dejarlos listos para el modelo.
3. El modelo calcula la estrategia de cobro óptima para cada crédito.
4. Tanto los datos originales como los resultados del modelo estarán disponibles para análisis en la pestaña de **Insights**.

---

✅ **Requisitos del archivo CSV:**

- Debe contener todas las columnas requeridas (por ejemplo: `credito_id`, `monto`, `fecha`, `emisora_actual`, etc.).
- No debe tener filas vacías o columnas renombradas.
- El archivo no debe estar filtrado, ordenado o modificado manualmente.

---

⚠️ **Advertencia importante**

- Si el archivo no cumple con el formato esperado, el sistema mostrará un error y no procesará el contenido.
- Asegúrate de revisar el archivo antes de cargarlo.
- Los datos subidos serán utilizados directamente por el modelo, así que cualquier error afectará las predicciones.
""")

uploaded_file = st.file_uploader("Cargar archivo CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Leer el contenido del archivo
        df = pd.read_csv(uploaded_file)

        # Crear la carpeta si no existe
        save_dir = "data/uploads"
        os.makedirs(save_dir, exist_ok=True)

        # Nombre del archivo con fecha y hora para evitar sobrescritura
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"datos_crudos_{now}.csv"
        filepath = os.path.join(save_dir, filename)

        # Guardar CSV
        df.to_csv(filepath, index=False)

        st.success(f"Archivo guardado exitosamente en `{filepath}`")
        st.info("Los datos han sido procesados y enviados al modelo.")
        st.info("Puedes ver los resultados en la pestaña de *Insights* una vez se complete el procesamiento.")

    except Exception as e:
        st.error("Hubo un error al procesar el archivo. Revisa el formato del CSV.")
        st.exception(e)
