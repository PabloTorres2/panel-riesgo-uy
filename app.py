import requests
import pandas as pd
import numpy as np
import time

# --- 1. DEFINICIÓN DE COORDENADAS (CIUDADES CON AFLUENTES Y RIESGO HISTÓRICO) ---
monitoreo_hidrico = {
    # Cuenca del Río Uruguay y Noroeste
    "Artigas_Capital": {"Ciudad": "Artigas", "Afluente": "Río Cuareim", "lat": -30.40, "lon": -56.46, "coef_v": 1.0},
    "Artigas_BellaUnion": {"Ciudad": "Bella Unión", "Afluente": "Río Uruguay / Cuareim", "lat": -30.26, "lon": -57.60, "coef_v": 0.9},
    "Salto_Capital": {"Ciudad": "Salto", "Afluente": "Río Uruguay", "lat": -31.38, "lon": -57.96, "coef_v": 1.0},
    "Paysandu_Capital": {"Ciudad": "Paysandú", "Afluente": "Río Uruguay", "lat": -32.31, "lon": -58.07, "coef_v": 1.0},
    "RioNegro_FrayBentos": {"Ciudad": "Fray Bentos", "Afluente": "Río Uruguay", "lat": -33.13, "lon": -58.29, "coef_v": 0.8},
    "RioNegro_NuevoBerlin": {"Ciudad": "Nuevo Berlín", "Afluente": "Río Uruguay", "lat": -32.98, "lon": -58.04, "coef_v": 0.8},
    
    # Cuenca del Río Negro y Centro
    "Soriano_Mercedes": {"Ciudad": "Mercedes", "Afluente": "Río Negro", "lat": -33.25, "lon": -58.02, "coef_v": 0.9},
    "Soriano_Dolores": {"Ciudad": "Dolores", "Afluente": "Río San Salvador", "lat": -33.53, "lon": -58.21, "coef_v": 0.9},
    "Soriano_VillaSoriano": {"Ciudad": "Villa Soriano", "Afluente": "Río Negro", "lat": -33.40, "lon": -58.31, "coef_v": 0.8},
    "Durazno_Capital": {"Ciudad": "Durazno", "Afluente": "Río Yí", "lat": -33.38, "lon": -56.52, "coef_v": 1.0},
    "Durazno_SarandiDelYi": {"Ciudad": "Sarandí del Yí", "Afluente": "Río Yí", "lat": -33.34, "lon": -55.62, "coef_v": 0.9},
    "Tacuarembo_PasoDeLosToros": {"Ciudad": "Paso de los Toros", "Afluente": "Río Negro", "lat": -32.81, "lon": -56.51, "coef_v": 0.7},
    "Tacuarembo_Capital": {"Ciudad": "Tacuarembó", "Afluente": "Río Tacuarembó", "lat": -31.71, "lon": -55.98, "coef_v": 0.8},
    "Rivera_Capital": {"Ciudad": "Rivera", "Afluente": "Arroyo Cuñapirú", "lat": -30.90, "lon": -55.53, "coef_v": 0.7},
    
    # Cuenca del Río Santa Lucía y Sur
    "Florida_Capital": {"Ciudad": "Florida", "Afluente": "Río Santa Lucía Chico", "lat": -34.09, "lon": -56.21, "coef_v": 0.9},
    "Florida_25DeAgosto": {"Ciudad": "25 de Agosto", "Afluente": "Río Santa Lucía", "lat": -34.40, "lon": -56.39, "coef_v": 1.0},
    "Canelones_SantaLucia": {"Ciudad": "Santa Lucía", "Afluente": "Río Santa Lucía", "lat": -34.45, "lon": -56.39, "coef_v": 1.0},
    "Canelones_SanRamon": {"Ciudad": "San Ramón", "Afluente": "Río Santa Lucía", "lat": -34.30, "lon": -55.96, "coef_v": 0.9},
    "SanJose_Capital": {"Ciudad": "San José de Mayo", "Afluente": "Río San José", "lat": -34.33, "lon": -56.71, "coef_v": 0.9},
    "SanJose_CiudadDelPlata": {"Ciudad": "Ciudad del Plata", "Afluente": "Río de la Plata / Santa Lucía", "lat": -34.76, "lon": -56.38, "coef_v": 0.8},
    "Colonia_Rosario": {"Ciudad": "Rosario", "Afluente": "Arroyo Colla", "lat": -34.31, "lon": -57.35, "coef_v": 0.8},
    "Colonia_Carmelo": {"Ciudad": "Carmelo", "Afluente": "Arroyo de las Vacas", "lat": -33.99, "lon": -58.28, "coef_v": 0.8},
    
    # Cuenca de la Laguna Merín, Río Cebollatí y Este
    "TreintaYTres_Capital": {"Ciudad": "Treinta y Tres", "Afluente": "Río Olimar", "lat": -33.23, "lon": -54.38, "coef_v": 1.0},
    "TreintaYTres_Charqueada": {"Ciudad": "Gral. Enrique Martínez (Charqueada)", "Afluente": "Río Cebollatí", "lat": -33.20, "lon": -53.80, "coef_v": 1.0},
    "TreintaYTres_Vergara": {"Ciudad": "Vergara", "Afluente": "Arroyo Parao", "lat": -32.93, "lon": -53.89, "coef_v": 0.9},
    "CerroLargo_Melo": {"Ciudad": "Melo", "Afluente": "Arroyo Conventos", "lat": -32.36, "lon": -54.16, "coef_v": 0.8},
    "CerroLargo_RioBranco": {"Ciudad": "Río Branco", "Afluente": "Río Yaguarón", "lat": -32.59, "lon": -53.39, "coef_v": 0.9},
    "Rocha_Capital": {"Ciudad": "Rocha", "Afluente": "Arroyo Rocha", "lat": -34.48, "lon": -54.33, "coef_v": 0.8},
    "Rocha_Cebollati": {"Ciudad": "Cebollatí", "Afluente": "Río Cebollatí", "lat": -33.25, "lon": -53.64, "coef_v": 0.9},
    "Maldonado_SanCarlos": {"Ciudad": "San Carlos", "Afluente": "Arroyo San Carlos", "lat": -34.80, "lon": -54.92, "coef_v": 0.8},
    "Lavalleja_Minas": {"Ciudad": "Minas", "Afluente": "Arroyo San Francisco", "lat": -34.37, "lon": -55.23, "coef_v": 0.7}
}

