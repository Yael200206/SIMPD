import os

# Obtener el directorio donde se encuentra este script
directorio_script = os.path.dirname(__file__)

# Unir la ruta del archivo JSON al directorio
ruta_relativa = os.path.join(directorio_script, '../ubicaciones_camaras.json')

print(ruta_relativa)