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
from sklearn.cluster import DBSCAN

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
    st.markdown("**FUERZA AÉREA URUGUAYA** | COP (Common Operational Picture) ISR Multi-Amenaza.")

st.divider()

# ==========================================
# 3. DICCIONARIOS GEOGRÁFICOS Y LOGÍSTICOS
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

# Unidades FAU Operativas (Velocidad crucero Helo/Avión Ligero en km/h)
unidades_fau = {
    "Brigada Aérea I (Carrasco)": {"lat": -34.833, "lon": -56.033, "vel_kmh": 200},
    "Brigada Aérea II (Durazno)": {"lat": -33.353, "lon": -56.498, "vel_kmh": 200},
    "Brigada Aérea III (Boiso Lanza)": {"lat": -34.816, "lon": -56.166, "vel_kmh": 200}
}

# ==========================================
# 4. MOTORES GEOESPACIALES E INTELIGENCIA
# ==========================================

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class MotorInteligencia:
    def __init__(self):
        # Infraestructura Genérica (Fuego)
        self.infra_general = {
            "aerodromos": [{"nombre": "Aeropuerto de Rivera", "lat": -30.9, "lon": -55.5}, {"nombre": "Aeródromo Santa Bernardina", "lat": -33.35, "lon": -56.49}],
            "rutas": [{"nombre": "Ruta Nacional Primaria", "lat": -33.0, "lon": -56.0}],
            "subestaciones": [{"nombre": "Subestación UTE Transmisión", "lat": -34.0, "lon": -56.2}],
            "poblados": [{"nombre": "Centro Urbano", "lat": -33.5, "lon": -56.5}]
        }
        # Infraestructura Hídrica Crítica
        self.infra_hidrica = {
            "represas": [{"nombre": "Represa Salto Grande", "lat": -31.27, "lon": -57.94}, {"nombre": "Represa Palmar", "lat": -33.05, "lon": -57.48}],
            "plantas_ose": [{"nombre": "Planta Aguas Corrientes", "lat": -34.52, "lon": -56.32}, {"nombre": "Toma OSE Durazno", "lat": -33.37, "lon": -56.50}],
            "puentes": [{"nombre": "Puente Internacional S. Martín", "lat": -33.10, "lon": -58.31}, {"nombre": "Puente Río Yí", "lat": -33.36, "lon": -56.51}],
            "hospitales": [{"nombre": "Hospital Tacuarembó", "lat": -31.71, "lon": -55.98}, {"nombre": "Hospital Durazno", "lat": -33.38, "lon": -56.52}]
        }

    def buscar_infraestructura(self, lat_foco, lon_foco, tipo="general"):
        diccionario = self.infra_hidrica if tipo == "hidrica" else self.infra_general
        reporte = {}
        for categoria, items in diccionario.items():
            distancias = []
            for item in items:
                dist = haversine(lat_foco, lon_foco, item["lat"], item["lon"])
                distancias.append((dist, item["nombre"]))
            distancias.sort(key=lambda x: x[0])
            reporte[categoria] = distancias[0] if distancias else (999, "N/A")
        return reporte

    def calcular_eta_fau(self, lat_foco, lon_foco):
        rutas_fau = []
        for base, info in unidades_fau.items():
            dist = haversine(lat_foco, lon_foco, info["lat"], info["lon"])
            tiempo_horas = dist / info["vel_kmh"]
            minutos = int(tiempo_horas * 60)
            rutas_fau.append({"base": base, "distancia": dist, "eta_min": minutos})
        rutas_fau.sort(key=lambda x: x["distancia"])
        return rutas_fau[0]

    def obtener_rfo_local_dinamico(self, lat, lon, df_rfo_base):
        if df_rfo_base.empty: return 0.8
        df_calc = df_rfo_base.copy()
        df_calc["dist_sq"] = (df_calc["Latitud"] - lat)**2 + (df_calc["Longitud"] - lon)**2
        return df_calc.loc[df_calc["dist_sq"].idxmin(), "RFO"]

    def calcular_prioridad_fuego(self, frp, rfo, distancias):
        frp_norm = min(float(frp) / 200.0, 1.0)
        amenaza = (rfo * 0.4) + (frp_norm * 0.6)
        exposicion = 0.0
        if distancias["poblados"][0] < 10: exposicion += 0.5
        if distancias["subestaciones"][0] < 5: exposicion += 0.3
        if distancias["rutas"][0] < 2: exposicion += 0.1
        if distancias["aerodromos"][0] < 15: exposicion += 0.1
        if exposicion == 0: exposicion = 0.1 
        prioridad_final = amenaza * exposicion * 100
        
        if prioridad_final > 75: return "ALTA", "red", round(prioridad_final, 1), "Extinción Aérea / Evacuación (Helo)"
        elif prioridad_final > 35: return "MODERADA", "orange", round(prioridad_final, 1), "Reconocimiento Táctico (Avión Ligero)"
        else: return "BAJA", "green", round(prioridad_final, 1), "Monitoreo Satelital (Sin Despliegue)"

    def calcular_prioridad_hidrica(self, ihi, distancias):
        amenaza = min(float(ihi) / 100.0, 1.0) 
        exposicion = 0.0
        if distancias["hospitales"][0] < 5: exposicion += 0.4
        if distancias["plantas_ose"][0] < 5: exposicion += 0.3
        if distancias["represas"][0] < 10: exposicion += 0.2
        if distancias["puentes"][0] < 2: exposicion += 0.1
        if exposicion == 0: exposicion = 0.1 
        prioridad_final = amenaza * exposicion * 100
        
        if prioridad_final > 70: return "CRÍTICA", "darkred", round(prioridad_final, 1), "Evacuación SAR / Aeromédica (Bell 212)"
        elif prioridad_final > 40: return "ALTA", "red", round(prioridad_final, 1), "Transporte de Suministros (C-130/C-212)"
        elif prioridad_final > 20: return "ATENCIÓN", "orange", round(prioridad_final, 1), "Reconocimiento de Cuenca (UAV/Avión Ligero)"
        else: return "NORMAL", "green", round(prioridad_final, 1), "Monitoreo Estándar (Sin Despliegue)"

    def aplicar_dbscan_hidrico(self, df):
        """Agrupa cuencas desbordadas cercanas en Eventos Macro"""
        df_riesgo = df[df['IHI'] >= 20].copy()
        if df_riesgo.empty: return pd.DataFrame()
        
        coords = df_riesgo[['Latitud', 'Longitud']].values
        # Epsilon 0.4 (aprox 45km). Si dos ciudades en alerta están cerca, es la misma zona de inundación
        db = DBSCAN(eps=0.4, min_samples=1, metric='euclidean').fit(coords)
        df_riesgo['cluster'] = db.labels_
        
        eventos = []
        for cluster_id, group in df_riesgo.groupby('cluster'):
            ihi_max = group['IHI'].max()
            lat_c = group['Latitud'].mean()
            lon_c = group['Longitud'].mean()
            afluentes = list(set(group['Afluente']))
            ciudades = ", ".join(group['Ciudad'].tolist())
            
            eventos.append({
                'evento_id': f"ZONA-{cluster_id+1:03d}",
                'Latitud': lat_c, 'Longitud': lon_c, 'IHI_Max': round(ihi_max, 1),
                'Ciudades': ciudades, 'Afluentes': ", ".join(afluentes), 'Num_Sistemas': len(group)
            })
        return pd.DataFrame(eventos)