# --- 2. FUNCIÓN MATEMÁTICA DE INUNDACIÓN ---
def calcular_riesgo_inundacion(lat, lon, coef_v):
    url = "https://api.open-meteo.com/v1/forecast"
    parametros = {
        "latitude": lat, "longitude": lon, 
        "past_days": 14, "forecast_days": 3, # 14 días para atrás (saturación), 3 para adelante (pronóstico)
        "daily": ["precipitation_sum"],
        "timezone": "America/Montevideo"
    }
    try:
        respuesta = requests.get(url, params=parametros)
        df_clima = pd.DataFrame(respuesta.json()["daily"])
        df_clima['precipitation_sum'] = df_clima['precipitation_sum'].fillna(0)
        
        # Separar lluvia histórica (últimos 14 días) y pronóstico (hoy + próximos 2 días)
        # La API devuelve los días pasados primero, luego el pronóstico.
        lluvia_pasada = df_clima['precipitation_sum'].iloc[:-3].sum()
        lluvia_futura = df_clima['precipitation_sum'].iloc[-3:].sum()
        
        # Modelo de Riesgo: Ponderamos más la lluvia pronosticada, pero la pasada actúa de multiplicador base
        # Si el suelo ya está saturado (lluvia_pasada alta), cualquier lluvia futura dispara el riesgo.
        riesgo_base = (lluvia_pasada * 0.3) + (lluvia_futura * 0.7)
        indice_inundacion = riesgo_base * coef_v
        
        # Categorización
        if indice_inundacion < 15: cat = "Normal"
        elif indice_inundacion <= 35: cat = "Alerta Amarilla"
        elif indice_inundacion <= 70: cat = "Alerta Naranja"
        else: cat = "Alerta Roja"
        
        return round(lluvia_pasada, 1), round(lluvia_futura, 1), round(indice_inundacion, 2), cat
    except Exception as e:
        return None, None, None, "Error"

