# -- coding: utf-8 --
"""
Created on Wed Sep 11 12:54:30 2024

@author: JaviyKarla
"""

import pandas as pd
import numpy as np
import folium
import webbrowser
from folium.plugins import MarkerCluster
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from keras.models import Sequential
from keras.layers import Dense
from sklearn.linear_model import LogisticRegression

# Coordenadas de las zonas de interés en Aguascalientes
puntos_zonas = {
    "Centro": (21.8853, -102.2920),
    "San Marcos Barrio": (21.8785, -102.2920),
    "Américas Las Fracc.": (21.8838, -102.2880),
    "Municipio Libre Fracc.": (21.8950, -102.3090),
    "Haciendas de Aguascalientes Fracc.": (21.8670, -102.3050),
    "Morelos I Fracc.": (21.8900, -102.2840),
    "Gremial Col.": (21.8840, -102.3070),
    "Ojocaliente I Fracc.": (21.8735, -102.2970),
    "Flores Las Col.": (21.8830, -102.2750),
    "Pilar Blanco Infonavit": (21.8930, -102.2920),
    "San Cayetano Fracc.": (21.8790, -102.2980),
    "Insurgentes Col. (Las Huertas)": (21.8795, -102.3080),
    "Guadalupe de Barrio": (21.8820, -102.3010),
    "Morelos Infonavit": (21.8890, -102.2900),
    "Circunvalación Norte Fracc.": (21.8955, -102.3055),
    "San Marcos Col.": (21.8770, -102.2870),
    "Rodolfo Landeros Fracc.": (21.8630, -102.3070),
    "Obraje Col.": (21.8845, -102.2760),
    "Santa Anita 1era Secc. Fracc.": (21.8820, -102.3030),
    "Trabajo del Col.": (21.8885, -102.2960),
    "José Guadalupe Peralta Fracc.": (21.8615, -102.3080),
    "Dorado El 1era Secc. Fracc.": (21.8620, -102.2950),
    "Purísima La Barrio": (21.8650, -102.3000),
    "Ojocaliente III Fracc.": (21.8730, -102.3075),
    "Colinas del Río Fracc.": (21.8690, -102.2875),
    "España Fracc.": (21.8850, -102.2950),
    "Industrial Col.": (21.8700, -102.2950),
    "Arboledas Las Fracc.": (21.8820, -102.2880),
    "Villas de Ntra. Sra. de la Asunción Sec Estacion Fracc.": (21.8920, -102.3095),
    "Bosques del Prado Sur Fracc.": (21.8925, -102.3010)
}

# Definir puntos de salida o rutas de escape
puntos_esc = {
    "Plaza Patria": (21.8871, -102.2845),
    "Centro Comercial Altaria": (21.9003, -102.2881),
    "Parque de los Descubrimientos": (21.8837, -102.3015),
    "Plaza de la Patria": (21.8866, -102.2850),
    "Biblioteca Pública": (21.8953, -102.3060)
}

# Datos de riesgo
datos_riesgo = {
    "Centro": 60,
    "San Marcos Barrio": 50,
    "Américas Las Fracc.": 45,
    "Municipio Libre Fracc.": 70,
    "Haciendas de Aguascalientes Fracc.": 30,
    "Morelos I Fracc.": 40,
    "Gremial Col.": 35,
    "Ojocaliente I Fracc.": 65,
    "Flores Las Col.": 25,
    "Pilar Blanco Infonavit": 50,
    "San Cayetano Fracc.": 40,
    "Insurgentes Col. (Las Huertas)": 60,
    "Guadalupe de Barrio": 35,
    "Morelos Infonavit": 55,
    "Circunvalación Norte Fracc.": 50,
    "San Marcos Col.": 45,
    "Rodolfo Landeros Fracc.": 70,
    "Obraje Col.": 40,
    "Santa Anita 1era Secc. Fracc.": 55,
    "Trabajo del Col.": 35,
    "José Guadalupe Peralta Fracc.": 65,
    "Dorado El 1era Secc. Fracc.": 45,
    "Purísima La Barrio": 25,
    "Ojocaliente III Fracc.": 55,
    "Colinas del Río Fracc.": 30,
    "España Fracc.": 60,
    "Industrial Col.": 50,
    "Arboledas Las Fracc.": 55,
    "Villas de Ntra. Sra. de la Asunción Sec Estacion Fracc.": (21.8920, -102.3095),
    "Bosques del Prado Sur Fracc.": 35
}

# Crear un dataframe para el modelo
data = pd.DataFrame(list(datos_riesgo.items()), columns=['Zona', 'Riesgo'])

# Dividir los datos en características (X) y etiquetas (y)
X = data['Riesgo'].values.reshape(-1, 1)
y = np.random.rand(len(X)) * 100  # Simular algún valor de salida

# Dividir el conjunto de datos en entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Crear el modelo de regresión neuronal
modelo = Sequential()
modelo.add(Dense(10, input_dim=1, activation='relu'))
modelo.add(Dense(1))

# Compilar el modelo
modelo.compile(loss='mean_squared_error', optimizer='adam')

# Entrenar el modelo
modelo.fit(X_train, y_train, epochs=100, verbose=1)

# Realizar predicciones
y_pred = modelo.predict(X_test)

# Calcular el error cuadrático medio
mse = mean_squared_error(y_test, y_pred)
print(f'Error cuadrático medio: {mse:.2f}')

# --- Análisis de Riesgo con Regresión Logística ---
X_logistic = data['Riesgo'].values.reshape(-1, 1)
y_logistic = (data['Riesgo'].values > 50).astype(int)  # Clasificación (1= alto riesgo, 0= bajo riesgo)

# Dividir el conjunto de datos en entrenamiento y prueba
X_train_logistic, X_test_logistic, y_train_logistic, y_test_logistic = train_test_split(X_logistic, y_logistic, test_size=0.2, random_state=42)

# Crear el modelo de regresión logística
modelo_logistico = LogisticRegression()
modelo_logistico.fit(X_train_logistic, y_train_logistic)

# Predicciones y cálculo de probabilidades
probabilidades = modelo_logistico.predict_proba(X_test_logistic)[:, 1]
for zona, prob in zip(data['Zona'].values[X_test_logistic.flatten().argsort()], np.sort(probabilidades)):
    print(f'Zona: {zona}, Probabilidad de riesgo alto: {prob:.2f}')

# --- Visualización de los Resultados ---
mapa = folium.Map(location=[21.8853, -102.2920], zoom_start=13)

# Añadir marcadores para cada zona
for zona, coords in puntos_zonas.items():
    riesgo = datos_riesgo.get(zona, 'Riesgo no encontrado')
    
    # Determinar el color basado en el riesgo
    if riesgo >= 60:
        color = 'red'
    elif 40 <= riesgo < 60:
        color = 'orange'
    else:
        color = 'green'
    
  

    # Añadir el marcador al mapa
    folium.Marker(location=coords, popup=f'{zona} - Riesgo: {riesgo}', icon=folium.Icon(color=color)).add_to(mapa)

# Guardar el mapa en un archivo HTML y abrirlo en el navegador
nombre_archivo = 'mapa_aguascalientes.html'
mapa.save('mapa_aguascalientes.html')

# Abrir el archivo HTML en el navegador
webbrowser.open('mapa_aguascalientes.html')