motor_isr = MotorInteligencia()

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

    def aplicar_dbscan_clustering(self, df):
        if df.empty: return pd.DataFrame()
        coords = df[['latitude', 'longitude']].values
        db = DBSCAN(eps=0.02, min_samples=1, metric='euclidean').fit(coords)
        df['cluster'] = db.labels_
        incidentes = []
        for cluster_id, group in df.groupby('cluster'):
            frp_max = group['frp'].max()
            lat_c = group['latitude'].mean()
            lon_c = group['longitude'].mean()
            sensores = len(group)
            area_km2 = sensores * 0.14
            nivel, color = self.clasificar_frp(frp_max)
            incidentes.append({
                'incidente_id': f"INC-{cluster_id+1:03d}", 'latitude': lat_c, 'longitude': lon_c,
                'frp_max': round(frp_max, 1), 'sensores': sensores, 'area_km2': round(area_km2, 2),
                'Nivel_FRP': nivel, 'Color_FRP': color
            })
        return pd.DataFrame(incidentes)

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
                return pd.DataFrame(), 0, "Sin Datos", 0

        df['frp'] = pd.to_numeric(df.get('frp', 0), errors='coerce').fillna(0)
        df_bbox = df[(df['latitude'] >= -36.0) & (df['latitude'] <= -29.0) & (df['longitude'] >= -59.0) & (df['longitude'] <= -52.0)].copy()
        focos_originales = len(df_bbox)

        try:
            gdf = gpd.GeoDataFrame(df_bbox, geometry=gpd.points_from_xy(df_bbox.longitude, df_bbox.latitude), crs="EPSG:4326")
            if os.path.exists("uruguay.gpkg"):
                uruguay = gpd.read_file("uruguay.gpkg")
                tipo_filtro = "GeoPackage Local (.gpkg) + DBSCAN"
            else:
                uruguay = gpd.read_file(self.geo_fallback_url)
                tipo_filtro = "GeoJSON (API) + DBSCAN"
            df_uy = gdf[gdf.within(uruguay.unary_union)].copy()
        except Exception:
            df_uy = df_bbox.copy()
            tipo_filtro = "Bounding Box + DBSCAN"
            
        detecciones_crudas = len(df_uy)
        df_incidentes = self.aplicar_dbscan_clustering(df_uy)
        return df_incidentes, focos_originales, tipo_filtro, detecciones_crudas