# --- 3. BUCLE DE EJECUCIÓN ---
resultados = []
print("Iniciando monitoreo de cuencas y afluentes (Tomará aprox. 15 segundos)...")

for key, info in monitoreo_hidrico.items():
    pasada, futura, indice, categoria = calcular_riesgo_inundacion(info["lat"], info["lon"], info["coef_v"])
    resultados.append({
        "Ciudad": info["Ciudad"],
        "Afluente": info["Afluente"],
        "Latitud": info["lat"],
        "Longitud": info["lon"],
        "Lluvia_Acumulada_14d": pasada,
        "Pronóstico_3d": futura,
        "Índice_Inundación": indice,
        "Categoría": categoria
    })
    time.sleep(1)

df_hidrico = pd.DataFrame(resultados)

# --- 4. GUARDADO DE ARCHIVO CSV ---
nombre_archivo = "Reporte_Riesgo_Inundaciones.csv"
df_hidrico.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')

print(f"\n¡Análisis completado! Archivo '{nombre_archivo}' guardado.")
print(df_hidrico[['Ciudad', 'Afluente', 'Índice_Inundación', 'Categoría']].head(15))

import folium

import plotly.express as px
import folium
import streamlit as st
import streamlit.components.v1 as components

# --- 1. TÍTULO DEL PANEL EN LA WEB ---
st.title("🚨 Radar de Riesgo Hídrico - Uruguay")
st.markdown("Monitor de saturación de suelo y pronóstico de lluvias a 3 días.")

# --- 2. GRÁFICO DE DISPERSIÓN EN STREAMLIT ---
fig_scatter = px.scatter(
    df_hidrico, 
    x="Lluvia_Acumulada_14d", 
    y="Pronóstico_3d", 
    color="Categoría", 
    hover_name="Ciudad", 
    hover_data=["Afluente", "Índice_Inundación"], 
    title="Análisis Táctico: Saturación vs Lluvia Inminente",
    color_discrete_map={
        "Normal": "green", 
        "Alerta Amarilla": "gold", 
        "Alerta Naranja": "darkorange", 
        "Alerta Roja": "darkred"
    },
    height=500
)

# Comando nativo de Streamlit para dibujar gráficos
st.plotly_chart(fig_scatter, use_container_width=True)

# --- 3. MAPA INTERACTIVO DE INUNDACIONES ---
st.subheader("🗺️ Despliegue Geográfico de Alertas")

# Creamos el lienzo del mapa
mapa_inundaciones = folium.Map(location=[-32.5, -56.0], zoom_start=6)

colores_mapa = {
    "Normal": "green", 
    "Alerta Amarilla": "orange", 
    "Alerta Naranja": "red", 
    "Alerta Roja": "darkred"
}

# Pegamos los puntos encima con el bucle
for index, fila in df_hidrico.iterrows():
    # El círculo de color interactivo
    folium.CircleMarker(
        location=[fila['Latitud'], fila['Longitud']],
        radius=10,
        tooltip=f"<b>{fila['Ciudad']}</b><br>Río: {fila['Afluente']}<br>Índice: {fila['Índice_Inundación']}<br>Estado: <b>{fila['Categoría']}</b>",
        color=colores_mapa.get(fila['Categoría'], "gray"),
        fill=True,
        fill_opacity=0.7
    ).add_to(mapa_inundaciones)
    
    # El número permanente flotando en el mapa
    folium.Marker(
        location=[fila['Latitud'], fila['Longitud']],
        icon=folium.DivIcon(
            html=f'<div style="font-size: 11pt; font-weight: bold; color: black; text-shadow: 1px 1px 3px white; margin-left: 15px; margin-top: -10px;">{fila["Índice_Inundación"]}</div>'
        )
    ).add_to(mapa_inundaciones)

