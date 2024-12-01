import pandas as pd
import numpy as np
import folium
import webbrowser
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
    # (otros puntos)
}

# Datos de riesgo
datos_riesgo = {
    "Centro": 60,
    "San Marcos Barrio": 50,
    "Américas Las Fracc.": 45,
    # (otros datos)
}

# Crear un dataframe para el modelo
data = pd.DataFrame(list(datos_riesgo.items()), columns=['Zona', 'Riesgo'])

# Dividir los datos en características (X) y etiquetas (y)
X = data['Riesgo'].values.reshape(-1, 1).astype(np.float32)  # Asegurarse de que sea un tipo numérico
y = (data['Riesgo'].values > 50).astype(int)  # Clasificación (1= alto riesgo, 0= bajo riesgo)

# Verificar que hay al menos una muestra de cada clase
if len(np.unique(y)) < 2:
    raise ValueError("No hay suficientes clases en los datos para entrenar el modelo de regresión logística.")

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

# Calcular el error cuadrático medio solo si hay datos de prueba
if len(y_test) > 0:
    mse = mean_squared_error(y_test, y_pred)
    print(f'Error cuadrático medio: {mse:.2f}')

# --- Análisis de Riesgo con Regresión Logística ---
X_logistic = data['Riesgo'].values.reshape(-1, 1).astype(np.float32)  # Asegurarse de que sea un tipo numérico
y_logistic = (data['Riesgo'].values > 50).astype(int)  # Clasificación (1= alto riesgo, 0= bajo riesgo)

# Verificar que hay al menos una muestra de cada clase
if len(np.unique(y_logistic)) < 2:
    print("No hay suficientes clases en los datos para entrenar el modelo de regresión logística.")
else:
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
mapa.save('mapa_aguascalientes.html')
webbrowser.open('mapa_aguascalientes.html')


