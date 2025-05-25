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


REQUIRED_COLUMNS = {
    "idCredito": str,
    "montoCobrar": float,
    "fechaCobroBanco": str,  # podrías parsearla después
    "idBanco": str
}

uploaded_file = st.file_uploader("Cargar archivo CSV", type=["csv"])

# Crear la carpeta si no existe
save_dir = "data/uploads"
os.makedirs(save_dir, exist_ok=True)

# Ruta al log
log_path = os.path.join(save_dir, "upload_log.csv")

# Función para registrar eventos
def log_upload(fecha_envio_cobro, status, message):
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fecha_envio_cobroy": fecha_envio_cobro,
        "status": status,
        "message": message
    }

    if os.path.exists(log_path):
        log_df = pd.read_csv(log_path)
        log_df = pd.concat([log_df, pd.DataFrame([log_entry])], ignore_index=True)
    else:
        log_df = pd.DataFrame([log_entry])

    log_df.to_csv(log_path, index=False)

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        # ✅ Validar columnas
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            st.error(f"❌ Faltan columnas requeridas: {', '.join(missing_cols)}")
            st.stop()

        # ✅ Validar tipos de datos
        type_errors = []
        for col, expected_type in REQUIRED_COLUMNS.items():
            sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
            if sample is not None and not isinstance(sample, expected_type):
                try:
                    df[col] = df[col].astype(expected_type)
                except Exception:
                    type_errors.append(f"{col} debe ser tipo {expected_type.__name__}")
        if type_errors:
            st.error("❌ Errores en los tipos de datos:\n- " + "\n- ".join(type_errors))
            st.stop()

        # ✅ Guardar el archivo
        save_dir = "data/uploads"
        os.makedirs(save_dir, exist_ok=True)
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"datos_crudos_{now}.csv"
        filepath = os.path.join(save_dir, filename)
        df.to_csv(filepath, index=False)

        # ✅ Mostrar resumen y mensaje de éxito
        st.success(f"✅ Archivo validado y guardado exitosamente: `{filename}`")
        st.dataframe(df.head())
                # 🎯 Mostrar porcentaje de cada emisora
        st.markdown("### 📊 Distribución de emisoras en el archivo")

        # Verifica que la columna exista (puedes cambiar 'emisora_actual' por el nombre real si es diferente)
        if "idEmisora" in df.columns:
            emisora_dist = df["idEmisora"].value_counts(normalize=True).mul(100).round(2)
            emisora_df = emisora_dist.reset_index()
            emisora_df.columns = ["Emisora", "Porcentaje (%)"]

            # Mostrar tabla
            st.dataframe(emisora_df)

            # Mostrar gráfica
            st.bar_chart(emisora_df.set_index("Emisora"))
        else:
            st.warning("⚠️ No se encontró la columna 'idEmisora en  el archivo.")
        st.info("✅ Datos preparados. Listos para enviarse al modelo.")
        st.markdown("## 📌 Análisis de Transacciones")

        # Agregar columnas auxiliares
        df["es_exito"] = df["fechaCobroBanco"].notna()
        df["es_reintento"] = df["transCount"] > 1
        df["es_fallo"] = df["fechaCobroBanco"].isna()

        # IDs
        ids_reintento = df[df["Status"].str.contains("reintento", case=False)]["consecutivoCobro"]
        ids_error = df[df["Status"].str.contains("error|cuenta cancelada", case=False)]["consecutivoCobro"]
        ids_fallido = df[df["Status"].str.contains("rechazado|fondos|fallido", case=False)]["consecutivoCobro"]


        # Exportar archivos
        st.download_button("⬇ Descargar IDs erróneos", data=ids_error.to_csv(index=False), file_name="ids_exito.csv")
        st.download_button("⬇ Descargar IDs fallidos", data=ids_fallido.to_csv(index=False), file_name="ids_fallo.csv")
        st.download_button("⬇ Descargar IDs de reintentos", data=ids_reintento.to_csv(index=False), file_name="ids_reintento.csv")

        # Porcentaje de reintentos exitosos
        reintentos = df[df["es_reintento"]]
        reintentos_exitosos = reintentos[reintentos["es_exito"]]
        pct_exito_reintentos = round(len(reintentos_exitosos) / len(reintentos) * 100, 2) if len(reintentos) > 0 else 0

        # Ganancia y pérdida
        df["ganancia"] = df.apply(lambda row: row["montoCobrado"] - row["Costo"] if row["es_exito"] else 0, axis=1)
        df["perdida"] = df.apply(lambda row: -row["Costo"] if not row["es_exito"] else 0, axis=1)

        ganancia_total = df["ganancia"].sum()
        perdida_total = df["perdida"].sum()

        # Métricas en pantalla
        st.metric("✅ Porcentaje de reintentos exitosos", f"{pct_exito_reintentos}%")
        st.metric("💸 Costo total", f"${abs(perdida_total):,.2f}")
        st.metric("💰 Ganancia total", f"${ganancia_total:,.2f}")



    except Exception as e:
        st.error("💥 Error inesperado al procesar el archivo:")
        st.exception(e)