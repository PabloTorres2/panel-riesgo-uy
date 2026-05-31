import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import numpy as np
import folium
import plotly.express as px
import concurrent.futures

# ==========================================
# 1. CONFIGURACIÓN DEL SISTEMA Y ESTILOS (UI)
# ==========================================
st.set_page_config(page_title="Sistema de Alerta FAU", page_icon="✈️", layout="wide")

# --- Inyección de CSS Institucional (Fuerza Aérea & Ambiental) ---
css_institucional = """
<style>
    /* Estilo general del fondo y texto */
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* Personalización de las Pestañas (Tabs) */
    div[data-baseweb="tab-list"] {
        gap: 15px;
        background-color: transparent;
    }
    div[data-baseweb="tab"] {
        height: 55px;
        background-color: #1B2A47; /* Azul oscuro institucional FAU */
        color: #FFFFFF !important;
        border-radius: 8px;
        padding: 10px 24px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        border: 1px solid #2C3E50;
    }
    div[data-baseweb="tab"]:hover {
        background-color: #2C3E50;
        transform: translateY(-2px);
    }
    div[aria-selected="true"] {
        background-color: #047857 !important; /* Verde ambiental activo */
        border: 2px solid #34D399 !important;
        box-shadow: 0 0 15px rgba(4, 120, 87, 0.4);
    }
    
    /* Tarjetas de los gráficos */
    .css-1r6slb0, .css-18e3th9 {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
</style>
"""
st.markdown(css_institucional, unsafe_allow_html=True)

# Google Analytics
GA_ID = "G-XXXXXXXXXX" 
ga_script = f"""<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script><script>window.dataLayer = window.dataLayer || []; function gtag(){{dataLayer.push(arguments);}} gtag('js', new Date()); gtag('config', '{GA_ID}');</script>"""
components.html(ga_script, height=0, width=0)

# ==========================================
# 2. DICCIONARIOS GEOGRÁFICOS
# ==========================================
monitoreo_hidrico = {
    "Artigas_Capital": {"Ciudad": "Artigas", "Afluente": "Río Cuareim", "lat": -30.40, "lon": -56.46, "coef_v": 1.0},
    "Salto_Capital": {"Ciudad": "Salto", "Afluente": "Río Uruguay", "lat": -31.38, "lon": -57.96, "coef_v": 1.0},
    "Paysandu_Capital": {"Ciudad": "Paysandú", "Afluente": "Río Uruguay", "lat": -32.31, "lon": -58.07, "coef_v": 1.0},
    "RioNegro_FrayBentos": {"Ciudad": "Fray Bentos", "Afluente": "Río Uruguay", "lat": -33.13, "lon": -58.29, "coef_v": 0.8},
    "Soriano_Mercedes": {"Ciudad": "Mercedes", "Afluente": "Río Negro", "lat": -33.25, "lon": -58.02, "coef_v": 0.9},
    "Soriano_Dolores": {"Ciudad": "Dolores", "Afluente": "Río San Salvador", "lat": -33.53, "lon": -58.21, "coef_v": 0.9},
    "Durazno_Capital": {"Ciudad": "Durazno", "Afluente": "Río Yí", "lat": -33.38, "lon": -56.52, "coef_v": 1.0},
    "Durazno_SarandiDelYi": {"Ciudad": "Sarandí del Yí", "Afluente": "Río Yí", "lat": -33.34, "lon": -55.62, "coef_v": 0.9},
    "Tacuarembo_PasoDeLosToros": {"Ciudad": "Paso de los Toros", "Afluente": "Río Negro", "lat": -32.81, "lon": -56.51, "coef_v": 0.7},
    "Florida_Capital": {"Ciudad": "Florida", "Afluente": "Río Santa Lucía Chico", "lat": -34.09, "lon": -56.21, "coef_v": 0.9},
    "Florida_25DeAgosto": {"Ciudad": "25 de Agosto", "Afluente": "Río Santa Lucía", "lat": -34.40, "lon": -56.39, "coef_v": 1.0},
    "Canelones_SantaLucia": {"Ciudad": "Santa Lucía", "Afluente": "Río Santa Lucía", "lat": -34.45, "lon": -56.39, "coef_v": 1.0},
    "Canelones_SanRamon": {"Ciudad": "San Ramón", "Afluente": "Río Santa Lucía", "lat": -34.30, "lon": -55.96, "coef_v": 0.9},
    "SanJose_Capital": {"Ciudad": "San José de Mayo", "Afluente": "Río San José", "lat": -34.33, "lon": -56.71, "coef_v": 0.9},
    "TreintaYTres_Capital": {"Ciudad": "Treinta y Tres", "Afluente": "Río Olimar", "lat": -33.23, "lon": -54.38, "coef_v": 1.0},
    "CerroLargo_Melo": {"Ciudad": "Melo", "Afluente": "Arroyo Conventos", "lat": -32.36, "lon": -54.16, "coef_v": 0.8},
    "CerroLargo_RioBranco": {"Ciudad": "Río Branco", "Afluente": "Río Yaguarón", "lat": -32.59, "lon": -53.39, "coef_v": 0.9},
    "Rocha_Capital": {"Ciudad": "Rocha", "Afluente": "Arroyo Rocha", "lat": -34.48, "lon": -54.33, "coef_v": 0.8},
    "Maldonado_SanCarlos": {"Ciudad": "San Carlos", "Afluente": "Arroyo San Carlos", "lat": -34.80, "lon": -54.92, "coef_v": 0.8},
    "Lavalleja_Minas": {"Ciudad": "Minas", "Afluente": "Arroyo San Francisco", "lat": -34.37, "lon": -55.23, "coef_v": 0.7}
}

