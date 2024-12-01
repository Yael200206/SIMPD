from flask import Flask, render_template_string, request
import pandas as pd
import folium
import matplotlib.pyplot as plt
import io
import base64
import mysql.connector
import datetime
import openpyxl



# Inicializar la aplicación Flask
app = Flask(__name__)

# Configuración de la conexión a la base de datos
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'zona_de_riesgo'
}

# Crear la conexión a la base de datos
def obtener_conexion():
    return mysql.connector.connect(**db_config)

def crear_base_de_datos():
    """Crea la base de datos y las tablas si no existen."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    # Crear base de datos
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
    cursor.execute(f"USE {db_config['database']}")

    # Crear tabla 'zonas'
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS zonas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            riesgo INT NOT NULL,
            latitud FLOAT NOT NULL,
            longitud FLOAT NOT NULL
        )
    ''')

    # Crear tabla 'probabilidad_asalto'
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS probabilidad_asalto (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            probabilidad FLOAT NOT NULL
        )
    ''')

    # Crear tabla 'peligro_zonas'
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS peligro_zonas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            porcentaje INT NOT NULL
        )
    ''')

    # Crear tabla 'graficas' con columna imagen como TEXT
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS graficas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            opcion INT NOT NULL,
            imagen TEXT NOT NULL
        )
    ''')
    
    cursor.close()
    conexion.close()

def cargar_zonas_a_db():
    """Carga las zonas de riesgo, probabilidades de asalto y peligrosidad en la base de datos."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    PUNTOS_ZONAS = {
        "centro": (21.8842637, -102.3134514),
        "san marcos barrio": (21.8818817, -102.3122746),
        "americas las fracc.": (21.8173776, -102.1151153),
        "municipio libre fracc.": (21.8954463, -102.2689912),
        "haciendas de aguascalientes fracc.": (21.8883146, -102.2533752),
        "morelos i fracc.": (21.8559395, -102.269382),
        "gremial col.": (21.8953131, -102.2984856),
        "ojocaliente i fracc.": (21.8851666, -102.2591437),
        "flores las col.": (21.8965786, -102.2835921),
        "pilar blanco infonavit": (21.8501643, -102.3074635)
    }

    DATOS_RIESGO = {
        "centro": 60,
        "san marcos barrio": 55,
        "americas las fracc.": 45,
        "municipio libre fracc.": 50,
        "haciendas de aguascalientes fracc.": 40,
        "morelos i fracc.": 35,
        "gremial col.": 30,
        "ojocaliente i fracc.": 30,
        "flores las col.": 20,
        "pilar blanco infonavit": 25
    }

    PROBABILIDAD_ASALTO = {
        "centro": 70.0,
        "san marcos barrio": 60.0,
        "americas las fracc.": 40.0,
        "municipio libre fracc.": 45.0,
        "haciendas de aguascalientes fracc.": 35.0,
        "morelos i fracc.": 25.0,
        "gremial col.": 30.0,
        "ojocaliente i fracc.": 20.0,
        "flores las col.": 15.0,
        "pilar blanco infonavit": 18.0
    }

    PELIGRO_ZONAS = {
        "centro": 85,
        "san marcos barrio": 75,
        "americas las fracc.": 60,
        "municipio libre fracc.": 55,
        "haciendas de aguascalientes fracc.": 50,
        "morelos i fracc.": 45,
        "gremial col.": 35,
        "ojocaliente i fracc.": 25,
        "flores las col.": 20,
        "pilar blanco infonavit": 30
    }

    # Limpiar las tablas antes de insertar datos
    cursor.execute("DELETE FROM zonas")
    cursor.execute("DELETE FROM probabilidad_asalto")
    cursor.execute("DELETE FROM peligro_zonas")

    for zona, coords in PUNTOS_ZONAS.items():
        riesgo = DATOS_RIESGO[zona]
        prob_asalto = PROBABILIDAD_ASALTO[zona]
        peligro = PELIGRO_ZONAS[zona]

        # Insertar datos en la tabla zonas
        query_zona = "INSERT INTO zonas (nombre, riesgo, latitud, longitud) VALUES (%s, %s, %s, %s)"
        cursor.execute(query_zona, (zona, riesgo, coords[0], coords[1]))

        # Insertar datos en la tabla probabilidad_asalto
        query_asalto = "INSERT INTO probabilidad_asalto (nombre, probabilidad) VALUES (%s, %s)"
        cursor.execute(query_asalto, (zona, prob_asalto))

        # Insertar datos en la tabla peligro_zonas
        query_peligro = "INSERT INTO peligro_zonas (nombre, porcentaje) VALUES (%s, %s)"
        cursor.execute(query_peligro, (zona, peligro))

    conexion.commit()
    cursor.close()
    conexion.close()