# --- 4. DIBUJAR MAPA EN LA WEB ---
# Le ordenamos a Streamlit que muestre el mapa terminado
components.html(mapa_inundaciones._repr_html_(), height=650)

# --- CREACIÓN DEL MAPA DE INUNDACIONES ---
# Centramos el mapa en Uruguay
mapa_inundaciones = folium.Map(location=[-32.5, -56.0], zoom_start=6)

# Definimos los colores de alerta hidrológica
colores_hidricos = {
    "Normal": "green", 
    "Alerta Amarilla": "orange", 
    "Alerta Naranja": "red", 
    "Alerta Roja": "darkred"
}

# Recorremos la base de datos y ponemos los marcadores
for index, fila in df_hidrico.iterrows():
    folium.CircleMarker(
        location=[fila['Latitud'], fila['Longitud']],
        radius=10, # Tamaño del círculo
        popup=f"<b>{fila['Ciudad']}</b><br>Río/Arroyo: {fila['Afluente']}<br>Índice de Saturación: {fila['Índice_Inundación']}<br>Estado: <b>{fila['Categoría']}</b>",
        color=colores_hidricos.get(fila['Categoría'], "gray"),
        fill=True,
        fill_opacity=0.7
    ).add_to(mapa_inundaciones)

# --- FORZAR LA VISUALIZACIÓN EN COLAB ---
from IPython.display import display

# Forzamos la representación visual directa del objeto
display(mapa_inundaciones)
# Guardamos el archivo y lo incrustamos a la fuerza
archivo_mapa = "mapa_hidrico_tactico.html"
mapa_inundaciones.save(archivo_mapa)
IPython.display.HTML(filename=archivo_mapa)
import folium
from IPython.display import display

# --- CREACIÓN DEL MAPA TÁCTICO DE INUNDACIONES (MEJORADO) ---
mapa_inundaciones = folium.Map(location=[-32.5, -56.0], zoom_start=6)

colores_hidricos = {
    "Normal": "green", 
    "Alerta Amarilla": "orange", 
    "Alerta Naranja": "red", 
    "Alerta Roja": "darkred"
}

for index, fila in df_hidrico.iterrows():
    # 1. El círculo de color (ahora usa 'tooltip' para activarse al pasar el ratón)
    folium.CircleMarker(
        location=[fila['Latitud'], fila['Longitud']],
        radius=10,
        tooltip=f"<b>{fila['Ciudad']}</b><br>Río: {fila['Afluente']}<br>Índice: {fila['Índice_Inundación']}<br>Estado: <b>{fila['Categoría']}</b>",
        color=colores_hidricos.get(fila['Categoría'], "gray"),
        fill=True,
        fill_opacity=0.7
    ).add_to(mapa_inundaciones)
    
    # 2. El número permanente (se dibuja directamente sobre el mapa)
    folium.Marker(
        location=[fila['Latitud'], fila['Longitud']],
        icon=folium.DivIcon(
            html=f'<div style="font-size: 11pt; font-weight: bold; color: black; text-shadow: 1px 1px 3px white; margin-left: 15px; margin-top: -10px;">{fila["Índice_Inundación"]}</div>'
        )
    ).add_to(mapa_inundaciones)

# Forzamos la visualización directa en Colab
display(mapa_inundaciones)
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import folium
# ... (tus otros imports)

# 1. Configuración de la página (Debe ser el primer comando de Streamlit)
st.set_page_config(page_title="Radar de Riesgo", page_icon="🚨", layout="wide")

# --- 2. INYECCIÓN DE GOOGLE ANALYTICS ---
# Reemplaza 'G-XXXXXXXXXX' con el código que copiaste en el Paso 1
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
# Insertamos el código de rastreo en un contenedor de tamaño cero (invisible)
components.html(ga_script, height=0, width=0)
# ---------------------------------------

# 3. El resto de tu aplicación web
st.title("🔥 Panel de Monitoreo de Riesgos")
# ... (tu código para calcular y mostrar mapas) ...