monitoreo_fuego = {
    "Artigas": {"lat": -30.40, "lon": -56.46, "coef_a": 0.7}, "Canelones": {"lat": -34.52, "lon": -55.93, "coef_a": 0.5},
    "Melo": {"lat": -32.36, "lon": -54.16, "coef_a": 0.7}, "Colonia": {"lat": -34.46, "lon": -57.83, "coef_a": 0.5},
    "Durazno": {"lat": -33.38, "lon": -56.52, "coef_a": 0.6}, "Trinidad": {"lat": -33.51, "lon": -56.89, "coef_a": 0.6},
    "Florida": {"lat": -34.09, "lon": -56.21, "coef_a": 0.6}, "Minas": {"lat": -34.37, "lon": -55.23, "coef_a": 0.9},
    "Maldonado": {"lat": -34.90, "lon": -54.95, "coef_a": 0.4}, "Piriápolis": {"lat": -34.86, "lon": -55.27, "coef_a": 0.9},
    "Montevideo": {"lat": -34.90, "lon": -56.16, "coef_a": 0.2}, "Paysandú": {"lat": -32.31, "lon": -58.07, "coef_a": 0.5},
    "Fray Bentos": {"lat": -33.13, "lon": -58.29, "coef_a": 0.6}, "Rivera": {"lat": -30.90, "lon": -55.53, "coef_a": 0.7},
    "Tranqueras": {"lat": -31.20, "lon": -55.75, "coef_a": 1.0}, "Rocha": {"lat": -34.48, "lon": -54.33, "coef_a": 0.7},
    "Punta del Diablo": {"lat": -34.04, "lon": -53.54, "coef_a": 1.0}, "Salto": {"lat": -31.38, "lon": -57.96, "coef_a": 0.5},
    "San José": {"lat": -34.33, "lon": -56.71, "coef_a": 0.5}, "Mercedes": {"lat": -33.25, "lon": -58.02, "coef_a": 0.5},
    "Tacuarembó": {"lat": -31.71, "lon": -55.98, "coef_a": 0.8}, "Treinta y Tres": {"lat": -33.23, "lon": -54.38, "coef_a": 0.7}
}