@app.route('/')
def index():
    return render_template_string(''' 
        <html>
            <head>
                <title>SIMPD - Mapa de Riesgo</title>
                <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
                <style>
                    body {
                        font-family: 'Roboto', sans-serif;
                        background-color: #f0f4f8;
                        color: #333;
                        text-align: center;
                        padding: 30px;
                        margin: 0;
                    }
                    h1 {
                        color: #4A90E2;
                        font-size: 2.5em;
                        margin-bottom: 10px;
                    }
                    h2 {
                        color: #E94E77;
                        font-size: 1.5em;
                        margin-bottom: 20px;
                    }
                    select, button {
                        padding: 12px;
                        margin: 10px 0;
                        border: 2px solid #4A90E2;
                        border-radius: 5px;
                        font-size: 1em;
                    }
                    button {
                        background-color: #4A90E2;
                        color: white;
                        cursor: pointer;
                    }
                    button:hover {
                        background-color: #357ABD;
                    }
                </style>
            </head>
            <body>
                <h1>Sistema de Monitoreo de Puntos de Riesgo</h1>
                <h2><a href="/mapa" target="_blank">Ver Mapa de Riesgo</a></h2>
                <form action="/grafica" method="POST">
                    <select name="opcion">
                        <option value="1">Gráfica 1: Nivel de Riesgo y Probabilidad de Asalto</option>
                        <option value="2">Gráfica 2: Proporción de Niveles de Riesgo</option>
                        <option value="3">Gráfica 3: Peligro de Zonas</option>
                    </select>
                    <button type="submit">Ver Gráfica</button>
                </form>
            </body>
        </html>
    ''')

@app.route('/grafica', methods=['POST'])
def grafica():
    opcion = int(request.form.get('opcion'))
    img = graficar_datos(opcion)
    return render_template_string(''' 
        <html>
            <head>
                <title>Gráfica {{ opcion }}</title>
            </head>
            <body>
                <h1>Gráfica {{ opcion }}</h1>
                <img src="data:image/png;base64,{{ img }}" alt="Gráfica">
                <br>
                <a href="/">Volver al Menú</a>
            </body>
        </html>
    ''', img=img, opcion=opcion)

def graficar_datos(opcion):
    plt.clf()  # Limpiar la figura actual
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    if opcion == 1:
        cursor.execute("SELECT zonas.nombre, zonas.riesgo, probabilidad_asalto.probabilidad FROM zonas JOIN probabilidad_asalto ON zonas.nombre = probabilidad_asalto.nombre")
        datos = cursor.fetchall()
        nombres = [d[0] for d in datos]
        riesgos = [d[1] for d in datos]
        prob_asalto = [d[2] for d in datos]

        # Gráfica 1: Nivel de Riesgo por Zona y Probabilidad de Asalto
        plt.figure(figsize=(10, 5))
        plt.bar(nombres, riesgos, color='lightblue', label='Nivel de Riesgo')
        plt.bar(nombres, prob_asalto, color='orange', alpha=0.7, label='Probabilidad de Asalto')
        plt.axhline(y=50, color='red', linestyle='--', label='Umbral de Riesgo')
        plt.title('Nivel de Riesgo y Probabilidad de Asalto por Zona')
        plt.xlabel('Zonas')
        plt.ylabel('Nivel de Riesgo / Probabilidad (%)')
        plt.xticks(rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
    elif opcion == 2:
        cursor.execute("SELECT riesgo FROM zonas")
        riesgos = [d[0] for d in cursor.fetchall()]
        niveles_riesgo = pd.cut(riesgos, bins=[0, 40, 60, 100], labels=['Bajo', 'Moderado', 'Alto'])
        conteo_niveles = niveles_riesgo.value_counts()

        # Gráfica 2: Proporción de Niveles de Riesgo
        plt.figure(figsize=(8, 6))
        plt.pie(conteo_niveles, labels=conteo_niveles.index, autopct='%1.1f%%', startangle=90)
        plt.title('Proporción de Zonas en Diferentes Niveles de Riesgo')
        plt.axis('equal')
    elif opcion == 3:
        cursor.execute("SELECT nombre, porcentaje FROM peligro_zonas")
        datos = cursor.fetchall()
        nombres = [d[0] for d in datos]
        porcentaje_peligro = [d[1] for d in datos]

        # Gráfica 3: Peligro de Zonas
        plt.figure(figsize=(10, 5))
        plt.bar(nombres, porcentaje_peligro, color='red')
        plt.title('Peligro de Zonas (1-100%)')
        plt.xlabel('Zonas')
        plt.ylabel('Porcentaje de Peligro (%)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

    cursor.close()
    conexion.close()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    img = base64.b64encode(buf.getvalue()).decode('utf8')
    return img

def exportar_datos_a_excel(opcion):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    fecha_hoy = datetime.datetime.now().strftime('%Y-%m-%d')
    nombre_archivo = f"datos_{fecha_hoy}.xlsx"

    if opcion == 1:
        cursor.execute("SELECT zonas.nombre, zonas.riesgo, probabilidad_asalto.probabilidad FROM zonas JOIN probabilidad_asalto ON zonas.nombre = probabilidad_asalto.nombre")
        datos = cursor.fetchall()
        df = pd.DataFrame(datos, columns=['Zona', 'Riesgo', 'Probabilidad de Asalto'])
    elif opcion == 2:
        cursor.execute("SELECT riesgo FROM zonas")
        riesgos = [d[0] for d in cursor.fetchall()]
        niveles_riesgo = pd.cut(riesgos, bins=[0, 40, 60, 100], labels=['Bajo', 'Moderado', 'Alto'])
        conteo_niveles = niveles_riesgo.value_counts().reset_index()
        conteo_niveles.columns = ['Nivel de Riesgo', 'Conteo']
        df = conteo_niveles
    elif opcion == 3:
        cursor.execute("SELECT nombre, porcentaje FROM peligro_zonas")
        datos = cursor.fetchall()
        df = pd.DataFrame(datos, columns=['Zona', 'Porcentaje de Peligro'])

    # Save the DataFrame to an Excel file
    df.to_excel(nombre_archivo, index=False)

    cursor.close()
    conexion.close()

    return nombre_archivo
if __name__ == "__main__":
    crear_base_de_datos()
    cargar_zonas_a_db()
    app.run(debug=True)