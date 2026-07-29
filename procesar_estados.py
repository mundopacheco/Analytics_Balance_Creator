from pathlib import Path
import subprocess
import sys
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "Estados de cuenta"
OUTPUT_DIR = BASE_DIR / "csv_output"
OUTPUT_DIR.mkdir(exist_ok=True)

EXTRACTOR = BASE_DIR / "extract_bbva_debito.py"

if not EXTRACTOR.exists():
    raise FileNotFoundError(f"No existe el extractor en: {EXTRACTOR}")

if not INPUT_DIR.exists():
    raise FileNotFoundError(f"No existe la carpeta de entrada: {INPUT_DIR}")

for pdf_file in sorted(INPUT_DIR.glob("*.pdf")):
    out_csv = OUTPUT_DIR / f"{pdf_file.stem}.csv"
    print(f"Procesando: {pdf_file.name}")

    result = subprocess.run(
        [
            sys.executable,
            str(EXTRACTOR),
            "--input",
            str(pdf_file),
            "--output",
            str(out_csv),
        ],
        capture_output=True,
        text=True,
        cwd=str(BASE_DIR),
    )

    if result.returncode != 0:
        print(f"ERROR en {pdf_file.name}")
        print(result.stderr or result.stdout)
    else:
        print(result.stdout.strip())

dfs = []
for csv_file in sorted(OUTPUT_DIR.glob("*.csv")):
    if csv_file.name == "movimientos_debito_total.csv":
        continue

    df = pd.read_csv(csv_file, sep="|")
    df["archivo_origen"] = csv_file.stem
    dfs.append(df)

if not dfs:
    raise RuntimeError("No se encontraron CSVs generados para concatenar.")

df_total = pd.concat(dfs, ignore_index=True)

df_total["fecha_oper"] = pd.to_datetime(df_total["fecha_oper"], errors="coerce")
df_total["fecha_liq"] = pd.to_datetime(df_total["fecha_liq"], errors="coerce")
df_total = df_total.sort_values(["fecha_oper"]).reset_index(drop=True)

df_total["fecha_oper"] = df_total["fecha_oper"].dt.strftime("%Y-%m-%d")
df_total["fecha_liq"] = df_total["fecha_liq"].dt.strftime("%Y-%m-%d")

out_total = OUTPUT_DIR / "movimientos_debito_total.csv"
df_total = df_total.replace('|', ' ', regex=True)
df_total = df_total.replace(',', '', regex=True)
df_total.to_csv(out_total, index=False, sep="|")

print(f"\nListo. Consolidado generado en: {out_total}")
print(f"Filas totales: {len(df_total)}")