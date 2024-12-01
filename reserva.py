import cv2
import torch
import tkinter as tk
from tkinter import StringVar
from threading import Thread
import numpy as np

# Cargar el modelo preentrenado YOLOv5 (usando la versión pequeña para mejor rendimiento)
modelo = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

class AplicacionDetector:
    def __init__(self, root):
        self.root = root
        self.root.title("Detección de Objetos")
        
        # Variables
        self.tipo_objeto = StringVar(value="car")  # Tipo de objeto inicial (auto, persona, etc.)
        self.color_objeto = StringVar(value="")     # Color de objeto inicial
        self.ejecutando = True  # Controla la ejecución del hilo de la cámara
        self.detectando = True  # Indica si está detectando objetos
        self.contador_frames = 0  # Contador para reducir la frecuencia de detección
        self.ultimo_frame = None  # Almacenar el último frame con detección

        # Interfaz gráfica
        self.cuadro_camara = tk.Label(self.root)
        self.cuadro_camara.grid(row=0, column=0, columnspan=3)
        
        # Selección del tipo de objeto
        tk.Label(self.root, text="Tipo de objeto:").grid(row=1, column=0)
        self.tipo_objeto_menu = tk.OptionMenu(self.root, self.tipo_objeto, "auto", "moto", "autobus", "persona")
        self.tipo_objeto_menu.grid(row=1, column=1)
        
        # Selección de color
        tk.Label(self.root, text="Color:").grid(row=2, column=0)
        self.color_objeto_menu = tk.OptionMenu(self.root, self.color_objeto, "Rojo", "Naranja", "Amarillo", "Verde", 
                                               "Azul", "Morado", "Negro", "Blanco", "Gris")
        self.color_objeto_menu.grid(row=2, column=1)
        
        # Botones de control
        tk.Button(self.root, text="Actualizar búsqueda", command=self.actualizar_busqueda).grid(row=3, column=2)
        tk.Button(self.root, text="Limpiar búsqueda", command=self.limpiar_busqueda).grid(row=3, column=1)

        # Crear ventana secundaria para mostrar el último frame con detección
        self.ventana_secundaria = tk.Toplevel(self.root)
        self.ventana_secundaria.title("Último Frame con Detección")
        self.label_secundario = tk.Label(self.ventana_secundaria)
        self.label_secundario.grid(row=0, column=0)

        # Hilo para mostrar la cámara
        self.hilo_camara = Thread(target=self.mostrar_camara, daemon=True)
        self.hilo_camara.start()
    
    def actualizar_busqueda(self):
        """Actualiza el tipo y color de objeto a buscar."""
        self.detectando = True

    def limpiar_busqueda(self):
        """Limpia las detecciones."""
        self.tipo_objeto.set("")
        self.color_objeto.set("")
        self.detectando = False

    def filtrar_objetos(self, detecciones):
        """Filtra las detecciones según el tipo y color del objeto."""
        filtrados = []
        tipo_buscar = self.tipo_objeto.get().lower()
        color_buscar = self.color_objeto.get().lower()
        
        # Mapeo de tipos de objetos
        mapeo_tipo = {
            "auto": ["car", "truck", "suv"],  # Mapeo para "auto"
            "moto": ["motorcycle"],            # Mapeo para "moto"
            "autobus": ["bus"],                # Mapeo para "autobus"
            "persona": ["person"],             # Mapeo para "persona"
        }
        etiquetas_validas = mapeo_tipo.get(tipo_buscar, [])
        
        for det in detecciones:
            etiqueta = det['name']
            if etiqueta in etiquetas_validas:
                color_det = det.get('color', "").lower()
                if color_buscar in color_det:  # Coincidencia parcial de color
                    filtrados.append(det)
        return filtrados

    def obtener_color_objeto(self, frame, x1, y1, x2, y2):
        """Determina el color dominante de un objeto (vehículo o persona)."""
        roi = frame[y1:y2, x1:x2]  # Región de interés
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Máscara para excluir colores oscuros o blancos
        mascara = cv2.inRange(hsv_roi, (0, 30, 30), (180, 255, 255))
        roi_enmascarado = cv2.bitwise_and(hsv_roi, hsv_roi, mask=mascara)
        
        # Histograma para calcular el color dominante
        hist = cv2.calcHist([roi_enmascarado], [0], mascara, [180], [0, 180])
        tono_dominante = np.argmax(hist)
        
        # Determinar el color basado en el tono dominante
        if 0 <= tono_dominante <= 10 or 160 <= tono_dominante <= 180:
            return "Rojo"
        elif 11 <= tono_dominante <= 25:
            return "Naranja"
        elif 26 <= tono_dominante <= 34:
            return "Amarillo"
        elif 35 <= tono_dominante <= 85:
            return "Verde"
        elif 86 <= tono_dominante <= 125:
            return "Azul"
        elif 126 <= tono_dominante <= 159:
            return "Morado"
        elif 0 <= tono_dominante <= 180 and cv2.norm(roi, cv2.NORM_L2) < 100:
            # Rango de colores oscuros, posiblemente negro o gris
            return "Negro" if np.mean(roi) < 60 else "Gris"
        elif 0 <= tono_dominante <= 10 and np.mean(roi) > 180:
            # Rango de colores claros, posiblemente blanco
            return "Blanco"
        else:
            return "Desconocido"

    def mostrar_camara(self):
        """Muestra la cámara y aplica detección."""
        cap = cv2.VideoCapture(0)
        
        while self.ejecutando:
            ret, frame = cap.read()
            if not ret:
                break
            
            if self.detectando and self.tipo_objeto.get():
                self.contador_frames += 1
                # Procesar solo cada 3 frames (optimización)
                if self.contador_frames % 3 == 0:
                    # Detección de objetos
                    with torch.no_grad():  # Evitar el cálculo de gradientes innecesarios
                        resultados = modelo(frame)
                    detecciones = resultados.pandas().xyxy[0].to_dict(orient="records")
                    
                    # Analizar el color de cada detección
                    for det in detecciones:
                        x1, y1, x2, y2 = int(det['xmin']), int(det['ymin']), int(det['xmax']), int(det['ymax'])
                        det['color'] = self.obtener_color_objeto(frame, x1, y1, x2, y2)

                    # Filtrar por tipo y color
                    detecciones_filtradas = self.filtrar_objetos(detecciones)
                    
                    if detecciones_filtradas:
                        # Guardar el último frame con detección
                        self.ultimo_frame = frame.copy()
                    
                    # Dibujar las detecciones en el frame
                    for det in detecciones_filtradas:
                        x1, y1, x2, y2 = int(det['xmin']), int(det['ymin']), int(det['xmax']), int(det['ymax'])
                        etiqueta = det['name']
                        color = det['color']
                        conf = det['confidence']
                        
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f"{etiqueta} ({color}) {conf:.2f}", 
                                    (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Convertir el frame para tkinter
            img = cv2.resize(frame, (640, 480))
            self.photo = cv2.imencode('.png', img)[1].tobytes()

            # Mostrar la imagen en la GUI
            self.cuadro_camara.imgtk = tk.PhotoImage(data=self.photo)
            self.cuadro_camara.configure(image=self.cuadro_camara.imgtk)
            
            # Mostrar el último frame con detección en la ventana secundaria
            if self.ultimo_frame is not None:
                ultimo_img = cv2.resize(self.ultimo_frame, (640, 480))
                self.photo_ultimo_frame = cv2.imencode('.png', ultimo_img)[1].tobytes()
                self.label_secundario.imgtk = tk.PhotoImage(data=self.photo_ultimo_frame)
                self.label_secundario.configure(image=self.label_secundario.imgtk)
            
            # Controlar la velocidad de actualización de los frames
            cv2.waitKey(1)

        cap.release()

    def detener(self):
        """Detiene la cámara y cierra la ventana."""
        self.ejecutando = False
        self.hilo_camara.join()
        self.root.destroy()

# Ejecutar la aplicación
if __name__ == "__main__":
    root = tk.Tk()
    app = AplicacionDetector(root)
    root.protocol("WM_DELETE_WINDOW", app.detener)
    root.mainloop()
