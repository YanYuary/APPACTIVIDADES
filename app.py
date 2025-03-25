import streamlit as st
import pandas as pd
import altair as alt
from datetime import date, datetime
#import toml quitamos para SCC
import gspread
import numpy as np
import matplotlib

# ============================
# Configuración de encabezados esperados
# ============================
EXPECTED_HEADERS = ["Actividad", "Sem 1", "Sem 2", "Sem 3", "Sem 4", "Fecha Inicio", "Fecha Fin", "Comentarios"]  # se agregó la columna "Comentarios"


# ============================
# Funciones para Google Sheets                    #AQUI ESTA LA MODIFICACION REALIZADA 
# ============================


#------------------------------------ Cargar credenciales desde el archivo TOML -----------------------------------------------#
def connect_gsheets():
    # Modificado: Usar st.secrets en lugar de cargar archivo TOML -------------------------------------------------------------# NOTA IMPORTANTE
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])  ## Conexión directa via st.secrets MODIFICACION TOML
    sh = gc.open("ACTIVIDADES_AVANCE")
    worksheet = sh.sheet1  # seleccionamos la hoja 1
    return worksheet


#---------------------------------------- Cargar el Archivo de Google Sheets -----------------------------------------------#
def load_data():
    worksheet = connect_gsheets()
    # Se especifican los encabezados esperados para evitar duplicados
    data = worksheet.get_all_records(expected_headers=EXPECTED_HEADERS)
    df = pd.DataFrame(data)
    if not df.empty:
        # Si en el Sheets aparece alguna columna extra, se ignora
        df = df[EXPECTED_HEADERS]
        # Convertir las columnas de fecha a datetime (si es posible)
        df["Fecha Inicio"] = pd.to_datetime(df["Fecha Inicio"], errors="coerce")
        df["Fecha Fin"] = pd.to_datetime(df["Fecha Fin"], errors="coerce")
    return df

#---------------------------------------- Consolida Fechas y Columnas del Archivo de Google Sheets -----------------------------------------------#
def update_sheet(df):
    worksheet = connect_gsheets()
    # Crear una copia y convertir las fechas a string para evitar error JSON serializable
    df_copy = df.copy()
    if "Fecha Inicio" in df_copy.columns:
        df_copy["Fecha Inicio"] = df_copy["Fecha Inicio"].apply(lambda x: x.strftime("%Y-%m-%d") if pd.notnull(x) else "")
    if "Fecha Fin" in df_copy.columns:
        df_copy["Fecha Fin"] = df_copy["Fecha Fin"].apply(lambda x: x.strftime("%Y-%m-%d") if pd.notnull(x) else "")
    worksheet.clear()
    # Se actualiza la hoja con encabezados y filas
    worksheet.update([df_copy.columns.values.tolist()] + df_copy.fillna("").values.tolist())


def delete_activity(activity_name):
    worksheet = connect_gsheets()
    # Se obtiene toda la data usando los encabezados esperados
    data = worksheet.get_all_records(expected_headers=EXPECTED_HEADERS)
    for i, row in enumerate(data, start=2):  # start=2 porque la fila 1 es el encabezado
        if row.get("Actividad") == activity_name:
            worksheet.delete_rows(i)
            break
#----------------------------------------------------------------------------------------------------------------------------------------------------#


# ============================
# Configuración Inicial de la App
# ============================

#---------------------------------------- Título de la App -----------------------------------------------#
st.set_page_config(page_title="Avance de Actividades - YanYuary", layout="wide", initial_sidebar_state="expanded", page_icon="👽")

#---------------------------------------- Se carga la data desde Google Sheets y se guarda en session_state -----------------------------------------------#
if "df" not in st.session_state:
    st.session_state.df = load_data()


# ============================
# Estilos CSS
# ============================


