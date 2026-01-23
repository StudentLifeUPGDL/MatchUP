import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import time

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Matchmaking San Valentín UP",
    page_icon="💘",
    layout="centered"
)

# --- ESTILOS CSS (TEMA SAN VALENTÍN) ---
st.markdown("""
    <style>
    /* Fondo general con un degradado suave */
    .stApp {
        background: linear-gradient(to bottom, #fff0f5, #ffffff);
    }
    
    /* Títulos en rojo pasión */
    h1, h2, h3 {
        color: #D32F2F !important;
        font-family: 'Helvetica', sans-serif;
    }
    
    /* Métricas con fondo blanco y borde rosa */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 2px solid #ffccd5;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Botón personalizado */
    .stButton>button {
        background-color: #FF4B4B;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #D32F2F;
        color: white;
    }
    
    /* Ajuste de la tabla */
    div[data-testid="stDataFrame"] {
        border: 2px solid #ffccd5;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN DE COLUMNAS DE GOOGLE SHEETS ---
# IMPORTANTE: Cambia estos textos EXACTAMENTE por como aparecen en la fila 1 de tu Excel
COL_ID_1 = "ID Ella"
COL_NOMBRE_1 = "Nombre Ella"
COL_ID_2 = "ID El"
COL_NOMBRE_2 = "Nombre El"
COL_RAZON = "Porque harian buena pareja?"

# --- URL DE TU GOOGLE FORM ---
URL_FORMULARIO = "https://forms.gle/o3kp4N79xSL1bn6E6"

# --- FUNCIONES ---

def cargar_datos():
    """Conecta con Google Sheets y descarga los datos"""
    conn = st.connection("gsheets", type=GSheetsConnection)
    # ttl=3600 hace que se actualice cada minuto para no saturar la API
    return conn.read(worksheet="Respuestas", ttl=3600)

def procesar_ranking(df):
    """Lógica para contar votos normalizando parejas (A+B = B+A)"""
    if df.empty:
        return pd.DataFrame()

    match_data = []

    for index, row in df.iterrows():
        try:
            # Obtenemos datos y limpiamos espacios
            id1 = str(row[COL_ID_1]).strip()
            id2 = str(row[COL_ID_2]).strip()
            nombre1 = str(row[COL_NOMBRE_1]).strip()
            nombre2 = str(row[COL_NOMBRE_2]).strip()
            
            # Normalización: Ordenamos los IDs para crear una clave única
            # Esto asegura que (123, 456) sea lo mismo que (456, 123)
            ids_ordenados = sorted([(id1, nombre1), (id2, nombre2)], key=lambda x: x[0])
            
            pareja_clave = f"{ids_ordenados[0][0]}-{ids_ordenados[1][0]}" # Clave interna (ID-ID)
            pareja_display = f"{ids_ordenados[0][1]} & {ids_ordenados[1][1]}" # Nombre & Nombre
            
            match_data.append({
                "Pareja_ID": pareja_clave,
                "Pareja": pareja_display,
                "Historia": row[COL_RAZON]
            })
        except Exception as e:
            continue # Si hay un error en una fila, la saltamos

    df_matches = pd.DataFrame(match_data)
    
    if df_matches.empty:
        return pd.DataFrame()

    # Contar votos
    conteo = df_matches.groupby(['Pareja_ID', 'Pareja']).size().reset_index(name='Votos')
    conteo = conteo.sort_values(by='Votos', ascending=False)
    
    return conteo

# --- INTERFAZ PRINCIPAL ---

st.title("💘 Matchmaking UP 💘")
st.markdown("### ¿Quiénes se ganarán la cena romántica?")
st.write("Vota por tus amigos (o por ti mismo/a) y ayuda a Cupido a hacer su trabajo.")

# Botón grande para ir al formulario
st.link_button("👉 ¡VOTAR POR UNA PAREJA AHORA! 👈", URL_FORMULARIO, use_container_width=True)

st.divider()

# Cargar datos
try:
    with st.spinner('Contactando a Cupido...'):
        df_raw = cargar_datos()
        ranking = procesar_ranking(df_raw)
        
    if not ranking.empty:
        # --- SECCIÓN DE MÉTRICAS ---
        col1, col2, col3 = st.columns(3)
        
        total_votos = ranking['Votos'].sum()
        pareja_top = ranking.iloc[0]['Pareja']
        votos_top = ranking.iloc[0]['Votos']
        
        col1.metric("Total de Votos", total_votos)
        col2.metric("Pareja Líder", "🥇 Top 1")
        col3.metric("Votos del Líder", votos_top)
        
        st.markdown(f"<div style='text-align: center; color: #D32F2F; font-size: 1.2em; margin-bottom: 20px;'>👑 <b>{pareja_top}</b> 👑</div>", unsafe_allow_html=True)

        # --- RANKING TABLE ---
        st.subheader("🔥 El Top 10 más pedido")
        
        # Configuramos la tabla para que se vea bonita con barras de progreso
        st.dataframe(
            ranking[['Pareja', 'Votos']].head(10),
            column_config={
                "Pareja": st.column_config.TextColumn("Tortolitos", width="medium"),
                "Votos": st.column_config.ProgressColumn(
                    "Popularidad",
                    format="%d ❤️",
                    min_value=0,
                    max_value=int(ranking['Votos'].max()),
                ),
            },
            hide_index=True,
            use_container_width=True
        )
        
        # --- BUSCADOR ---
        st.subheader("🕵️‍♀️ ¿Estás en la lista?")
        busqueda = st.text_input("Escribe un nombre o ID para buscar:")
        
        if busqueda:
            resultados = ranking[ranking['Pareja'].str.contains(busqueda, case=False, na=False)]
            if not resultados.empty:
                st.success(f"¡Sí! Encontramos {len(resultados)} coincidencia(s):")
                st.dataframe(resultados[['Pareja', 'Votos']], hide_index=True)
                st.balloons()
            else:
                st.info("No encontramos coincidencias... ¡Ve al formulario y nomina esa pareja!")

    else:
        st.info("Aún no hay votos. ¡Sé el primero en crear un match!")

except Exception as e:
    st.error(f"Hubo un error de conexión con la base de datos de Cupido: {e}")
    st.info("Verifica que el archivo secrets.toml esté bien configurado.")

st.markdown("---")
st.caption("Hecho con ❤️ para San Valentín UP.")