proveedor_firms = FirmsProvider()

@st.cache_data(ttl=1800)
def obtener_focos_firms_isr():
    return proveedor_firms.obtener_focos()

def obtener_capa_radar():
    try:
        res = requests.get("https://api.rainviewer.com/public/weather-maps.json", timeout=10)
        if res.status_code == 200:
            return f"{res.json()['host']}{res.json()['radar']['past'][-1]['path']}/256/{{z}}/{{x}}/{{y}}/2/1_1.png"
        return None
    except:
        return None

def fetch_hidrico(info):
    try:
        time.sleep(random.uniform(0.1, 0.5)) 
        url = "https://api.open-meteo.com/v1/forecast"
        params = {"latitude": info["lat"], "longitude": info["lon"], "past_days": 14, "forecast_days": 3, "daily": ["precipitation_sum"], "timezone": "America/Montevideo"}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200: raise ValueError
            
        df_c = pd.DataFrame(resp.json().get("daily", {}))
        
        # Histórico y predicción a 24/48/72 horas
        serie_pasada = df_c['precipitation_sum'].fillna(0).iloc[:-3]
        serie_futura = df_c['precipitation_sum'].fillna(0).iloc[-3:]
        
        ll_pasada_total = serie_pasada.sum()
        ll_ultima_24h = serie_pasada.iloc[-1] 
        ll_futura_24h = serie_futura.iloc[0]
        ll_futura_48h = serie_futura.iloc[1]
        ll_futura_72h = serie_futura.iloc[2]
        ll_futura_total = serie_futura.sum()
        
        # IHI: Índice Hídrico Integrado Operacional
        ihi = ((ll_pasada_total * 0.4) + (ll_futura_total * 0.6)) * info["coef_v"]
        
        if ihi < 15: cat = "Normal"
        elif ihi <= 35: cat = "Atención"
        elif ihi <= 70: cat = "Alerta"
        else: cat = "Emergencia"
        
        return {
            "Ciudad": info["Ciudad"], "Afluente": info["Afluente"], "Latitud": info["lat"], "Longitud": info["lon"], 
            "Lluvia_24h": round(ll_ultima_24h, 1), "Lluvia_14d": round(ll_pasada_total, 1), 
            "Futura_24h": round(ll_futura_24h, 1), "Futura_48h": round(ll_futura_48h, 1), "Futura_72h": round(ll_futura_72h, 1),
            "Pronostico_3d": round(ll_futura_total, 1), "IHI": round(ihi, 2), "Categoria": cat
        }
    except:
        return {
            "Ciudad": info["Ciudad"], "Afluente": info["Afluente"], "Latitud": info["lat"], "Longitud": info["lon"], 
            "Lluvia_24h": 0, "Lluvia_14d": 0, "Futura_24h": 0, "Futura_48h": 0, "Futura_72h": 0, 
            "Pronostico_3d": 0, "IHI": 0, "Categoria": "Sin Datos"
        }

