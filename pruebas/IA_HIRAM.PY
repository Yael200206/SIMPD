import cv2
import torch
import tkinter as tk
from tkinter import StringVar
from threading import Thread
import time
import numpy as np
from PIL import Image, ImageTk

# Cargar el modelo preentrenado YOLOv5
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
model.conf = 0.4  # Confianza mínima para detecciones

class VehicleDetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Detección de Vehículos")
        
        # Variables
        self.vehicle_type = StringVar(value="auto")  # Tipo de vehículo inicial
        self.vehicle_color = StringVar(value="")     # Color del vehículo inicial
        self.running = True  # Controla la ejecución del hilo de la cámara
        self.detecting = True  # Indica si está detectando objetos
        self.detections = []  # Lista para almacenar las detecciones actuales
        self.last_detection_time = 0  # Controla la frecuencia de detección
        self.detection_interval = 0.5  # Intervalo entre detecciones (en segundos)
        
        # Interfaz gráfica
        self.camera_frame = tk.Label(self.root)
        self.camera_frame.grid(row=0, column=0, columnspan=3)
        
        tk.Label(self.root, text="Tipo de vehículo:").grid(row=1, column=0)
        self.type_entry = tk.Entry(self.root, textvariable=self.vehicle_type)
        self.type_entry.grid(row=1, column=1)
        
        tk.Label(self.root, text="Color:").grid(row=2, column=0)
        self.color_entry = tk.Entry(self.root, textvariable=self.vehicle_color)
        self.color_entry.grid(row=2, column=1)
        
        tk.Button(self.root, text="Actualizar búsqueda", command=self.update_search).grid(row=3, column=2)
        tk.Button(self.root, text="Limpiar búsqueda", command=self.clear_search).grid(row=3, column=1)

        # Hilos
        self.camera_thread = Thread(target=self.show_camera)
        self.detection_thread = Thread(target=self.detect_objects)
        self.camera_thread.start()
        self.detection_thread.start()
    
    def update_search(self):
        """Actualiza el tipo y color de vehículo a buscar."""
        self.detecting = True

    def clear_search(self):
        """Limpia las detecciones."""
        self.vehicle_type.set("")
        self.vehicle_color.set("")
        self.detecting = False
        self.detections = []

    def detect_objects(self):
        """Detecta objetos en un intervalo de tiempo."""
        cap = cv2.VideoCapture(0)
        while self.running:
            if self.detecting and (time.time() - self.last_detection_time >= self.detection_interval):
                ret, frame = cap.read()
                if not ret:
                    continue

                # Reducción de resolución para detección más rápida
                small_frame = cv2.resize(frame, (640, 360))
                
                # Detección de objetos
                results = model(small_frame)
                detections = results.pandas().xyxy[0].to_dict(orient="records")
                
                # Analizar el color de cada detección
                for det in detections:
                    x1, y1, x2, y2 = int(det['xmin']), int(det['ymin']), int(det['xmax']), int(det['ymax'])
                    det['color'] = self.get_vehicle_color(small_frame, x1, y1, x2, y2)
                
                # Filtrar detecciones
                self.detections = self.filter_vehicles(detections)
                self.last_detection_time = time.time()
        
        cap.release()

    def filter_vehicles(self, detections):
        """Filtra las detecciones según el tipo y color del vehículo."""
        filtered = []
        search_type = self.vehicle_type.get().lower()
        search_color = self.vehicle_color.get().lower()
        
        # Mapeo de tipos de vehículos
        type_mapping = {
            "auto": ["car", "truck", "suv"],  # Mapeo para "auto"
            "moto": ["motorcycle"],          # Mapeo para "moto"
            "autobus": ["bus"]               # Mapeo para "autobus"
        }
        valid_labels = type_mapping.get(search_type, [])
        
        for det in detections:
            label = det['name']
            if label in valid_labels:
                det_color = det.get('color', "").lower()
                if search_color in det_color:  # Coincidencia parcial de color
                    filtered.append(det)
        return filtered

    def get_vehicle_color(self, frame, x1, y1, x2, y2):
        """Determina el color dominante de un vehículo en el área detectada."""
        roi = frame[y1:y2, x1:x2]  # Región de interés
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Máscara para excluir colores oscuros o blancos
        mask = cv2.inRange(hsv_roi, (0, 30, 30), (180, 255, 255))
        masked_roi = cv2.bitwise_and(hsv_roi, hsv_roi, mask=mask)
        
        # Histograma para calcular color dominante
        hist = cv2.calcHist([masked_roi], [0], mask, [180], [0, 180])
        dominant_hue = np.argmax(hist)
        
        # Determinar el color basado en el tono dominante
        if 0 <= dominant_hue <= 10 or 160 <= dominant_hue <= 180:
            return "Rojo"
        elif 11 <= dominant_hue <= 25:
            return "Naranja"
        elif 26 <= dominant_hue <= 34:
            return "Amarillo"
        elif 35 <= dominant_hue <= 85:
            return "Verde"
        elif 86 <= dominant_hue <= 125:
            return "Azul"
        elif 126 <= dominant_hue <= 159:
            return "Morado"
        else:
            return "Desconocido"

    def show_camera(self):
        """Muestra la cámara en la interfaz."""
        cap = cv2.VideoCapture(0)
        while self.running:
            ret, frame = cap.read()
            if not ret:
                break

            # Dibujar detecciones
            for det in self.detections:
                x1, y1, x2, y2 = int(det['xmin']), int(det['ymin']), int(det['xmax']), int(det['ymax'])
                label = det['name']
                color = det['color']
                conf = det['confidence']
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{label} ({color}) {conf:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Convertir el frame para tkinter
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            imgtk = ImageTk.PhotoImage(image=img)
            self.camera_frame.imgtk = imgtk
            self.camera_frame.configure(image=imgtk)
        
        cap.release()

    def stop(self):
        """Detiene la cámara y cierra la ventana."""
        self.running = False
        self.camera_thread.join()
        self.detection_thread.join()
        self.root.destroy()

# Ejecutar la aplicación
if __name__ == "__main__":
    root = tk.Tk()
    app = VehicleDetectorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.stop)
    root.mainloop()