# ==========================================
# 3. MOTORES DE EXTRACCIÓN (HILOS PARALELOS)
# ==========================================
def fetch_hidrico(info):
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {"latitude": info["lat"], "longitude": info["lon"], "past_days": 14, "forecast_days": 3, "daily": ["precipitation_sum"], "timezone": "America/Montevideo"}
        resp = requests.get(url, params=params, timeout=4)
        if resp.status_code != 200: raise ValueError
        df_c = pd.DataFrame(resp.json().get("daily", {}))
        ll_pasada = df_c['precipitation_sum'].fillna(0).iloc[:-3].sum()
        ll_futura = df_c['precipitation_sum'].fillna(0).iloc[-3:].sum()
        idx = ((ll_pasada * 0.3) + (ll_futura * 0.7)) * info["coef_v"]
        
        if idx < 15: cat = "Normal"
        elif idx <= 35: cat = "Alerta Amarilla"
        elif idx <= 70: cat = "Alerta Naranja"
        else: cat = "Alerta Roja"
        return {"Ciudad": info["Ciudad"], "Afluente": info["Afluente"], "Latitud": info["lat"], "Longitud": info["lon"], "Lluvia_14d": round(ll_pasada,1), "Pronostico_3d": round(ll_futura,1), "Indice": round(idx,2), "Categoria": cat}
    except:
        return {"Ciudad": info["Ciudad"], "Afluente": info["Afluente"], "Latitud": info["lat"], "Longitud": info["lon"], "Lluvia_14d": 0, "Pronostico_3d": 0, "Indice": 0, "Categoria": "Sin Datos"}

def fetch_fuego(ciudad, info):
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {"latitude": info["lat"], "longitude": info["lon"], "past_days": 90, "forecast_days": 1, "daily": ["temperature_2m_max", "relative_humidity_2m_min", "precipitation_sum"], "timezone": "America/Montevideo"}
        resp = requests.get(url, params=params, timeout=4)
        if resp.status_code != 200: raise ValueError
        df_c = pd.DataFrame(resp.json().get("daily", {}))
        df_c = df_c.sort_values(by='time', ascending=False).reset_index(drop=True)
        prec = df_c['precipitation_sum'].fillna(0).values
        p = [np.sum(prec[0:i]) for i in [1, 2, 3, 4, 5, 10, 15, 30, 60, 90]]
        exps = [-0.14, -0.07, -0.04, -0.03, -0.02, -0.01, -0.008, -0.004, -0.002, -0.001]
        fps = [np.exp(exps[0] * p[0])] + [np.exp(exps[i] * (p[i] - p[i-1])) for i in range(1, 10)]
        PSE = 105 * np.prod(fps)
        RFO = (0.9 * (1 + np.sin(np.radians((info["coef_a"] * 1.72 * PSE - 90)))) / 2) * (-0.006 * df_c['relative_humidity_2m_min'].ffill().iloc[0] + 1.3) * (0.02 * df_c['temperature_2m_max'].ffill().iloc[0] + 0.4)
        
        if RFO < 0.15: cat = "Mínimo"
        elif RFO <= 0.40: cat = "Bajo"
        elif RFO <= 0.70: cat = "Medio"
        elif RFO <= 0.95: cat = "Alto"
        else: cat = "Crítico"
        return {"Ciudad": ciudad, "Latitud": info["lat"], "Longitud": info["lon"], "PSE": round(PSE,2), "RFO": round(RFO,4), "Categoria": cat}
    except:
        return {"Ciudad": ciudad, "Latitud": info["lat"], "Longitud": info["lon"], "PSE": 0, "RFO": 0, "Categoria": "Sin Datos"}

@st.cache_data(ttl=3600)
def obtener_datos_completos():
    r_agua, r_fuego = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        f_agua = [executor.submit(fetch_hidrico, i) for k, i in monitoreo_hidrico.items()]
        for f in concurrent.futures.as_completed(f_agua): r_agua.append(f.result())
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        f_fuego = [executor.submit(fetch_fuego, c, i) for c, i in monitoreo_fuego.items()]
        for f in concurrent.futures.as_completed(f_fuego): r_fuego.append(f.result())
    return pd.DataFrame(r_agua), pd.DataFrame(r_fuego)

# ==========================================
# 4. INTERFAZ PRINCIPAL INSTITUCIONAL
# ==========================================

# Cabecera con imagen ilustrativa genérica de operaciones aéreas/ambientales
# (Puedes reemplazar el link de la imagen por el logo de la FAU u otro gráfico)
col_img, col_txt = st.columns([1, 4])
with col_img:
    st.image("https://images.unsplash.com/photo-1579607590892-0b19b6eb8236?q=80&w=250&auto=format&fit=crop", use_container_width=True)
with col_txt:
    st.title("Sistema de Vigilancia Territorial")
    st.markdown("Plataforma integrada de evaluación de riesgos ambientales para el despliegue de unidades aéreas y terrestres.")