def fetch_fuego(ciudad, info):
    try:
        time.sleep(random.uniform(0.1, 0.5))
        url = "https://api.open-meteo.com/v1/forecast"
        params = {"latitude": info["lat"], "longitude": info["lon"], "past_days": 90, "forecast_days": 1, "daily": ["temperature_2m_max", "relative_humidity_2m_min", "precipitation_sum"], "timezone": "America/Montevideo"}
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
        RFO = (0.9 * (1 + np.sin(np.radians((info["coef_a"] * 1.72 * PSE - 90)))) / 2) * (-0.006 * df_c['relative_humidity_2m_min'].ffill().iloc[0] + 1.3) * (0.02 * df_c['temperature_2m_max'].ffill().iloc[0] + 0.4)
        
        if RFO < 0.15: cat = "Mínimo"
        elif RFO <= 0.40: cat = "Bajo"
        elif RFO <= 0.70: cat = "Medio"
        elif RFO <= 0.95: cat = "Alto"
        else: cat = "Crítico"
        
        return {"Ciudad": ciudad, "Latitud": info["lat"], "Longitud": info["lon"], "PSE": round(PSE,2), "RFO": round(RFO,4), "Precip_90d": round(precip_total_90d, 1), "Categoria": cat}
    except:
        return {"Ciudad": ciudad, "Latitud": info["lat"], "Longitud": info["lon"], "PSE": 0, "RFO": 0, "Precip_90d": 0, "Categoria": "Sin Datos"}

# ===> RENOMBRADA PARA EVITAR CACHÉ VIEJA <===
@st.cache_data(ttl=3600)
def obtener_datos_completos_v2():
    r_agua = []
    r_fuego = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        f_agua = [executor.submit(fetch_hidrico, i) for k, i in monitoreo_hidrico.items()]
        for f in concurrent.futures.as_completed(f_agua): r_agua.append(f.result())
            
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        f_fuego = [executor.submit(fetch_fuego, c, i) for c, i in monitoreo_fuego.items()]
        for f in concurrent.futures.as_completed(f_fuego): r_fuego.append(f.result())
            
    hora_actualizacion = datetime.now().strftime("%d/%m/%Y a las %H:%M:%S")
    return pd.DataFrame(r_agua), pd.DataFrame(r_fuego), hora_actualizacion

# ==========================================
# 5. PANELES DE CONTROL (FRONT-END)
# ==========================================
with st.spinner('Sincronizando Sistemas C4ISR y Constelaciones Satelitales...'):
    df_inundacion, df_fuego, ultima_actualizacion = obtener_datos_completos_v2()
    df_eventos_hidricos = motor_isr.aplicar_dbscan_hidrico(df_inundacion)
    df_incidentes, focos_crudos, metodo_filtro, detec_crudas = obtener_focos_firms_isr()
    enlace_radar = obtener_capa_radar()

st.info(f"📡 **ENLACE C4ISR ESTABLECIDO:** Última actualización de telemetría el {ultima_actualizacion} (Hora Local).")

tab_agua, tab_fuego, tab_radar = st.tabs(["💧 EVENTOS HÍDRICOS (IHI)", "🌲 INCIDENTES FUEGO (RFO)", "📡 RADAR ESPACIO AÉREO"])

