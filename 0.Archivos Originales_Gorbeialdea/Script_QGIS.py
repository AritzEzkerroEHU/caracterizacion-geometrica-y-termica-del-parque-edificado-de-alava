import os
import time
import sys
from PyQt5.QtWidgets import QFileDialog, QApplication

# --- Inicializar aplicación de PyQt ---
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

# --- Seleccionar carpeta de códigos ---
ruta_codigos = QFileDialog.getExistingDirectory(
    None,
    "Selecciona la carpeta donde están los códigos",
    os.path.expanduser("~")
)
if not ruta_codigos:
    raise ValueError("No se seleccionó ninguna carpeta")

# --- Lista de archivos .txt ---
archivos = [f for f in os.listdir(ruta_codigos) if f.endswith(".txt")]

# --- Guardar resultados en lista ---
tiempos = []

# --- Ejecutar cada archivo con medición de tiempo ---
for archivo in archivos[3:]:
    ruta_completa = os.path.join(ruta_codigos, archivo)
    print(f"⏳ Ejecutando: {archivo}")
    with open(ruta_completa, "r", encoding="utf-8") as f:
        codigo = f.read()
    try:
        inicio = time.time()
        exec(codigo)
        fin = time.time()
        duracion = fin - inicio
        print(f"✅ Ejecutado en {duracion:.2f} segundos\n")
        tiempos.append(round(duracion, 2))  # redondeado a 2 decimales
    except Exception as e:
        print(f"❌ Error al ejecutar {archivo}: {e}\n")
        tiempos.append(None)

# --- Escribir los timepos ---
# Usamos "-" como separador
texto_final = "-".join(str(t if t is not None else "ERR") for t in tiempos)
print(texto_final)
