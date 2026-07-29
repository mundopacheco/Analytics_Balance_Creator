from pathlib import Path
import subprocess
import sys

import pandas as pd


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "Estados de cuenta"
OUTPUT_DIR = BASE_DIR / "csv_output"
EXTRACTOR = BASE_DIR / "extract_bbva_debito.py"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# INITIAL VALIDATION
# ============================================================

if not EXTRACTOR.exists():
    raise FileNotFoundError(
        f"No se encontró el extractor de débito:\n{EXTRACTOR}"
    )

if not INPUT_DIR.exists():
    raise FileNotFoundError(
        f"No se encontró la carpeta de estados de cuenta:\n{INPUT_DIR}\n\n"
        'Crea una carpeta llamada "Estados de cuenta" en la raíz del proyecto '
        "y coloca ahí tus archivos PDF."
    )

pdf_files = sorted(INPUT_DIR.glob("*.pdf"))

if not pdf_files:
    raise RuntimeError(
        f'No se encontraron archivos PDF en:\n{INPUT_DIR}'
    )


# ============================================================
# PROCESS EACH PDF
# ============================================================

print(f"PDF encontrados: {len(pdf_files)}")
print(f"Carpeta de entrada: {INPUT_DIR}")
print(f"Carpeta de salida: {OUTPUT_DIR}\n")

generated_csvs = []

for pdf_file in pdf_files:
    output_csv = OUTPUT_DIR / f"{pdf_file.stem}.csv"

    print("=" * 70)
    print(f"Procesando: {pdf_file.name}")

    result = subprocess.run(
        [
            sys.executable,
            str(EXTRACTOR),
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
        print(f"ERROR al procesar: {pdf_file.name}")

        if result.stdout.strip():
            print("\nSalida:")
            print(result.stdout.strip())

        if result.stderr.strip():
            print("\nDetalle del error:")
            print(result.stderr.strip())

        continue

    if result.stdout.strip():
        print(result.stdout.strip())

    if output_csv.exists():
        generated_csvs.append(output_csv)
    else:
        print(f"ADVERTENCIA: no se generó el archivo esperado: {output_csv}")


# ============================================================
# CONSOLIDATE GENERATED CSV FILES
# ============================================================

print("\n" + "=" * 70)
print("Generando archivo consolidado...")

dfs = []

for csv_file in sorted(generated_csvs):
    try:
        df = pd.read_csv(csv_file, sep="|")
    except Exception as exc:
        print(f"ADVERTENCIA: no se pudo leer {csv_file.name}: {exc}")
        continue

    if df.empty:
        print(f"ADVERTENCIA: {csv_file.name} está vacío y será omitido.")
        continue

    required_columns = {
        "fecha_oper",
        "fecha_liq",
        "descripcion",
        "cargo",
        "abono",
        "pagina",
    }

    missing_columns = required_columns.difference(df.columns)

    if missing_columns:
        print(
            f"ADVERTENCIA: {csv_file.name} no tiene las columnas requeridas: "
            f"{sorted(missing_columns)}"
        )
        continue

    df["archivo_origen"] = csv_file.stem
    dfs.append(df)


if not dfs:
    raise RuntimeError(
        "No se encontraron CSV válidos para generar el consolidado."
    )


# Crear el DataFrame consolidado antes de intentar modificarlo
df_total = pd.concat(dfs, ignore_index=True)


# ============================================================
# DATA CLEANING
# ============================================================

df_total["fecha_oper"] = pd.to_datetime(
    df_total["fecha_oper"],
    errors="coerce",
)

df_total["fecha_liq"] = pd.to_datetime(
    df_total["fecha_liq"],
    errors="coerce",
)

df_total["cargo"] = pd.to_numeric(
    df_total["cargo"],
    errors="coerce",
)

df_total["abono"] = pd.to_numeric(
    df_total["abono"],
    errors="coerce",
)

for column in ["descripcion", "archivo_origen"]:
    df_total[column] = (
        df_total[column]
        .astype("string")
        .str.replace("|", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

rows_before = len(df_total)

df_total = df_total[
    df_total["fecha_oper"].notna()
].copy()

removed_rows = rows_before - len(df_total)

if removed_rows:
    print(
        f"ADVERTENCIA: se eliminaron {removed_rows} filas "
        "sin una fecha de operación válida."
    )

df_total = df_total.sort_values(
    by=["fecha_oper", "fecha_liq", "archivo_origen"],
    na_position="last",
).reset_index(drop=True)

df_total["fecha_oper"] = df_total["fecha_oper"].dt.strftime("%Y-%m-%d")
df_total["fecha_liq"] = df_total["fecha_liq"].dt.strftime("%Y-%m-%d")


# ============================================================
# SAVE CONSOLIDATED FILE
# ============================================================

out_total = OUTPUT_DIR / "movimientos_debito_total.csv"

df_total.to_csv(
    out_total,
    index=False,
    sep="|",
    encoding="utf-8-sig",
)

print("\nProceso terminado correctamente.")
print(f"Consolidado generado en: {out_total}")
print(f"Archivos individuales incluidos: {len(dfs)}")
print(f"Filas totales: {len(df_total)}")
