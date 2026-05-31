import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import numpy as np
import folium
import plotly.express as px
import concurrent.futures

# ==========================================
# 1. CONFIGURACIÓN DEL SISTEMA
# ==========================================
st.set_page_config(page_title="Vigilancia Territorial FAU", page_icon="✈️", layout="wide")

GA_ID = "G-XXXXXXXXXX" 
ga_script = f"""<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script><script>window.dataLayer = window.dataLayer || []; function gtag(){{dataLayer.push(arguments);}} gtag('js', new Date()); gtag('config', '{GA_ID}');</script>"""
components.html(ga_script, height=0, width=0)

# ==========================================
# 2. CABECERA INSTITUCIONAL FAU
# ==========================================
col_logo, col_titulo = st.columns([1, 7])

with col_logo:
    st.image("FAU.svg", use_container_width=True)

with col_titulo:
    st.title("Sistema de Vigilancia Territorial")
    st.markdown("**FUERZA AÉREA URUGUAYA** | Plataforma integrada de evaluación de riesgos ambientales para el despliegue operativo.")

st.divider()

# ==========================================
# 3. DICCIONARIOS GEOGRÁFICOS
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
# 4. MOTORES DE EXTRACCIÓN Y RADARES
# ==========================================
def obtener_capa_radar():
    try:
        # Tiempo de espera extendido a 10s para darle margen al satélite
        res = requests.get("https://api.rainviewer.com/public/weather-maps.json", timeout=10)
        if res.status_code == 200:
            data = res.json()
            latest_time = data["radar"]["past"][-1]["time"]
            host = data["host"]
            return f"{host}/v2/radar/{latest_time}/256/{{z}}/{{x}}/{{y}}/2/1_1.png"
        return None
    except:
        return None

def fetch_hidrico
