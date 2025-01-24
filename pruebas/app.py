from flask import Flask, render_template, send_from_directory,request,send_file
from flask_socketio import SocketIO, emit
import json
import re
from IA_simpd import graficar_datos,obtener_conexion,exportar_datos_a_excel
import math
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'

socketio = SocketIO(app)



def cargar_puntos_zonas():
    with open(r'C:\Users\Administrator\Documents\SIMPD\SIMPD\pruebas\colonias_modificado.json', 'r') as archivo:
        return json.load(archivo)
    
def ubicaciones_camaras():
    with open(r'C:\Users\Administrator\Documents\SIMPD\SIMPD\pruebas\ubicaciones_camaras.json', 'r') as archivo:
        return json.load(archivo)

puntos_zonas = cargar_puntos_zonas()


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
    "Villas de Ntra. Sra. de la Asunción Sec Estacion Fracc.": 35,
    "Bosques del Prado Sur Fracc.": 35
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/camara')
def camara():
    return render_template('camara.html')

@socketio.on('mostrar_zonas_riesgo')
def handle_mostrar_zonas_riesgo():
    zonas_con_riesgo = []
    for colonia in puntos_zonas:
        nombre = colonia['nombre_colonia']
        lat = colonia['centro'][1]  
        lng = colonia['centro'][0]  
        riesgo = colonia['riesgo']
        zonas_con_riesgo.append({'nombre': nombre, 'lat': lat, 'lng': lng, 'riesgo': riesgo})
        

    bajo = []
    moderado = []
    alto = []
    muy_alto = []


    for colonia in puntos_zonas:
        nombre = colonia['nombre_colonia']
        lat = colonia['centro'][1]  
        lng = colonia['centro'][0]  
        riesgo = colonia['riesgo']  

    
        if 0 <= riesgo <= 25:
            bajo.append({'nombre': nombre, 'lat': lat, 'lng': lng, 'riesgo': riesgo})
        elif 26 <= riesgo <= 50:
            moderado.append({'nombre': nombre, 'lat': lat, 'lng': lng, 'riesgo': riesgo})
        elif 51 <= riesgo <= 75:
            alto.append({'nombre': nombre, 'lat': lat, 'lng': lng, 'riesgo': riesgo})
        elif 76 <= riesgo <= 100:
            muy_alto.append({'nombre': nombre, 'lat': lat, 'lng': lng, 'riesgo': riesgo})

 
    
    print("Bajo:")
    print("Moderado:")
    print("Alto:")
    print("Muy Alto:")


    
    socketio.emit('zonas_riesgo', zonas_con_riesgo)
    
import math

def calcular_distancia(coord1, coord2):
    R = 6371 
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))

    return R * c  
    
@app.route('/mapa/<int:opcion>')
def mapa(opcion):
    
    zonas_con_riesgo = []
    for colonia in puntos_zonas:
        nombre = colonia['nombre_colonia']
        lat = colonia['centro'][1]  
        lng = colonia['centro'][0]
        riesgo = colonia['riesgo']
        zonas_con_riesgo.append({'nombre': nombre, 'lat': lat, 'lng': lng, 'riesgo': riesgo})
        

    bajo = []
    moderado = []
    alto = []
    muy_alto = []

    for colonia in puntos_zonas:
        nombre = colonia['nombre_colonia']
        lat = colonia['centro'][1] 
        lng = colonia['centro'][0]  
        riesgo = colonia['riesgo']  

        if 0 <= riesgo <= 25:
            bajo.append({'nombre': nombre, 'lat': lat, 'lng': lng, 'riesgo': riesgo})
        elif 26 <= riesgo <= 50:
            moderado.append({'nombre': nombre, 'lat': lat, 'lng': lng, 'riesgo': riesgo})
        elif 51 <= riesgo <= 75:
            alto.append({'nombre': nombre, 'lat': lat, 'lng': lng, 'riesgo': riesgo})
        elif 76 <= riesgo <= 100:
            muy_alto.append({'nombre': nombre, 'lat': lat, 'lng': lng, 'riesgo': riesgo})

    if opcion == 1:
        return render_template('mapa.html', lista=bajo)
    elif opcion==2:
        return render_template('mapa.html', lista=moderado)
    elif opcion==3:
        return render_template('mapa.html', lista=alto)
    elif opcion==4:
        return render_template('mapa.html', lista=alto)
    else:
        return render_template('mapa.html', lista=zonas_con_riesgo)
        

@socketio.on('search')
def handle_search(query):
    results = [colonia for colonia in puntos_zonas if query.lower() in colonia['nombre_colonia'].lower()]
    socketio.emit('search_results', results)

@socketio.on('ruta_cambiada')
def handle_ruta_cambiada(data):
    distancia = data.get('distancia')
    duracion = data.get('duracion')
    waypoints = data.get('waypoints')
    calles = data.get('calles') 


    calles_str = "Calles por las que pasa la ruta:\n"


    for calle in calles:
        calles_str += calle + '\n'  

def separate_by_street(text):
    lines = text.strip().split('\n') 
    streets = []
    
    for line in lines:
        match = re.search(r'\b(C|A)\w+.*', line)
        if match:
            street = match.group(0)  
            streets.append(street)
    
    return streets
    
@socketio.on('waypoint_dragged')
def handle_waypoint_dragged(data):
    waypoints = data['waypoints']
    print("Puntos de control actualizados:", waypoints)
    
    
@app.route('/estadisticas/<int:opcion>', methods=['GET', 'POST'])
def estadisticas(opcion):
    BD = []
    cursor = None
    conexion = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT nombre, riesgo FROM zonas ORDER BY riesgo DESC;")
        BD = cursor.fetchall()
    except Exception as e:
        print("Error connecting to the database or executing query:", e)
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

    # Prepare data for rendering
    nombres1 = [c[0] for c in BD]
    riesgos1 = [c[1] for c in BD]
    combinados = list(zip(nombres1, riesgos1))
    img1 = graficar_datos(opcion)

    if request.method == 'POST':
        # Handle Excel download request
        archivo_generado = exportar_datos_a_excel(opcion)  # Call your function to generate Excel
        
        # Check if the file was generated successfully
        if archivo_generado and os.path.exists(archivo_generado):
            return send_file(archivo_generado, as_attachment=True)
        else:
            error_message = "Error generating the Excel file."
            print(error_message)
            return error_message, 500

    # Render the template with the required context
    return render_template('estadisticas.html', img=img1, combinados=combinados, opcion=opcion)




@socketio.on('enviar_coordenadas')
def handle_coordinates(data):
    lat = data['lat']
    lon = data['lng']
    radio = 1  

    camaras = ubicaciones_camaras()

    camaras_cercanas = []
    for camara in camaras:
        try:
            camara_coord = (camara['lat'], camara['lon'])
            distancia = calcular_distancia((lat, lon), camara_coord)

            if distancia <= radio:
                camaras_cercanas.append(camara)
        except KeyError:
            print(f"Cámara con id {camara.get('id')} no tiene coordenadas válidas.")
            continue


    socketio.emit('camaras_cercanas', camaras_cercanas)



if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
