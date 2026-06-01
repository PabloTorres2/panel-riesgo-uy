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
import os
import math
from datetime import datetime
import geopandas as gpd
from shapely.geometry import Point

# ==========================================
# 1. CONFIGURACIÓN DEL SISTEMA
# ==========================================
st.set_page_config(
    page_title="Vigilancia Territorial FAU", 
    page_icon="✈️", 
    layout="wide"
)

GA_ID = "G-7F3944JTSG" 
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
    st.markdown("**FUERZA AÉREA URUGUAYA** | Plataforma C4ISR de evaluación operativa.")

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
    "Artigas": {"lat": -30.40, "lon": -56.46, "coef_a": 0.7}, "Canelones": {"lat": -34.52, "lon": -55.93, "coef_a": 0.5},
    "Melo": {"lat": -32.36, "lon": -54.16, "coef_a": 0.7}, "Colonia": {"lat": -34.46, "lon": -57.83, "coef_a": 0.5},
    "Durazno": {"lat": -33.38, "lon": -56.52, "coef_a": 0.6}, "Trinidad": {"lat": -33.51, "lon": -56.89, "coef_a": 0.6},
    "Florida": {"lat": -34.09, "lon": -56.21, "coef_a": 0.6}, "Minas": {"lat": -34.37, "lon": -55.23, "coef_a": 0.9},
    "Maldonado": {"lat": -34.90, "lon": -54.95, "coef_a": 0.4}, "Piriápolis": {"lat": -34.86, "lon": -55.27, "coef_a": 0.9},
    "Montevideo": {"lat": -34.90, "lon": -56.16, "coef_a": 0.2}, "Paysandú": {"lat": -32.31, "lon": -58.07, "coef_a": 0.5},
    "Fray Bentos": {"lat": -33.13, "lon": -58.29, "coef_a": 0.6}, "Rivera": {"lat": -30.90, "lon": -55.53, "coef_a": 0.7},
    "Tranqueras": {"lat": -31.20, "lon": -55.75, "coef_a": 1.0}, "Rocha": {"lat": -34.48, "lon": -54.33, "coef_a": 0.7},
    "P. del Diablo": {"lat": -34.04, "lon": -53.54, "coef_a": 1.0}, "Salto": {"lat": -31.38, "lon": -57.96, "coef_a": 0.5},
    "San José": {"lat": -34.33, "lon": -56.71, "coef_a": 0.5}, "Mercedes": {"lat": -33.25, "lon": -58.02, "coef_a": 0.5},
    "Tacuarembó": {"lat": -31.71, "lon": -55.98, "coef_a": 0.8}, "Treinta y Tres": {"lat": -33.23, "lon": -54.38, "coef_a": 0.7}
}

# ==========================================
# 4. MOTORES GEOESPACIALES E INTELIGENCIA
# ==========================================

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class FirmsProvider:
    def __init__(self):
        self.url_base = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_South_America_24h.csv"
        self.cache_file = "firms_24h_cache.csv"
        self.geo_fallback_url = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/URY.geo.json"
        
    def clasificar_frp(self, frp):
        try:
            val = float(frp)
            if val < 10: return "BAJO", "orange"
            elif val < 50: return "MODERADO", "lightred"
            elif val < 200: return "ALTO", "red"
            else: return "SEVERO", "darkred"
        except:
            return "DESCONOCIDO", "gray"

    def obtener_focos(self):
        focos_originales = 0
        tipo_filtro = "Fallido"
        
        try:
            df = pd.read_csv(self.url_base)
            df.to_csv(self.cache_file, index=False)
        except Exception:
            if os.path.exists(self.cache_file):
                df = pd.read_csv(self.cache_file)
            else:
                return pd.DataFrame(), 0, "Sin Datos"

        df['frp'] = pd.to_numeric(df.get('frp', 0), errors='coerce').fillna(0)
        
        df_bbox = df[(df['latitude'] >= -36.0) & (df['latitude'] <= -29.0) & 
                     (df['longitude'] >= -59.0) & (df['longitude'] <= -52.0)].copy()
        focos_originales = len(df_bbox)

        try:
            gdf = gpd.GeoDataFrame(df_bbox, geometry=gpd.points_from_xy(df_bbox.longitude, df_bbox.latitude), crs="EPSG:4326")
            
            if os.path.exists("uruguay.gpkg"):
                uruguay = gpd.read_file("uruguay.gpkg")
                tipo_filtro = "GeoPackage Local (.gpkg)"
            else:
                uruguay = gpd.read_file(self.geo_fallback_url)
                tipo_filtro = "GeoJSON Redundante (API)"

            df_uy = gdf[gdf.within(uruguay.unary_union)].copy()
            
        except Exception:
            df_uy = df_bbox.copy()
            tipo_filtro = "Bounding Box (Emergencia)"
            
        if not df_uy.empty:
            df_uy[['Nivel_FRP', 'Color_FRP']] = df_uy.apply(
                lambda row: pd.Series(self.clasificar_frp(row['frp'])), axis=1
            )
            
        return df_uy, focos_originales, tipo_filtro

