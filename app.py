import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
import plotly.express as px
import concurrent.futures
import time
import random

# ==========================================
# 1. CONFIGURACIÓN DEL SISTEMA
# ==========================================
st.set_page_config(
    page_title="Vigilancia Territorial FAU", 
    page_icon="✈️", 
    layout="wide"
)

GA_ID = "G-XXXXXXXXXX" 
ga_script = f"""
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || []; 
  function gtag(){{dataLayer.push(arguments);}} 
  gtag('js', new Date()); 
  gtag('config', '{GA_ID}');
</script>
"""
components.html(ga_script, height=0, width=0)

# ==========================================
# 2. CABECERA INSTITUCIONAL FAU
# ==========================================
col_logo, col_titulo = st.columns([1, 7])

with col_logo:
    st.image("FAU.svg", use_container_width=True)

with col_titulo:
    st.title("Sistema de Vigilancia Territorial")
    st.markdown("**FUERZA AÉREA URUGUAYA** | Plataforma integrada de evaluación operativa.")

st.divider()

# ==========================================
# 3. DICCIONARIOS GEOGRÁFICOS
# ==========================================
monitoreo_hidrico = {
    "Artigas_Cap": {"Ciudad": "Artigas", "Afluente": "Río Cuareim", "lat": -30.40, "lon": -56.46, "coef_v": 1.0},
    "Salto_Cap": {"Ciudad": "Salto", "Afluente": "Río Uruguay", "lat": -31.38, "lon": -57.96, "coef_v": 1.0},
    "Paysandu_Cap": {"Ciudad": "Paysandú", "Afluente": "Río Uruguay", "lat": -32.31, "lon": -58.07, "coef_v": 1.0},
    "RioNegro_FB": {"Ciudad": "Fray Bentos", "Afluente": "Río Uruguay", "lat": -33.13, "lon": -58.29, "coef_v": 0.8},
    "Soriano_Mer": {"Ciudad": "Mercedes", "Afluente": "Río Negro", "lat": -33.25, "lon": -58.02, "coef_v": 0.9},
    "Soriano_Dol": {"Ciudad": "Dolores", "Afluente": "Río San Salvador", "lat": -33.53, "lon": -58.21, "coef_v": 0.9},
    "Durazno_Cap": {"Ciudad": "Durazno", "Afluente": "Río Yí", "lat": -33.38, "lon": -56.52, "coef_v": 1.0},
    "Durazno_Sar": {"Ciudad": "Sarandí del Yí", "Afluente": "Río Yí", "lat": -33.34, "lon": -55.62, "coef_v": 0.9},
    "Tacuarembo_PT": {"Ciudad": "Paso Toros", "Afluente": "Río Negro", "lat": -32.81, "lon": -56.51, "coef_v": 0.7},
    "Florida_Cap": {"Ciudad": "Florida", "Afluente": "Río S. Lucía Chico", "lat": -34.09, "lon": -56.21, "coef_v": 0.9},
    "Florida_25A": {"Ciudad": "25 de Agosto", "Afluente": "Río Santa Lucía", "lat": -34.40, "lon": -56.39, "coef_v": 1.0},
    "Canelones_SL": {"Ciudad": "Santa Lucía", "Afluente": "Río Santa Lucía", "lat": -34.45, "lon": -56.39, "coef_v": 1.0},
    "Canelones_SR": {"Ciudad": "San Ramón", "Afluente": "Río Santa Lucía", "lat": -34.30, "lon": -55.96, "coef_v": 0.9},
    "SanJose_Cap": {"Ciudad": "San José", "Afluente": "Río San José", "lat": -34.33, "lon": -56.71, "coef_v": 0.9},
    "Treinta_Cap": {"Ciudad": "Treinta y Tres", "Afluente": "Río Olimar", "lat": -33.23, "lon": -54.38, "coef_v": 1.0},
    "CerroL_Melo": {"Ciudad": "Melo", "Afluente": "Arroyo Conventos", "lat": -32.36, "lon": -54.16, "coef_v": 0.8},
    "CerroL_RB": {"Ciudad": "Río Branco", "Afluente": "Río Yaguarón", "lat": -32.59, "lon": -53.39, "coef_v": 0.9},
    "Rocha_Cap": {"Ciudad": "Rocha", "Afluente": "Arroyo Rocha", "lat": -34.48, "lon": -54.33, "coef_v": 0.8},
    "Maldonado_SC": {"Ciudad": "San Carlos", "Afluente": "A. San Carlos", "lat": -34.80, "lon": -54.92, "coef_v": 0.8},
    "Lavalleja_Min": {"Ciudad": "Minas", "Afluente": "A. San Francisco", "lat": -34.37, "lon": -55.23, "coef_v": 0.7}
}