#---------------------------------------- Se define el estilo del CSS -----------------------------------------------#
st.markdown("""
    <style>
    .title {
        background: linear-gradient(90deg, #ff6b6b, #ff8e53);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #4b6cb7, #182848);
        border-radius: 15px;
        padding: 1.5rem;
        color: white;
        margin: 0.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stDataFrame th {
        background: linear-gradient(90deg, #4b6cb7, #182848) !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)


# ============================
# Funciones Auxiliares
# ============================


#---------------------------------------- Se define ..... ----------------------------------------------#
def apply_row_style(row):
    semanas = ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4']
    try:
        values = [float(row.get(s, 0)) for s in semanas]
        avg = sum(values) / len(values)
    except:
        avg = 0
    color = f"linear-gradient(90deg, rgba(46,213,115,{avg/100 + 0.3}) 0%, rgba(255,71,87,{1 - avg/100 + 0.3}) 100%)"
    return [f'background: {color}; color: white;'] * len(row)


# ============================
# Layout Principal
# ============================


#---------------------------------------- Se definem las pestañas de la APP -----------------------------------------------#
tab0, tab1, tab2 = st.tabs(["🔭 Visión General", "📋 Actualizar Progreso", "🛰️ Evolución"])


# ============================
# Pestaña 0 - Visión General
# ============================
with tab0:
    st.markdown('<div class="title"><h1> 🛸 Progreso Global 🛸 </h1></div>', unsafe_allow_html=True)
    df = st.session_state.df.copy()
    if df.empty:
        st.write("No hay actividades registradas.")
    else:
        # Métrica: Promedio global de progreso
        sem_cols = [col for col in df.columns if col.startswith("Sem")]
        if sem_cols:
            # Limpiar datos numéricos
            df[sem_cols] = df[sem_cols].replace('', np.nan).apply(pd.to_numeric, errors='coerce')
            total = df[sem_cols].mean().mean()
                        
            st.markdown(f"""
                <div style="
                    background: white;
                    text-align: center;
                    padding: 15px;
                    border-radius: 10px;
                ">
                    <h1 style="color: #000000 !important; margin: 0;">{total:.1f}%</h1>
                </div>
            """, unsafe_allow_html=True)


        # Tabla estilizada con formato y limpieza de datos
        styled_df = df.style.format({
            "Fecha Inicio": lambda d: d.strftime("%d/%m/%Y") if pd.notnull(d) else "",
            "Fecha Fin": lambda d: d.strftime("%d/%m/%Y") if pd.notnull(d) else ""
        }, na_rep='')\
            .apply(apply_row_style, axis=1)\
            .background_gradient(subset=sem_cols, cmap='YlGnBu', text_color_threshold=0.5, vmin=0, vmax=100)\
            .set_properties(**{
                'background-color': '#f8f9fa',
                'color': '#2d3436',
                'border': '1px solid #dfe6e9'
            })\
            .set_table_styles([{
                'selector': 'th',
                'props': [
                    ('background-color', '#0984e3'),
                    ('color', 'white'),
                    ('font-family', 'Arial'),
                    ('border', '1px solid #74b9ff')
                ]
            }, {
                'selector': 'tr:hover',
                'props': [('background-color', '#ffeaa7')]
            }])\
            .set_properties(subset=['Fecha Inicio', 'Fecha Fin'], **{
                'font-weight': '600',
                'color': '#d63031',
                'background-color': '#ffcccc'
            })\
            .bar(subset=sem_cols, color='#00b894', vmin=0, vmax=100)\
            .format("{:.1f}%", subset=sem_cols)  # Formato porcentual

        st.dataframe(styled_df, use_container_width=True, height=400)

        # Mapa de calor
        if sem_cols:
            heat_df = df.melt(id_vars="Actividad", value_vars=sem_cols, var_name="Semana", value_name="Progreso")
            heatmap = alt.Chart(heat_df).mark_rect().encode(
                x="Semana:N",
                y="Actividad:N",
                color=alt.Color("Progreso:Q", scale=alt.Scale(scheme="goldred")),
                tooltip=["Actividad", "Semana", "Progreso"]
            ).properties(height=300)
            st.altair_chart(heatmap, use_container_width=True)


# ============================
# Pestaña 1 - Actualizar Progreso
# ============================
with tab1:
    st.markdown('<div class="title"><h1> 🌌 Actualizar Progreso 🌌 </h1></div>', unsafe_allow_html=True)
    df = st.session_state.df.copy()

    sem_cols = [col for col in df.columns if col.startswith("Sem")]
    semana = st.selectbox("Seleccionar Semana", sem_cols, key="semana_selector")

    # Se crean formularios individuales por cada actividad
    if df.empty:
        st.write("No hay actividades registradas para actualizar.")
    else:
        for idx, row in df.iterrows():
            with st.form(key=f"update_form_{idx}", clear_on_submit=False):
                st.subheader(row["Actividad"])
                cols = st.columns([2, 1, 1, 3])
                with cols[0]:
                    new_start = st.date_input(
                        "Fecha Inicio",
                        value=row["Fecha Inicio"].date() if pd.notnull(row["Fecha Inicio"]) else date.today(),
                        key=f"start_{idx}_{semana}"
                    )
                with cols[1]:
                    new_end = st.date_input(
                        "Fecha Fin",
                        value=row["Fecha Fin"].date() if pd.notnull(row["Fecha Fin"]) else date.today(),
                        key=f"end_{idx}_{semana}"
                    )
                with cols[3]:
                    current_value = row.get(semana, 0)
                    new_value = st.slider(
                        "Progreso",
                        0, 100,
                        value=int(current_value) if current_value != "" else 0,
                        key=f"slider_{idx}_{semana}"
                    )
                # Nuevo textbox para Comentarios, ubicado debajo de la fecha
                new_comentario = st.text_input(
                    "Comentario",
                    value=row.get("Comentarios", ""),
                    key=f"comentario_{idx}"
                )
                submitted = st.form_submit_button("💾 Guardar Cambios")
                if submitted:
                    # Actualiza los valores en el DataFrame
                    df.at[idx, "Fecha Inicio"] = pd.to_datetime(new_start)
                    df.at[idx, "Fecha Fin"] = pd.to_datetime(new_end)
                    df.at[idx, semana] = new_value
                    df.at[idx, "Comentarios"] = new_comentario
                    update_sheet(df)
                    st.success(f"Cambios guardados para '{row['Actividad']}'.")
                    st.session_state.df = load_data()

    st.markdown("---")
    st.markdown("### Eliminar Actividad")
    with st.form("delete_form"):
        act_to_delete = st.selectbox("Selecciona la actividad a borrar", df["Actividad"].tolist(), key="delete_select")
        delete_submitted = st.form_submit_button("🗑️ Borrar Actividad")
        if delete_submitted:
            delete_activity(act_to_delete)
            st.success(f"Actividad '{act_to_delete}' eliminada.")
            st.session_state.df = load_data()

    st.markdown("---")
    st.markdown("### ⚛️ Añadir Nueva Actividad")
    with st.form("add_activity_form"):
        nueva_actividad = st.text_input("Nombre de la Actividad")
        new_sem1 = st.number_input("Sem 1", min_value=0, max_value=100, value=0)
        new_sem2 = st.number_input("Sem 2", min_value=0, max_value=100, value=0)
        new_sem3 = st.number_input("Sem 3", min_value=0, max_value=100, value=0)
        new_sem4 = st.number_input("Sem 4", min_value=0, max_value=100, value=0)
        new_fecha_inicio = st.date_input("Fecha Inicio", value=date.today())
        new_fecha_fin = st.date_input("Fecha Fin", value=date.today())
        # Nuevo campo para Comentarios en actividad nueva
        new_comentario = st.text_input("Comentario", value="")
        add_submitted = st.form_submit_button("➕ Añadir Actividad")
        if add_submitted:
            if nueva_actividad.strip() == "":
                st.error("El nombre de la actividad es obligatorio.")
            else:
                fecha_inicio_str = new_fecha_inicio.strftime("%Y-%m-%d")
                fecha_fin_str = new_fecha_fin.strftime("%Y-%m-%d")
                new_row = [
                    nueva_actividad,
                    new_sem1, new_sem2, new_sem3, new_sem4,
                    fecha_inicio_str,
                    fecha_fin_str,
                    new_comentario
                ]
                worksheet = connect_gsheets()
                worksheet.append_row(new_row)
                st.success("Actividad añadida.")
                st.session_state.df = load_data()


# ============================
# Pestaña 3 - Evolución Histórica
# ============================
with tab2:
    st.markdown('<div class="title"><h1> 👾 Evolución Histórica 👾 </h1></div>', unsafe_allow_html=True)
    df = st.session_state.df.copy()
    sem_cols = [col for col in df.columns if col.startswith("Sem")]
    if not df.empty and sem_cols:
        melt_df = df.melt(
            id_vars=["Actividad"],
            value_vars=sem_cols,
            var_name="Semana",
            value_name="Progreso"
        )
        line_chart = alt.Chart(melt_df).mark_line(point=True, strokeWidth=3).encode(
            x=alt.X("Semana:N", sort=sem_cols),
            y="Progreso:Q",
            color="Actividad:N",
            tooltip=["Actividad", "Semana", "Progreso"]
        ).properties(height=400, title="Evolución por Semana")
        st.altair_chart(line_chart, use_container_width=True)
    else:
        st.write("No hay datos para mostrar la evolución.")