# --- PESTAÑA 1: INUNDACIONES C4ISR ---
with tab_agua:
    if "Sin Datos" in df_inundacion["Categoria"].values: 
        st.warning("Aviso: Disrupción temporal en algunas cuencas.")
        
    inundaciones_criticas = len(df_inundacion[df_inundacion['IHI'] >= 70])
    if inundaciones_criticas > 0:
        st.error(f"🚨 **ALERTA ROJA HÍDRICA:** {inundaciones_criticas} cuencas en estado de Emergencia/Alerta. Despliegue de reconocimiento aéreo recomendado.")
    else:
        st.success("✅ **REPORTE ISR:** Sistemas hídricos dentro de los umbrales operativos.")
    
    # RANKING NACIONAL HÍDRICO (Nuevo Módulo C4ISR)
    if not df_eventos_hidricos.empty:
        st.markdown("### 🏆 RANKING TÁCTICO HÍDRICO (ZONAS AFECTADAS)")
        st.markdown("Agrupación por Machine Learning de Cuencas desbordadas y asignación de misión FAU.")
        
        datos_ranking_hidrico = []
        for idx, evento in df_eventos_hidricos.iterrows():
            lat, lon = evento['Latitud'], evento['Longitud']
            ihi_zona = evento['IHI_Max']
            distancias = motor_isr.buscar_infraestructura(lat, lon, tipo="hidrica")
            nivel_prioridad, color_rep, score, mision = motor_isr.calcular_prioridad_hidrica(ihi_zona, distancias)
            logistica_fau = motor_isr.calcular_eta_fau(lat, lon)
            
            datos_ranking_hidrico.append({
                "ID": evento['evento_id'], "Prioridad": nivel_prioridad, "Score": score, "Color": color_rep,
                "IHI": ihi_zona, "Sistemas": evento['Afluentes'], "Mision": mision,
                "Base_FAU": logistica_fau['base'], "ETA": logistica_fau['eta_min'], 
                "Represa": distancias['represas'], "Planta": distancias['plantas_ose']
            })
            
        datos_ranking_hidrico.sort(key=lambda x: x["Score"], reverse=True)
        
        cols_ranking_h = st.columns(min(3, len(datos_ranking_hidrico)))
        for i, obj in enumerate(datos_ranking_hidrico[:3]):
            with cols_ranking_h[i]:
                st.markdown(f"""
                <div style="background-color: #0F172A; color: white; padding: 15px; border-radius: 8px; border-top: 5px solid {obj['Color']};">
                    <h4 style="margin-top:0; margin-bottom:5px; color: {obj['Color']};">{obj['ID']} | SCORE: {obj['Score']}</h4>
                    <hr style="border-color: #334155; margin: 8px 0;">
                    <span style="font-size: 13px; color: #FBBF24;">🛡️ <b>Misión:</b> {obj['Mision']}</span><br>
                    <span style="font-size: 13px; color: #F8FAFC;">⏱️ <b>ETA Despliegue ({obj['Base_FAU']}):</b> {obj['ETA']} min</span><br>
                    <span style="font-size: 13px; color: #94A3B8;">🌊 <b>Afluentes:</b> {obj['Sistemas']}</span><br>
                    <span style="font-size: 13px; color: #94A3B8;">🏭 <b>Planta OSE Cercana:</b> a {obj['Planta'][0]:.1f} km</span>
                </div>
                """, unsafe_allow_html=True)
        st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Matriz IHI + Zonas de Impacto (DBSCAN)")
        mapa_indice_agua = folium.Map(location=[-32.5, -56.0], zoom_start=6, tiles="CartoDB dark_matter")
        colores_agua = {"Normal": "green", "Atención": "orange", "Alerta": "red", "Emergencia": "darkred", "Sin Datos": "gray"}
        
        for idx, fila in df_inundacion.iterrows():
            folium.CircleMarker(
                location=[fila['Latitud'], fila['Longitud']], radius=8,
                tooltip=f"<b>{fila['Ciudad']}</b><br>Río: {fila['Afluente']}<br>IHI: {fila['IHI']}<br>Nivel: <b>{fila['Categoria']}</b>",
                color=colores_agua.get(fila['Categoria'], "gray"), fill=True, fill_opacity=0.6
            ).add_to(mapa_indice_agua)
            
        if not df_eventos_hidricos.empty:
            for idx, ev in df_eventos_hidricos.iterrows():
                radio_zona = max(15, min(ev['IHI_Max'] / 2, 40))
                folium.CircleMarker(
                    location=[ev['Latitud'], ev['Longitud']], radius=radio_zona,
                    tooltip=f"<b>{ev['evento_id']}</b><br>IHI Máx: {ev['IHI_Max']}<br>Sistemas Afectados: {ev['Afluentes']}",
                    color="red", fill=True, fill_opacity=0.3
                ).add_to(mapa_indice_agua)
                
                folium.Marker(
                    location=[ev['Latitud'], ev['Longitud']], icon=folium.Icon(color="red", icon="tint", prefix="fa"),
                ).add_to(mapa_indice_agua)
            
        components.html(mapa_indice_agua._repr_html_(), height=500)
        
    with col2:
        st.markdown("#### 🗺️ Mapa de Calor (Saturación y Pronóstico 72h)")
        mapa_meteo = folium.Map(location=[-32.5, -56.0], zoom_start=6, tiles="CartoDB dark_matter")
        
        # Heatmap Hídrico
        heat_data_agua = [[row['Latitud'], row['Longitud'], float(row['IHI'])] for idx, row in df_inundacion.iterrows()]
        HeatMap(heat_data_agua, radius=40, blur=25, gradient={0.3: 'blue', 0.6: 'cyan', 0.8: 'lime', 1.0: 'red'}).add_to(mapa_meteo)
            
        for idx, fila in df_inundacion.iterrows():
            etiqueta_intuitiva = f"""
            <div style='min-width: 170px; font-family: sans-serif;'>
                <h4 style='margin-bottom: 5px; color: #1E293B;'>{fila['Ciudad']}</h4>
                <hr style='margin: 2px 0;'>
                <span style='color: #047857;'>🌧️ <b>Acumulado (14d):</b> {fila['Lluvia_14d']} mm</span><br>
                <hr style='margin: 2px 0;'>
                <span style='color: #D97706;'><b>Predicción Meteorológica:</b></span><br>
                • +24h: {fila['Futura_24h']} mm<br>
                • +48h: {fila['Futura_48h']} mm<br>
                • +72h: {fila['Futura_72h']} mm<br>
                <b>Total Pronóstico:</b> {fila['Pronostico_3d']} mm
            </div>
            """
            radio_dinamico = max(5, min(fila['Pronostico_3d'] / 5, 18))
            folium.CircleMarker(
                location=[fila['Latitud'], fila['Longitud']], radius=radio_dinamico,
                tooltip=etiqueta_intuitiva, color="#3B82F6", fill=True, fill_opacity=0.6
            ).add_to(mapa_meteo)
        
        components.html(mapa_meteo._repr_html_(), height=500)