monitoreo_fuego = {
    "Artigas": {"lat": -30.40, "lon": -56.46, "coef_a": 0.7}, 
    "Canelones": {"lat": -34.52, "lon": -55.93, "coef_a": 0.5},
    "Melo": {"lat": -32.36, "lon": -54.16, "coef_a": 0.7}, 
    "Colonia": {"lat": -34.46, "lon": -57.83, "coef_a": 0.5},
    "Durazno": {"lat": -33.38, "lon": -56.52, "coef_a": 0.6}, 
    "Trinidad": {"lat": -33.51, "lon": -56.89, "coef_a": 0.6},
    "Florida": {"lat": -34.09, "lon": -56.21, "coef_a": 0.6}, 
    "Minas": {"lat": -34.37, "lon": -55.23, "coef_a": 0.9},
    "Maldonado": {"lat": -34.90, "lon": -54.95, "coef_a": 0.4}, 
    "Piriápolis": {"lat": -34.86, "lon": -55.27, "coef_a": 0.9},
    "Montevideo": {"lat": -34.90, "lon": -56.16, "coef_a": 0.2}, 
    "Paysandú": {"lat": -32.31, "lon": -58.07, "coef_a": 0.5},
    "Fray Bentos": {"lat": -33.13, "lon": -58.29, "coef_a": 0.6}, 
    "Rivera": {"lat": -30.90, "lon": -55.53, "coef_a": 0.7},
    "Tranqueras": {"lat": -31.20, "lon": -55.75, "coef_a": 1.0}, 
    "Rocha": {"lat": -34.48, "lon": -54.33, "coef_a": 0.7},
    "P. del Diablo": {"lat": -34.04, "lon": -53.54, "coef_a": 1.0}, 
    "Salto": {"lat": -31.38, "lon": -57.96, "coef_a": 0.5},
    "San José": {"lat": -34.33, "lon": -56.71, "coef_a": 0.5}, 
    "Mercedes": {"lat": -33.25, "lon": -58.02, "coef_a": 0.5},
    "Tacuarembó": {"lat": -31.71, "lon": -55.98, "coef_a": 0.8}, 
    "Treinta y Tres": {"lat": -33.23, "lon": -54.38, "coef_a": 0.7}
}

# ==========================================
# 4. MOTORES DE EXTRACCIÓN METEOROLÓGICA
# ==========================================
def fetch_hidrico(info):
    try:
        time.sleep(random.uniform(0.1, 0.7)) 
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": info["lat"], 
            "longitude": info["lon"], 
            "past_days": 14, 
            "forecast_days": 3, 
            "daily": ["precipitation_sum"], 
            "timezone": "America/Montevideo"
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200: 
            raise ValueError
            
        df_c = pd.DataFrame(resp.json().get("daily", {}))
        ll_pasada = df_c['precipitation_sum'].fillna(0).iloc[:-3].sum()
        ll_futura = df_c['precipitation_sum'].fillna(0).iloc[-3:].sum()
        idx = ((ll_pasada * 0.3) + (ll_futura * 0.7)) * info["coef_v"]
        
        if idx < 15: cat = "Normal"
        elif idx <= 35: cat = "Alerta Amarilla"
        elif idx <= 70: cat = "Alerta Naranja"
        else: cat = "Alerta Roja"
        
        return {
            "Ciudad": info["Ciudad"], 
            "Afluente": info["Afluente"], 
            "Latitud": info["lat"], 
            "Longitud": info["lon"], 
            "Lluvia_14d": round(ll_pasada,1), 
            "Pronostico_3d": round(ll_futura,1), 
            "Indice": round(idx,2), 
            "Categoria": cat
        }
    except:
        return {
            "Ciudad": info["Ciudad"], 
            "Afluente": info["Afluente"], 
            "Latitud": info["lat"], 
            "Longitud": info["lon"], 
            "Lluvia_14d": 0, 
            "Pronostico_3d": 0, 
            "Indice": 0, 
            "Categoria": "Sin Datos"
        }