class MotorInteligencia:
    def __init__(self):
        self.infra_critica = {
            "aerodromos": [{"nombre": "Base Aérea", "lat": -34.8, "lon": -56.0}],
            "rutas": [{"nombre": "Ruta Nacional", "lat": -33.0, "lon": -56.0}],
            "subestaciones": [{"nombre": "Subestación UTE", "lat": -34.0, "lon": -56.2}],
            "poblados": [{"nombre": "Centro Poblado", "lat": -33.5, "lon": -56.5}]
        }

    def buscar_infraestructura_cercana(self, lat_foco, lon_foco):
        reporte = {}
        for categoria, items in self.infra_critica.items():
            distancias = []
            for item in items:
                dist = haversine(lat_foco, lon_foco, item["lat"], item["lon"])
                distancias.append((dist, item["nombre"]))
            distancias.sort(key=lambda x: x[0])
            reporte[categoria] = distancias[0] if distancias else (999, "N/A")
        return reporte

    def obtener_rfo_local_dinamico(self, lat, lon, df_rfo_base):
        if df_rfo_base.empty: return 0.8
        df_calc = df_rfo_base.copy()
        df_calc["dist_sq"] = (df_calc["Latitud"] - lat)**2 + (df_calc["Longitud"] - lon)**2
        return df_calc.loc[df_calc["dist_sq"].idxmin(), "RFO"]

    def calcular_prioridad_operacional(self, frp, rfo, distancias):
        frp_norm = min(float(frp) / 200.0, 1.0)
        amenaza = (rfo * 0.4) + (frp_norm * 0.6)
        
        exposicion = 0.0
        if distancias["poblados"][0] < 10: exposicion += 0.5
        if distancias["subestaciones"][0] < 5: exposicion += 0.3
        if distancias["rutas"][0] < 2: exposicion += 0.1
        if distancias["aerodromos"][0] < 15: exposicion += 0.1
        if exposicion == 0: exposicion = 0.1 
        
        prioridad_final = amenaza * exposicion * 100
        
        if prioridad_final > 75: return "ALTA", "red", round(prioridad_final, 1)
        elif prioridad_final > 35: return "MODERADA", "orange", round(prioridad_final, 1)
        else: return "BAJA", "green", round(prioridad_final, 1)

proveedor_firms = FirmsProvider()
motor_isr = MotorInteligencia()

# ===> RENOMBRADA PARA EVITAR EL ERROR DE CACHÉ DE STREAMLIT <===
@st.cache_data(ttl=1800)
def obtener_focos_firms_v2():
    return proveedor_firms.obtener_focos()

def obtener_capa_radar():
    try:
        res = requests.get("https://api.rainviewer.com/public/weather-maps.json", timeout=10)
        if res.status_code == 200:
            data = res.json()
            latest_path = data["radar"]["past"][-1]["path"]
            host = data["host"]
            return f"{host}{latest_path}/256/{{z}}/{{x}}/{{y}}/2/1_1.png"
        return None
    except:
        return None

