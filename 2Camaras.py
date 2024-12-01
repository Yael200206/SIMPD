import cv2
import torch
import tkinter as tk
from tkinter import StringVar
from threading import Thread
import numpy as np

# Cargar el modelo preentrenado YOLOv5
modelo = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

class AplicacionDetector:
    def __init__(self, root):
        self.root = root
        self.root.title("Detección de Objetos con Dos Cámaras")
        
        # Variables
        self.tipo_objeto = StringVar(value="car")  # Tipo de objeto inicial
        self.color_objeto = StringVar(value="")     # Color de objeto inicial
        self.ejecutando = True  # Controla la ejecución de los hilos de las cámaras
        self.detectando = True  # Indica si está detectando objetos
        
        # Interfaz gráfica
        tk.Label(self.root, text="Tipo de objeto:").grid(row=0, column=0)
        self.tipo_objeto_menu = tk.OptionMenu(self.root, self.tipo_objeto, "auto", "moto", "autobus", "persona")
        self.tipo_objeto_menu.grid(row=0, column=1)
        
        tk.Label(self.root, text="Color:").grid(row=1, column=0)
        self.color_objeto_menu = tk.OptionMenu(self.root, self.color_objeto, "Rojo", "Naranja", "Amarillo", "Verde", 
                                               "Azul", "Morado", "Negro", "Blanco", "Gris")
        self.color_objeto_menu.grid(row=1, column=1)
        
        tk.Button(self.root, text="Actualizar búsqueda", command=self.actualizar_busqueda).grid(row=2, column=0)
        tk.Button(self.root, text="Limpiar búsqueda", command=self.limpiar_busqueda).grid(row=2, column=1)

        # Ventanas para mostrar las cámaras
        self.cuadro_camara1 = tk.Label(self.root)
        self.cuadro_camara1.grid(row=3, column=0)
        self.cuadro_camara2 = tk.Label(self.root)
        self.cuadro_camara2.grid(row=3, column=1)

        # Hilos para las cámaras
        self.hilo_camara1 = Thread(target=self.mostrar_camara, args=(0, self.cuadro_camara1), daemon=True)
        self.hilo_camara2 = Thread(target=self.mostrar_camara, args=(1, self.cuadro_camara2), daemon=True)
        self.hilo_camara1.start()
        self.hilo_camara2.start()
    
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
        
        mapeo_tipo = {
            "auto": ["car", "truck", "suv"],
            "moto": ["motorcycle"],
            "autobus": ["bus"],
            "persona": ["person"],
        }
        etiquetas_validas = mapeo_tipo.get(tipo_buscar, [])
        
        for det in detecciones:
            etiqueta = det['name']
            if etiqueta in etiquetas_validas:
                color_det = det.get('color', "").lower()
                if color_buscar in color_det:
                    filtrados.append(det)
        return filtrados

    def obtener_color_objeto(self, frame, x1, y1, x2, y2):
        """Determina el color dominante de un objeto."""
        roi = frame[y1:y2, x1:x2]
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mascara = cv2.inRange(hsv_roi, (0, 30, 30), (180, 255, 255))
        hist = cv2.calcHist([hsv_roi], [0], mascara, [180], [0, 180])
        tono_dominante = np.argmax(hist)
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
        elif np.mean(roi) < 60:
            return "Negro"
        elif np.mean(roi) > 180:
            return "Blanco"
        else:
            return "Gris"

    def mostrar_camara(self, cam_id, cuadro_camara):
        """Muestra la cámara y aplica detección."""
        cap = cv2.VideoCapture(cam_id)
        while self.ejecutando:
            ret, frame = cap.read()
            if not ret:
                break
            
            if self.detectando and self.tipo_objeto.get():
                resultados = modelo(frame)
                detecciones = resultados.pandas().xyxy[0].to_dict(orient="records")
                
                for det in detecciones:
                    x1, y1, x2, y2 = int(det['xmin']), int(det['ymin']), int(det['xmax']), int(det['ymax'])
                    det['color'] = self.obtener_color_objeto(frame, x1, y1, x2, y2)

                detecciones_filtradas = self.filtrar_objetos(detecciones)
                for det in detecciones_filtradas:
                    x1, y1, x2, y2 = int(det['xmin']), int(det['ymin']), int(det['xmax']), int(det['ymax'])
                    etiqueta = det['name']
                    color = det['color']
                    conf = det['confidence']
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"{etiqueta} ({color}) {conf:.2f}", 
                                (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            img = cv2.resize(frame, (640, 480))
            self.photo = cv2.imencode('.png', img)[1].tobytes()
            cuadro_camara.imgtk = tk.PhotoImage(data=self.photo)
            cuadro_camara.configure(image=cuadro_camara.imgtk)
        
        cap.release()

    def detener(self):
        """Detiene la cámara y cierra la ventana."""
        self.ejecutando = False
        self.hilo_camara1.join()
        self.hilo_camara2.join()
        self.root.destroy()

# Ejecutar la aplicación
if __name__ == "__main__":
    root = tk.Tk()
    app = AplicacionDetector(root)
    root.protocol("WM_DELETE_WINDOW", app.detener)
    root.mainloop()