def fetch_fuego(ciudad, info):
    try:
        time.sleep(random.uniform(0.1, 0.7))
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": info["lat"], 
            "longitude": info["lon"], 
            "past_days": 90, 
            "forecast_days": 1, 
            "daily": ["temperature_2m_max", "relative_humidity_2m_min", "precipitation_sum"], 
            "timezone": "America/Montevideo"
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200: 
            raise ValueError
            
        df_c = pd.DataFrame(resp.json().get("daily", {}))
        df_c = df_c.sort_values(by='time', ascending=False).reset_index(drop=True)
        prec = df_c['precipitation_sum'].fillna(0).values
        
        precip_total_90d = np.sum(prec)
        p = [np.sum(prec[0:i]) for i in [1, 2, 3, 4, 5, 10, 15, 30, 60, 90]]
        
        exps = [-0.14, -0.07, -0.04, -0.03, -0.02, -0.01, -0.008, -0.004, -0.002, -0.001]
        fps = [np.exp(exps[0] * p[0])] + [np.exp(exps[i] * (p[i] - p[i-1])) for i in range(1, 10)]
        PSE = 105 * np.prod(fps)
        
        RFO = (0.9 * (1 + np.sin(np.radians((info["coef_a"] * 1.72 * PSE - 90)))) / 2) * \
              (-0.006 * df_c['relative_humidity_2m_min'].ffill().iloc[0] + 1.3) * \
              (0.02 * df_c['temperature_2m_max'].ffill().iloc[0] + 0.4)
        
        if RFO < 0.15: cat = "Mínimo"
        elif RFO <= 0.40: cat = "Bajo"
        elif RFO <= 0.70: cat = "Medio"
        elif RFO <= 0.95: cat = "Alto"
        else: cat = "Crítico"
        
        return {
            "Ciudad": ciudad, 
            "Latitud": info["lat"], 
            "Longitud": info["lon"], 
            "PSE": round(PSE,2), 
            "RFO": round(RFO,4), 
            "Precip_90d": round(precip_total_90d, 1),
            "Categoria": cat
        }
    except:
        return {
            "Ciudad": ciudad, 
            "Latitud": info["lat"], 
            "Longitud": info["lon"], 
            "PSE": 0, 
            "RFO": 0, 
            "Precip_90d": 0,
            "Categoria": "Sin Datos"
        }

@st.cache_data(ttl=3600)
def obtener_datos_completos():
    r_agua = []
    r_fuego = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        f_agua = [executor.submit(fetch_hidrico, i) for k, i in monitoreo_hidrico.items()]
        for f in concurrent.futures.as_completed(f_agua): 
            r_agua.append(f.result())
            
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        f_fuego = [executor.submit(fetch_fuego, c, i) for c, i in monitoreo_fuego.items()]
        for f in concurrent.futures.as_completed(f_fuego): 
            r_fuego.append(f.result())
            
    return pd.DataFrame(r_agua), pd.DataFrame(r_fuego)


# ==========================================
# 5. PANELES DE CONTROL (FRONT-END)
# ==========================================
with st.spinner('Sincronizando modelos de Open-Meteo...'):
    df_inundacion, df_fuego = obtener_datos_completos()

tab_agua, tab_fuego = st.tabs(["💧 EVALUACIÓN HÍDRICA", "🌲 VULNERABILIDAD FORESTAL"])

