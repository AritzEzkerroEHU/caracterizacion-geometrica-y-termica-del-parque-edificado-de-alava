
import os
import pandas as pd
import numpy as np
import xlsxwriter
import joblib
import xgboost as xgb
from PyQt5.QtWidgets import QApplication, QFileDialog
import sys


app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

ruta_original = QFileDialog.getExistingDirectory(
    None,
    "Selecciona la carpeta de archivos originales"
)
if not ruta_original:
    print("❌ No se seleccionó la carpeta de archivos originales")
    exit()

ruta_modificado = QFileDialog.getExistingDirectory(
    None,
    "Selecciona la carpeta donde guardar archivos modificados"
)
if not ruta_modificado:
    print("❌ No se seleccionó la carpeta de archivos modificados")
    exit()

ruta_pickle = os.path.join(ruta_original, "modelo_TB.pkl")
grid = joblib.load(ruta_pickle)

xgb_model = grid.best_estimator_

ruta_json = os.path.join(ruta_modificado, "modelo_TB.json")
booster = xgb_model.get_booster()
booster.save_model(ruta_json)

booster_mod = xgb.Booster()
booster_mod.load_model(ruta_json)


ruta_csv = os.path.join(ruta_modificado, "Parametros_Edificios.csv")
if not os.path.exists(ruta_csv):
    print(f"❌ No se encontró el CSV de prueba en {ruta_csv}")
    exit()

for sep in [';', ',']:
    X_test = pd.read_csv(ruta_csv, sep=sep)
    if len(X_test.columns) > 1:
        break
else:
    raise ValueError("No se pudo detectar correctamente el separador del CSV.")

if "CodEdifici" in X_test.columns:
    X_test_model = X_test.drop(columns=["CodEdifici"])
else:
    X_test_model = X_test.copy()

for col in X_test_model.columns:
    if X_test_model[col].dtype == 'object':
        try:
            X_test_model[col] = pd.to_numeric(X_test_model[col], errors='coerce')
        except:
            pass
for col in X_test_model.select_dtypes(include='object').columns:
    X_test_model[col] = X_test_model[col].astype('category')

dtest = xgb.DMatrix(X_test_model, enable_categorical=True)

preds = booster_mod.predict(dtest)

dframe = pd.DataFrame()
if "CodEdifici" in X_test.columns:
    dframe["CodEdifici"] = X_test["CodEdifici"]
dframe["TB Model Prediction (ºC)"] = preds

ruta_pred = os.path.join(ruta_modificado, "Parametros_Edificios_TB.csv")
dframe.to_csv(ruta_pred, index=False)
print(f"✅ Predicciones guardadas en: {ruta_pred}")

tipo = "TB"
model = "with HDD"
alg = "XGBoost"
tiempo = "anual"
version = "V2"

archivo_climatico = os.path.join(ruta_original, "ArchivoClimatico.xlsx")
df_temp = pd.read_excel(archivo_climatico, engine="openpyxl")
df_temp = df_temp.set_index('Date/Time')
ts_temp = df_temp['OutTemp']

hdd_tot = []
base_temp = dframe["TB Model Prediction (ºC)"]
for tb in base_temp:
    df_temp["HDD"] = tb - ts_temp
    df_temp["Logico"] = np.where(df_temp["HDD"] < 0, 0, 1)
    df_temp["HDD2"] = df_temp["HDD"] * df_temp["Logico"]
    hdd = df_temp["HDD2"].sum()
    hdd_tot.append(hdd / 24)

archivo_hdd = os.path.join(ruta_modificado, f'Parametros_TB_HDD.xlsx')
workbook = xlsxwriter.Workbook(archivo_hdd)
worksheet1 = workbook.add_worksheet("Resultados")
header = ["TB", "HDD"]
for col, h in enumerate(header):
    worksheet1.write(0, col, h)

for row, val in enumerate(base_temp, start=1):
    worksheet1.write(row, 0, float(val))
for row, val in enumerate(hdd_tot, start=1):
    worksheet1.write(row, 1, val)
workbook.close()
print("✅ HDD value export is done")

archivo_UA = os.path.join(ruta_modificado, "Parametros_Edificios_2.csv")
df_UA = pd.read_csv(archivo_UA, sep=';') 
sigma = df_UA["UA +  ρVcp (KW/K)"]

PDemand = np.multiply(sigma, hdd_tot)
PredDemand = np.multiply(PDemand, 24)

archivo_final = os.path.join(ruta_modificado, f'Predicciones_Edificios.xlsx')
dframe["UA +  ρVcp (KW/K)"] = sigma
dframe["HDD (ºC·days)"] = hdd_tot
dframe["Prediction (kWh)"] = PredDemand

dframe.to_excel(archivo_final, index=False)
print(f"✅ Cumulative prediction result is exported in: {archivo_final}")