def fetch_hidrico(info):
    try:
        time.sleep(random.uniform(0.1, 0.7)) 
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": info["lat"], "longitude": info["lon"], "past_days": 14, 
            "forecast_days": 3, "daily": ["precipitation_sum"], "timezone": "America/Montevideo"
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200: raise ValueError
            
        df_c = pd.DataFrame(resp.json().get("daily", {}))
        serie_pasada = df_c['precipitation_sum'].fillna(0).iloc[:-3]
        ll_pasada_total = serie_pasada.sum()
        ll_ultima_24h = serie_pasada.iloc[-1] 
        ll_futura = df_c['precipitation_sum'].fillna(0).iloc[-3:].sum()
        
        idx = ((ll_pasada_total * 0.3) + (ll_futura * 0.7)) * info["coef_v"]
        
        if idx < 15: cat = "Normal"
        elif idx <= 35: cat = "Alerta Amarilla"
        elif idx <= 70: cat = "Alerta Naranja"
        else: cat = "Alerta Roja"
        
        return {
            "Ciudad": info["Ciudad"], "Afluente": info["Afluente"], "Latitud": info["lat"], "Longitud": info["lon"], 
            "Lluvia_24h": round(ll_ultima_24h, 1), "Lluvia_14d": round(ll_pasada_total, 1), 
            "Pronostico_3d": round(ll_futura, 1), "Indice": round(idx, 2), "Categoria": cat
        }
    except:
        return {
            "Ciudad": info["Ciudad"], "Afluente": info["Afluente"], "Latitud": info["lat"], "Longitud": info["lon"], 
            "Lluvia_24h": 0, "Lluvia_14d": 0, "Pronostico_3d": 0, "Indice": 0, "Categoria": "Sin Datos"
        }