st.divider()

# Extracción de datos
with st.spinner('Sincronizando modelos meteorológicos globales...'):
    df_inundacion, df_fuego = obtener_datos_completos()

# Creación de las pestañas estilizadas
tab_agua, tab_fuego = st.tabs(["💧 MODELO HÍDRICO (Riesgo de Inundación)", "🌲 MODELO FORESTAL (Riesgo de Incendio)"])

# --- PESTAÑA 1: INUNDACIONES ---
with tab_agua:
    if "Sin Datos" in df_inundacion["Categoria"].values: st.warning("Aviso de Sistema: Disrupción temporal con enlace satelital en algunas áreas.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Evaluación de Cuencas")
        fig_agua = px.scatter(df_inundacion, x="Lluvia_14d", y="Pronostico_3d", color="Categoria", hover_name="Ciudad", hover_data=["Afluente", "Indice"],
            color_discrete_map={"Normal": "#10B981", "Alerta Amarilla": "#FBBF24", "Alerta Naranja": "#F97316", "Alerta Roja": "#DC2626", "Sin Datos": "#94A3B8"}, height=400)
        fig_agua.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_agua, use_container_width=True)
    
    with col2:
        st.subheader("Despliegue Geográfico Hídrico")
        mapa_agua = folium.Map(location=[-32.5, -56.0], zoom_start=6, tiles="CartoDB positron")
        colores_agua = {"Normal": "green", "Alerta Amarilla": "orange", "Alerta Naranja": "red", "Alerta Roja": "darkred", "Sin Datos": "gray"}
        
        for idx, fila in df_inundacion.iterrows():
            folium.CircleMarker(location=[fila['Latitud'], fila['Longitud']], radius=10,
                tooltip=f"<b>{fila['Ciudad']}</b><br>Río: {fila['Afluente']}<br>Índice: {fila['Indice']}<br>Situación: <b>{fila['Categoria']}</b>",
                color=colores_agua.get(fila['Categoria'], "gray"), fill=True, fill_opacity=0.7).add_to(mapa_agua)
            folium.Marker(location=[fila['Latitud'], fila['Longitud']],
                icon=folium.DivIcon(html=f'<div style="font-size: 11pt; font-weight: bold; color: #1E293B; text-shadow: 1px 1px 3px white; margin-left: 15px; margin-top: -10px;">{fila["Indice"]}</div>')
            ).add_to(mapa_agua)
        components.html(mapa_agua._repr_html_(), height=500)

# --- PESTAÑA 2: INCENDIOS ---
with tab_fuego:
    if "Sin Datos" in df_fuego["Categoria"].values: st.warning("Aviso de Sistema: Disrupción temporal con enlace satelital en algunas áreas.")
    
    col3, col4 = st.columns([1, 2])
    with col3:
        st.subheader("Índice de Vulnerabilidad Forestal")
        fig_fuego = px.scatter(df_fuego, x="PSE", y="RFO", color="Categoria", hover_name="Ciudad",
            color_discrete_map={"Mínimo": "#10B981", "Bajo": "#3B82F6", "Medio": "#FBBF24", "Alto": "#F97316", "Crítico": "#DC2626", "Sin Datos": "#94A3B8"}, height=400)
        fig_fuego.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_fuego, use_container_width=True)
    
    with col4:
        st.subheader("Cartografía de Riesgo (RFO)")
        mapa_fuego = folium.Map(location=[-32.5, -56.0], zoom_start=6, tiles="CartoDB positron")
        colores_fuego = {"Mínimo": "green", "Bajo": "blue", "Medio": "orange", "Alto": "red", "Crítico": "darkred", "Sin Datos": "gray"}
        
        for idx, fila in df_fuego.iterrows():
            folium.CircleMarker(location=[fila['Latitud'], fila['Longitud']], radius=9,
                tooltip=f"<b>{fila['Ciudad']}</b><br>RFO: {fila['RFO']}<br>Nivel: <b>{fila['Categoria']}</b>",
                color=colores_fuego.get(fila['Categoria'], "gray"), fill=True, fill_opacity=0.7).add_to(mapa_fuego)
        components.html(mapa_fuego._repr_html_(), height=500)