# --- PESTAÑA 2: INCENDIOS + FIRMS + INTELIGENCIA ---
with tab_fuego:
    if "Sin Datos" in df_fuego["Categoria"].values: 
        st.warning("Aviso: Disrupción temporal en algunas localidades.")
        
    if not df_incidentes.empty:
        incidentes_totales = len(df_incidentes)
        incidentes_criticos = len(df_incidentes[df_incidentes['Nivel_FRP'].isin(['ALTO', 'SEVERO'])])
        
        if incidentes_criticos > 0:
            st.error(f"🚨 **ALERTA ROJA ISR:** {incidentes_criticos} INCIDENTES TÁCTICOS CRÍTICOS confirmados. Priorizando logística FAU.")
        elif incidentes_totales > 0:
            st.warning(f"⚠️ **ACTIVIDAD DETECTADA:** {incidentes_totales} incidentes aislados (Nivel Bajo/Moderado). Mantener vigilancia.")
    else:
        st.success("✅ **REPORTE ISR:** Sin incidentes térmicos confirmados en las últimas 24 horas.")
    
    # RANKING NACIONAL FUEGO C4ISR
    if not df_incidentes.empty:
        st.markdown("### 🏆 RANKING TÁCTICO FUEGO")
        st.markdown("Incidentes priorizados automáticamente por el Motor Analítico.")
        
        datos_ranking = []
        for idx, foco in df_incidentes.iterrows():
            lat, lon = foco['latitude'], foco['longitude']
            frp = foco['frp_max']
            rfo_local = motor_isr.obtener_rfo_local_dinamico(lat, lon, df_fuego)
            distancias = motor_isr.buscar_infraestructura(lat, lon, tipo="general")
            nivel_prioridad, color_rep, score, mision = motor_isr.calcular_prioridad_fuego(frp, rfo_local, distancias)
            logistica_fau = motor_isr.calcular_eta_fau(lat, lon)
            
            datos_ranking.append({
                "ID": foco['incidente_id'], "Prioridad": nivel_prioridad, "Score": score, "Color": color_rep,
                "FRP": frp, "Area": foco['area_km2'], "Mision": mision,
                "Base_FAU": logistica_fau['base'], "ETA": logistica_fau['eta_min'], "Poblado": distancias['poblados']
            })
            
        datos_ranking.sort(key=lambda x: x["Score"], reverse=True)
        
        cols_ranking = st.columns(min(3, len(datos_ranking)))
        for i, obj in enumerate(datos_ranking[:3]):
            with cols_ranking[i]:
                st.markdown(f"""
                <div style="background-color: #0F172A; color: white; padding: 15px; border-radius: 8px; border-top: 5px solid {obj['Color']};">
                    <h4 style="margin-top:0; margin-bottom:5px; color: {obj['Color']};">{obj['ID']} | SCORE: {obj['Score']}</h4>
                    <hr style="border-color: #334155; margin: 8px 0;">
                    <span style="font-size: 13px; color: #FBBF24;">🛡️ <b>Misión:</b> {obj['Mision']}</span><br>
                    <span style="font-size: 13px; color: #F8FAFC;">⏱️ <b>ETA Despliegue ({obj['Base_FAU']}):</b> {obj['ETA']} min</span><br>
                    <span style="font-size: 13px; color: #94A3B8;">📏 <b>Área Estimada:</b> {obj['Area']} km²</span><br>
                    <span style="font-size: 13px; color: #94A3B8;">🏘️ <b>Población:</b> a {obj['Poblado'][0]:.1f} km</span>
                </div>
                """, unsafe_allow_html=True)
        st.divider()

    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("#### Matriz RFO + Incidentes (DBSCAN)")
        mapa_fuego = folium.Map(location=[-32.5, -56.0], zoom_start=6, tiles="CartoDB dark_matter")
        colores_fuego = {"Mínimo": "green", "Bajo": "blue", "Medio": "orange", "Alto": "red", "Crítico": "darkred", "Sin Datos": "gray"}
        
        for idx, fila in df_fuego.iterrows():
            folium.CircleMarker(
                location=[fila['Latitud'], fila['Longitud']], radius=10,
                tooltip=f"<b>{fila['Ciudad']}</b><br>RFO: {fila['RFO']}<br>Nivel: <b>{fila['Categoria']}</b>",
                color=colores_fuego.get(fila['Categoria'], "gray"), fill=True, fill_opacity=0.4
            ).add_to(mapa_fuego)
            
        if not df_incidentes.empty:
            for idx, foco in df_incidentes.iterrows():
                radio_incidente = max(8, min(foco['area_km2'] * 5, 25))
                etiqueta_firms = f"""
                <div style='min-width: 170px; font-family: sans-serif;'>
                    <h4 style='margin-bottom: 5px; color: {foco['Color_FRP']};'>🔥 {foco['incidente_id']} | {foco['Nivel_FRP']}</h4>
                    <hr style='margin: 2px 0;'>
                    <b>Potencia Máx (FRP):</b> {foco['frp_max']} MW<br>
                    <b>Área Estimada:</b> {foco['area_km2']} km²<br>
                    <b>Sensores Agrupados:</b> {foco['sensores']}<br>
                    <b>Centroide:</b> {foco['latitude']:.3f}, {foco['longitude']:.3f}
                </div>
                """
                folium.CircleMarker(
                    location=[foco['latitude'], foco['longitude']],
                    radius=radio_incidente, color=foco['Color_FRP'], fill=True, fill_opacity=0.5, tooltip=etiqueta_firms
                ).add_to(mapa_fuego)
                folium.Marker(location=[foco['latitude'], foco['longitude']], icon=folium.Icon(color=foco['Color_FRP'], icon="fire", prefix="fa")).add_to(mapa_fuego)
            
        components.html(mapa_fuego._repr_html_(), height=500)
        
    with col4:
        st.markdown("#### 🗺️ Mapa de Calor (Estrés Hídrico Previo)")
        mapa_calor = folium.Map(location=[-32.5, -56.0], zoom_start=6, tiles="CartoDB dark_matter")
        
        lluvia_maxima = df_fuego['Precip_90d'].max()
        df_fuego['Peso_Sequia'] = df_fuego['Precip_90d'].apply(lambda x: lluvia_maxima - x + 10)
        heat_data = [[row['Latitud'], row['Longitud'], row['Peso_Sequia']] for idx, row in df_fuego.iterrows()]
        HeatMap(heat_data, radius=35, blur=25, gradient={0.2: 'blue', 0.4: 'cyan', 0.6: 'lime', 0.8: 'yellow', 1.0: 'red'}).add_to(mapa_calor)
        
        components.html(mapa_calor._repr_html_(), height=500)

# --- PESTAÑA 3: RADAR ANIMADO ---
with tab_radar:
    st.markdown("#### Monitor Táctico (Windy)")
    iframe_windy = """
    <iframe width="100%" height="600" src="https://embed.windy.com/embed2.html?lat=-32.5&lon=-56.0&zoom=6&level=surface&overlay=radar&product=radar&menu=&message=&marker=&calendar=now&city=&type=map&location=coordinates&detail=&metricWind=kt&metricTemp=%C2%B0C&radarRange=-1" frameborder="0"></iframe>
    """
    components.html(iframe_windy, height=600)
