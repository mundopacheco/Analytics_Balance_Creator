from pathlib import Path
import subprocess
import sys
import fitz
import pandas as pd
import re


BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "Estados de cuenta" / "TDC"
OUTPUT_DIR = BASE_DIR / "csv_output_tdc"
OUTPUT_DIR.mkdir(exist_ok=True)

SCRIPT_REGULARES = BASE_DIR / "extract_bbva_tdc_regulares.py"
SCRIPT_MOVIMIENTOS = BASE_DIR / "extract_bbva_tdc_movimientos.py"
SCRIPT_DESGLOSE = BASE_DIR / "extract_bbva_tdc_desglose.py"

MESES = {
    "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4,
    "MAYO": 5, "JUNIO": 6, "JULIO": 7, "AGOSTO": 8,
    "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12
}

def extraer_fecha_base(nombre_archivo):
    nombre = nombre_archivo.upper()

    for mes_txt, mes_num in MESES.items():
        if mes_txt in nombre:
            match = re.search(r'(20\d{2})', nombre)
            if match:
                anio = int(match.group(1))
                return pd.Timestamp(anio, mes_num, 1)

    return pd.NaT

def detectar_formato(pdf_path):
    doc = fitz.open(pdf_path)

    for i in range(min(5, len(doc))):
        text = doc[i].get_text("text").upper()

        # 🔴 PRIORIDAD: DESGLOSE
        if "DESGLOSE DE MOVIMIENTOS" in text:
            return "desglose"

        # 🟡 FORMATO ANTIGUO
        if "MOVIMIENTOS EFECTUADOS" in text:
            return "movimientos"

        # 🟢 FORMATO MODERNO
        if "CARGOS,COMPRAS Y ABONOS REGULARES" in text:
            return "regulares"

    return "desconocido"


# --- PROCESAMIENTO ---
for pdf_file in sorted(INPUT_DIR.glob("*.pdf")):
    print(f"\nProcesando: {pdf_file.name}")

    formato = detectar_formato(pdf_file)

    if formato == "movimientos":
        extractor = SCRIPT_MOVIMIENTOS
        print("Formato detectado: MOVIMIENTOS EFECTUADOS")

    elif formato == "regulares":
        extractor = SCRIPT_REGULARES
        print("Formato detectado: REGULARES")

    elif formato == "desglose":
        extractor = SCRIPT_DESGLOSE

    else:
        print("⚠️ Formato desconocido, se omite")
        continue

    output_csv = OUTPUT_DIR / f"{pdf_file.stem}.csv"

    result = subprocess.run(
        [
            sys.executable,
            str(extractor),
            "--input",
            str(pdf_file),
            "--output",
            str(output_csv),
        ],
        capture_output=True,
        text=True,
        cwd=str(BASE_DIR),
    )

    if result.returncode != 0:
        print(f"❌ ERROR en {pdf_file.name}")
        print(result.stderr or result.stdout)
    else:
        print(result.stdout.strip())


# --- CONCATENACIÓN ---
dfs = []

for csv_file in sorted(OUTPUT_DIR.glob("*.csv")):
    if csv_file.name == "movimientos_tdc_total.csv":
        continue

    df = pd.read_csv(csv_file, sep="|")
    df["archivo_origen"] = csv_file.stem

    # =========================
    # 1. FECHA BASE (mes del PDF)
    # =========================
    df["fecha_base"] = extraer_fecha_base(csv_file.stem)

    # =========================
    # 2. ORDEN DENTRO DEL MES
    # =========================
    df = df.reset_index(drop=True)
    df["orden_mes"] = df.index

    # =========================
    # 3. FECHA REAL (si sirve)
    # =========================
    df["fecha_real"] = pd.to_datetime(df.get("fecha_operacion"), errors="coerce")

    # Invalidar fechas sospechosas (ej: 2020)
    df.loc[df["fecha_real"].dt.year < 2022, "fecha_real"] = pd.NaT

    # =========================
    # 4. FECHA FINAL (fallback inteligente)
    # =========================
    df["fecha"] = df["fecha_real"].fillna(
        df["fecha_base"] + pd.to_timedelta(df["orden_mes"], unit="D")
    )

    dfs.append(df)

if not dfs:
    raise RuntimeError("No se generaron CSVs para concatenar.")

df_total = pd.concat(dfs, ignore_index=True)

# Normalizar fechas
df_total["fecha"] = pd.to_datetime(df_total["fecha"], errors="coerce")

# Ordenar
df_total = df_total.sort_values(["fecha", "archivo_origen"]).reset_index(drop=True)

# Guardar
out_total = OUTPUT_DIR / "movimientos_tdc_total.csv"
df_total = df_total.replace('|', ' ', regex=True)
df_total = df_total.replace(',', '', regex=True)
df_total.to_csv(out_total, index=False, sep="|")

print("\n✅ Consolidado generado")
print(f"Archivo: {out_total}")
print(f"Filas totales: {len(df_total)}")