# --- PESTAÑA 1: INUNDACIONES ---
with tab_agua:
    if "Sin Datos" in df_inundacion["Categoria"].values: 
        st.warning("Aviso: Disrupción temporal en algunas localidades.")
    
    st.markdown("#### Análisis de Cuencas Global")
    fig_agua = px.scatter(
        df_inundacion, 
        x="Lluvia_14d", 
        y="Pronostico_3d", 
        color="Categoria", 
        hover_name="Ciudad", 
        hover_data=["Afluente", "Indice"],
        color_discrete_map={
            "Normal": "#10B981", 
            "Alerta Amarilla": "#FBBF24", 
            "Alerta Naranja": "#F97316", 
            "Alerta Roja": "#DC2626", 
            "Sin Datos": "#94A3B8"
        }, 
        height=300, 
        template="plotly_white"
    )
    st.plotly_chart(fig_agua, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Mapa de Índice de Inundación")
        mapa_indice_agua = folium.Map(location=[-32.5, -56.0], zoom_start=6, tiles="CartoDB positron")
        colores_agua = {"Normal": "green", "Alerta Amarilla": "orange", "Alerta Naranja": "red", "Alerta Roja": "darkred", "Sin Datos": "gray"}
        
        for idx, fila in df_inundacion.iterrows():
            folium.CircleMarker(
                location=[fila['Latitud'], fila['Longitud']], 
                radius=10,
                tooltip=f"<b>{fila['Ciudad']}</b><br>Índice: {fila['Indice']}<br>Situación: <b>{fila['Categoria']}</b>",
                color=colores_agua.get(fila['Categoria'], "gray"), fill=True, fill_opacity=0.7
            ).add_to(mapa_indice_agua)
            
            folium.Marker(
                location=[fila['Latitud'], fila['Longitud']],
                icon=folium.DivIcon(html=f'<div style="font-size: 11pt; font-weight: bold; color: #1E293B; text-shadow: 1px 1px 3px white; margin-left: 15px; margin-top: -10px;">{fila["Indice"]}</div>')
            ).add_to(mapa_indice_agua)
        components.html(mapa_indice_agua._repr_html_(), height=450)
        
    with col2:
        st.markdown("#### Mapa Satelital Infrarrojo (GOES-16)")
        mapa_meteo = folium.Map(location=[-32.5, -56.0], zoom_start=6, tiles="CartoDB dark_matter")
        
        # INYECCIÓN DEL SATÉLITE GOES-16 (IEM WMS)
        folium.WmsTileLayer(
            url="https://mesonet.agron.iastate.edu/cgi-bin/wms/goes/conus_ir.cgi",
            layers="goes_conus_ir",
            name="Satélite GOES-16 (IR)",
            attr="Iowa Environmental Mesonet (IEM)",
            format="image/png",
            transparent=True,
            overlay=True,
            control=True,
            opacity=0.5
        ).add_to(mapa_meteo)
            
        for idx, fila in df_inundacion.iterrows():
            folium.CircleMarker(
                location=[fila['Latitud'], fila['Longitud']], 
                radius=6,
                tooltip=f"<b>{fila['Ciudad']}</b><br>Lluvia pasada: {fila['Lluvia_14d']} mm<br>Pronóstico 3d: {fila['Pronostico_3d']} mm",
                color="#3B82F6", fill=True, fill_opacity=0.5
            ).add_to(mapa_meteo)
        
        folium.LayerControl().add_to(mapa_meteo)
        components.html(mapa_meteo._repr_html_(), height=450)

# --- PESTAÑA 2: INCENDIOS ---
with tab_fuego:
    if "Sin Datos" in df_fuego["Categoria"].values: 
        st.warning("Aviso: Disrupción temporal en algunas localidades.")
    
    st.markdown("#### Índice de Vulnerabilidad Forestal (RFO)")
    fig_fuego = px.scatter(
        df_fuego, 
        x="PSE", 
        y="RFO", 
        color="Categoria", 
        hover_name="Ciudad",
        color_discrete_map={
            "Mínimo": "#10B981", 
            "Bajo": "#3B82F6", 
            "Medio": "#FBBF24", 
            "Alto": "#F97316", 
            "Crítico": "#DC2626", 
            "Sin Datos": "#94A3B8"
        }, 
        height=300, 
        template="plotly_white"
    )
    st.plotly_chart(fig_fuego, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("#### Mapa de Índice (RFO) y Satélite GOES-16")
        mapa_fuego = folium.Map(location=[-32.5, -56.0], zoom_start=6, tiles="CartoDB dark_matter")
        colores_fuego = {"Mínimo": "green", "Bajo": "blue", "Medio": "orange", "Alto": "red", "Crítico": "darkred", "Sin Datos": "gray"}
        
        # INYECCIÓN DEL SATÉLITE GOES-16 (IEM WMS) también en incendios
        folium.WmsTileLayer(
            url="https://mesonet.agron.iastate.edu/cgi-bin/wms/goes/conus_ir.cgi",
            layers="goes_conus_ir",
            name="Satélite GOES-16 (IR)",
            attr="Iowa Environmental Mesonet (IEM)",
            format="image/png",
            transparent=True,
            overlay=True,
            control=True,
            opacity=0.5
        ).add_to(mapa_fuego)
        
        for idx, fila in df_fuego.iterrows():
            folium.CircleMarker(
                location=[fila['Latitud'], fila['Longitud']], 
                radius=9,
                tooltip=f"<b>{fila['Ciudad']}</b><br>RFO: {fila['RFO']}<br>Nivel: <b>{fila['Categoria']}</b>",
                color=colores_fuego.get(fila['Categoria'], "gray"), fill=True, fill_opacity=0.7
            ).add_to(mapa_fuego)
            
        folium.LayerControl().add_to(mapa_fuego)
        components.html(mapa_fuego._repr_html_(), height=450)
        
    with col4:
        st.markdown("#### Mapa de Calor (Estrés Hídrico/Sequía)")
        mapa_calor = folium.Map(location=[-32.5, -56.0], zoom_start=6, tiles="CartoDB dark_matter")
        
        lluvia_maxima = df_fuego['Precip_90d'].max()
        df_fuego['Peso_Sequia'] = df_fuego['Precip_90d'].apply(lambda x: lluvia_maxima - x + 10)
        
        heat_data = [[row['Latitud'], row['Longitud'], row['Peso_Sequia']] for idx, row in df_fuego.iterrows()]
        
        HeatMap(
            heat_data,
            radius=35,
            blur=25,
            gradient={0.2: 'blue', 0.4: 'cyan', 0.6: 'lime', 0.8: 'yellow', 1.0: 'red'}
        ).add_to(mapa_calor)
        
        components.html(mapa_calor._repr_html_(), height=450)
