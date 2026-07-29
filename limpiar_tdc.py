import pandas as pd
import os
import re

OUTPUT_DIR = "tmp"
INPUT = "tmp/movimientos_tdc_total.csv"
OUTPUT = os.path.join(OUTPUT_DIR, "movimientos_tdc_limpio.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- CARGA ---
df = pd.read_csv(INPUT, sep="|")

# --- LIMPIEZA BÁSICA ---
df = df.dropna(subset=["monto"])
df["monto"] = pd.to_numeric(df["monto"], errors="coerce")
df = df.dropna(subset=["monto"])

# quitar filas con texto basura
df = df[~df["descripcion"].str.contains("BBVA|Estado de Cuenta|Página", na=False)]

# --- PARSEAR AÑO DESDE archivo_origen ---
def extraer_año(x):
    if pd.isna(x):
        return None
    match = re.search(r"(20\d{2})", str(x))
    return int(match.group(1)) if match else None

df["anio"] = df["archivo_origen"].apply(extraer_año)

# --- PARSEAR FECHAS ---
df["fecha_operacion"] = pd.to_datetime(df["fecha_operacion"], errors="coerce")
df["fecha_cargo"] = pd.to_datetime(df["fecha_cargo"], errors="coerce")

# --- RECONSTRUIR FECHA REAL ---
def reconstruir_fecha(row):
    if pd.isna(row["fecha_operacion"]) or pd.isna(row["anio"]):
        return pd.NaT
    
    return pd.Timestamp(
        year=row["anio"],
        month=row["fecha_operacion"].month,
        day=row["fecha_operacion"].day
    )

df["fecha"] = df.apply(reconstruir_fecha, axis=1)

# --- FILTROS IMPORTANTES ---
# quitar fechas absurdas
df = df[df["fecha"].notna()]
df = df[df["fecha"] > "2022-01-01"]
df = df[df["fecha"] < "2027-01-01"]

# --- LIMPIEZA DE TEXTO ---
df["descripcion"] = df["descripcion"].str.replace(r"\s+", " ", regex=True).str.strip()

# --- ORDEN FINAL ---
df = df.sort_values("fecha")

# --- GUARDAR ---
df.replace('|', ' ', regex=True)
df.replace(',', '', regex=True)
df.to_csv(OUTPUT, index=False, sep="|")

print(f"Archivo limpio guardado en: {OUTPUT}")