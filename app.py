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
    "Maldonado_SanCarlos": {"Ciudad": "