def fetch_fuego(ciudad, info):
    try:
        time.sleep(random.uniform(0.1, 0.7))
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": info["lat"], "longitude": info["lon"], "past_days": 90, 
            "forecast_days": 1, "daily": ["temperature_2m_max", "relative_humidity_2m_min", "precipitation_sum"], 
            "timezone": "America/Montevideo"
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200: raise ValueError
            
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
            "Ciudad": ciudad, "Latitud": info["lat"], "Longitud": info["lon"], 
            "PSE": round(PSE,2), "RFO": round(RFO,4), "Precip_90d": round(precip_total_90d, 1), "Categoria": cat
        }
    except:
        return {
            "Ciudad": ciudad, "Latitud": info["lat"], "Longitud": info["lon"], 
            "PSE": 0, "RFO": 0, "Precip_90d": 0, "Categoria": "Sin Datos"
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
            
    hora_actualizacion = datetime.now().strftime("%d/%m/%Y a las %H:%M:%S")
    return pd.DataFrame(r_agua), pd.DataFrame(r_fuego), hora_actualizacion

# ==========================================
# 5. PANELES DE CONTROL (FRONT-END)
# ==========================================
with st.spinner('Sincronizando modelos, base de datos local y red satelital (VIIRS)...'):
    df_inundacion, df_fuego, ultima_actualizacion = obtener_datos_completos()
    df_firms, focos_crudos, metodo_filtro = obtener_focos_firms_v2() # <--- NOMBRE NUEVO
    enlace_radar = obtener_capa_radar()

st.info(f"📡 **ENLACE C4ISR ESTABLECIDO:** Última actualización de telemetría el {ultima_actualizacion} (Hora Local).")

tab_agua, tab_fuego, tab_radar = st.tabs(["💧 EVALUACIÓN HÍDRICA", "🌲 FOCOS ISR & PRIORIZACIÓN", "📡 RADAR ESPACIO AÉREO"])

# --- PESTAÑA 1: INUNDACIONES ---
with tab_agua:
    if "Sin Datos" in df_inundacion["Categoria"].values: 
        st.warning("Aviso: Disrupción temporal en algunas localidades.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Mapa de Índice de Inundación")
        mapa_indice_agua = folium.Map(location=[-32.5, -56.0], zoom_start=6, tiles="CartoDB positron")
        colores_agua = {"Normal": "green", "Alerta Amarilla": "orange", "Alerta Naranja": "red", "Alerta Roja": "darkred", "Sin Datos": "gray"}
        
        for idx, fila in df_inundacion.iterrows():
            folium.CircleMarker(
                location=[fila['Latitud'], fila['Longitud']], radius=10,
                tooltip=f"<b>{fila['Ciudad']}</b><br>Índice: {fila['Indice']}<br>Situación: <b>{fila['Categoria']}</b>",
                color=colores_agua.get(fila['Categoria'], "gray"), fill=True, fill_opacity=0.7
            ).add_to(mapa_indice_agua)
            
            folium.Marker(
                location=[fila['Latitud'], fila['Longitud']],
                icon=folium.DivIcon(html=f'<div style="font-size: 11pt; font-weight: bold; color: #1E293B; text-shadow: 1px 1px 3px white; margin-left: 15px; margin-top: -10px;">{fila["Indice"]}</div>')
            ).add_to(mapa_indice_agua)
        components.html(mapa_indice_agua._repr_html_(), height=450)
        
    with col2:
        st.markdown("#### Mapa Telemetría Base (Precipitaciones)")
        mapa_meteo = folium.Map(location=[-32.5, -56.0], zoom_start=6, tiles="CartoDB dark_matter")
        
        if enlace_radar:
            folium.TileLayer(
                tiles=enlace_radar, attr="RainViewer", name="Radar Lluvias", overlay=True, control=True, opacity=0.7
            ).add_to(mapa_meteo)
            
        for idx, fila in df_inundacion.iterrows():
            etiqueta_intuitiva = f"""
            <div style='min-width: 160px; font-family: sans-serif;'>
                <h4 style='margin-bottom: 5px; color: #1E293B;'>{fila['Ciudad']}</h4>
                <hr style='margin: 2px 0;'>
                <span style='color: #2563EB;'>💧 <b>Últimas 24h:</b> {fila['Lluvia_24h']} mm</span><br>
                <span style='color: #047857;'>🌧️ <b>Acumulado (14d):</b> {fila['Lluvia_14d']} mm</span><br>
                <span style='color: #D97706;'>🔮 <b>Pronóstico (3d):</b> {fila['Pronostico_3d']} mm</span>
            </div>
            """
            radio_dinamico = max(5, min(fila['Lluvia_14d'] / 10, 18))
            folium.CircleMarker(
                location=[fila['Latitud'], fila['Longitud']], radius=radio_dinamico,
                tooltip=etiqueta_intuitiva, color="#3B82F6", fill=True, fill_opacity=0.6
            ).add_to(mapa_meteo)
        
        components.html(mapa_meteo._repr_html_(), height=450)

# --- PESTAÑA 2: INCENDIOS + FIRMS + INTELIGENCIA ---
with tab_fuego:
    if "Sin Datos" in df_fuego["Categoria"].values: 
        st.warning("Aviso: Disrupción temporal en algunas localidades.")
        
    if not df_firms.empty:
        focos_totales = len(df_firms)
        focos_criticos = len(df_firms[df_firms['Nivel_FRP'].isin(['ALTO', 'SEVERO'])])
        
        if focos_criticos > 0:
            st.error(f"🚨 **ALERTA ROJA ISR:** {focos_criticos} focos de calor CRÍTICOS/ALTOS detectados. Despliegue de reconocimiento recomendado.")
        elif focos_totales > 0:
            st.warning(f"⚠️ **ACTIVIDAD DETECTADA:** {focos_totales} focos de calor (Nivel Bajo/Moderado). Mantener vigilancia rutinaria.")
    else:
        st.success("✅ **REPORTE ISR:** Sin detecciones de anomalías térmicas en las últimas 24 horas (Satélite VIIRS).")
        
    with st.expander("🔍 Auditoría Espacial FIRMS", expanded=False):
        st.write(f"**Motor Geométrico:** {metodo_filtro}")
        st.write(f"**Detecciones Crudas (Caja Sudamérica):** {focos_crudos}")
        st.write(f"**Focos Depurados (Intersección Uruguay):** {len(df_firms)}")
    
    st.markdown("#### Índice de Vulnerabilidad Forestal Global (RFO)")
    fig_fuego = px.scatter(
        df_fuego, x="PSE", y="RFO", color="Categoria", hover_name="Ciudad",
        color_discrete_map={"Mínimo": "#10B981", "Bajo": "#3B82F6", "Medio": "#FBBF24", "Alto": "#F97316", "Crítico": "#DC2626", "Sin Datos": "#94A3B8"}, 
        height=300, template="plotly_white"
    )
    st.plotly_chart(fig_fuego, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("#### Matriz RFO + Focos Térmicos (FIRMS)")
        mapa_fuego = folium.Map(location=[-32.5, -56.0], zoom_start=6, tiles="CartoDB dark_matter")
        colores_fuego = {"Mínimo": "green", "Bajo": "blue", "Medio": "orange", "Alto": "red", "Crítico": "darkred", "Sin Datos": "gray"}
        
        for idx, fila in df_fuego.iterrows():
            folium.CircleMarker(
                location=[fila['Latitud'], fila['Longitud']], radius=10,
                tooltip=f"<b>{fila['Ciudad']}</b><br>RFO: {fila['RFO']}<br>Nivel: <b>{fila['Categoria']}</b>",
                color=colores_fuego.get(fila['Categoria'], "gray"), fill=True, fill_opacity=0.4
            ).add_to(mapa_fuego)
            
        if not df_firms.empty:
            for idx, foco in df_firms.iterrows():
                etiqueta_firms = f"""
                <div style='min-width: 160px; font-family: sans-serif;'>
                    <h4 style='margin-bottom: 5px; color: {foco['Color_FRP']};'>🔥 FOCO {foco['Nivel_FRP']}</h4>
                    <hr style='margin: 2px 0;'>
                    <b>Potencia (FRP):</b> {foco['frp']} MW<br>
                    <b>Confianza:</b> {foco.get('confidence', 'N/A')}<br>
                    <b>Lat/Lon:</b> {foco['latitude']:.4f}, {foco['longitude']:.4f}
                </div>
                """
                folium.Marker(
                    location=[foco['latitude'], foco['longitude']],
                    icon=folium.Icon(color=foco['Color_FRP'], icon="fire", prefix="fa"),
                    tooltip=etiqueta_firms
                ).add_to(mapa_fuego)
            
        components.html(mapa_fuego._repr_html_(), height=500)
        
    with col4:
        st.markdown("#### 📡 Reporte ISR Automatizado")
        st.info("Priorización calculada cruzando amenaza y exposición de infraestructuras críticas.")
        
        if not df_firms.empty:
            focos_ordenados = df_firms.sort_values(by='frp', ascending=False).head(5)
            
            for idx, foco in focos_ordenados.iterrows():
                lat, lon = foco['latitude'], foco['longitude']
                frp = foco['frp']
                
                rfo_local = motor_isr.obtener_rfo_local_dinamico(lat, lon, df_fuego)
                distancias = motor_isr.buscar_infraestructura_cercana(lat, lon)
                nivel_prioridad, color_rep, score = motor_isr.calcular_prioridad_operacional(frp, rfo_local, distancias)
                
                st.markdown(f"""
                <div style="border-left: 4px solid {color_rep}; padding-left: 15px; margin-bottom: 15px; background-color: #F8FAFC; padding-top: 10px; padding-bottom: 10px; border-radius: 4px; border-right: 1px solid #E2E8F0; border-top: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0;">
                    <h5 style="color: #1E293B; margin-bottom: 2px; margin-top: 0;">🔥 OBJETIVO TÁCTICO | Potencia: {frp} MW</h5>
                    <p style="font-family: monospace; font-size: 13px; color: #475569; margin-top: 5px; margin-bottom: 8px;">
                        • RFO Local Heredado: <b>{rfo_local:.2f}</b><br>
                        • Poblado más cercano: <b>{distancias['poblados'][0]:.1f} km</b> ({distancias['poblados'][1]})<br>
                        • Ruta nacional: <b>{distancias['rutas'][0]:.1f} km</b> ({distancias['rutas'][1]})<br>
                        • Infra. Eléctrica: <b>{distancias['subestaciones'][0]:.1f} km</b> ({distancias['subestaciones'][1]})
                    </p>
                    <h6 style="color: {color_rep}; margin-top: 0px; margin-bottom: 0px;">PRIORIDAD ASIGNADA: {nivel_prioridad} (Score: {score})</h6>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("Sin objetivos tácticos activos para derivar a reconocimiento.")

# --- PESTAÑA 3: RADAR ANIMADO ---
with tab_radar:
    st.markdown("#### Monitor Táctico (Windy)")
    iframe_windy = """
    <iframe width="100%" height="600" src="https://embed.windy.com/embed2.html?lat=-32.5&lon=-56.0&zoom=6&level=surface&overlay=radar&product=radar&menu=&message=&marker=&calendar=now&city=&type=map&location=coordinates&detail=&metricWind=kt&metricTemp=%C2%B0C&radarRange=-1" frameborder="0"></iframe>
    """
    components.html(iframe_windy, height=600)
