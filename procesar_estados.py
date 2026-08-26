from pathlib import Path
import subprocess
import sys

import pandas as pd


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_DIR = (
    BASE_DIR
    / "Estados de cuenta"
)

OUTPUT_DIR = (
    BASE_DIR
    / "csv_output"
)

SALDOS_DIR = (
    OUTPUT_DIR
    / "saldos"
)

RESUMENES_DIR = (
    OUTPUT_DIR
    / "resumenes"
)

CONSOLIDADOS_DIR = (
    OUTPUT_DIR
    / "consolidados"
)

EXTRACTOR = (
    BASE_DIR
    / "extract_bbva_debito.py"
)


# ============================================================
# CREATE OUTPUT DIRECTORIES
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

SALDOS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

RESUMENES_DIR.mkdir(
    parents=True,
    exist_ok=True
)

CONSOLIDADOS_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# INITIAL VALIDATION
# ============================================================

if not EXTRACTOR.exists():

    raise FileNotFoundError(
        "No se encontró el extractor de débito:\n"
        f"{EXTRACTOR}"
    )


if not INPUT_DIR.exists():

    raise FileNotFoundError(
        "No se encontró la carpeta de estados de cuenta:\n"
        f"{INPUT_DIR}\n\n"
        'Crea la carpeta "Estados de cuenta" '
        "y coloca ahí los PDF."
    )


pdf_files = sorted(
    INPUT_DIR.glob("*.pdf")
)


if not pdf_files:

    raise RuntimeError(
        "No se encontraron archivos PDF en:\n"
        f"{INPUT_DIR}"
    )


# ============================================================
# PROCESS EACH PDF
# ============================================================

print(
    f"PDF encontrados: {len(pdf_files)}"
)

print(
    f"Entrada: {INPUT_DIR}"
)

print(
    f"Salida principal: {OUTPUT_DIR}"
)

print()


generated_movimientos = []
generated_saldos = []
generated_resumenes = []


for pdf_file in pdf_files:

    # Individual movement CSV remains directly in csv_output/
    output_movimientos = (
        OUTPUT_DIR
        / f"{pdf_file.stem}.csv"
    )

    output_saldo = (
        SALDOS_DIR
        / f"{pdf_file.stem}_saldo.csv"
    )

    output_resumen = (
        RESUMENES_DIR
        / f"{pdf_file.stem}_resumen.csv"
    )

    print("=" * 70)

    print(
        f"Procesando: "
        f"{pdf_file.name}"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(EXTRACTOR),

            "--input",
            str(pdf_file),

            "--output",
            str(output_movimientos),

            "--saldo-output",
            str(output_saldo),

            "--resumen-output",
            str(output_resumen),
        ],
        capture_output=True,
        text=True,
        cwd=str(BASE_DIR),
    )

    # --------------------------------------------------------
    # Extractor failed
    # --------------------------------------------------------

    if result.returncode != 0:

        print(
            f"ERROR al procesar: "
            f"{pdf_file.name}"
        )

        if result.stdout.strip():

            print("\nSalida:")
            print(
                result.stdout.strip()
            )

        if result.stderr.strip():

            print("\nDetalle:")
            print(
                result.stderr.strip()
            )

        continue

    # --------------------------------------------------------
    # Show extractor output
    # --------------------------------------------------------

    if result.stdout.strip():

        print(
            result.stdout.strip()
        )

    # --------------------------------------------------------
    # Register generated files
    # --------------------------------------------------------

    if output_movimientos.exists():

        generated_movimientos.append(
            output_movimientos
        )

    else:

        print(
            "ADVERTENCIA: no se generó "
            f"{output_movimientos}"
        )


    if output_saldo.exists():

        generated_saldos.append(
            output_saldo
        )

    else:

        print(
            "ADVERTENCIA: no se generó "
            f"{output_saldo}"
        )


    if output_resumen.exists():

        generated_resumenes.append(
            output_resumen
        )

    else:

        print(
            "ADVERTENCIA: no se generó "
            f"{output_resumen}"
        )


# ============================================================
# HELPER: READ CSV SAFELY
# ============================================================

def read_csv_safe(path: Path):

    try:

        return pd.read_csv(
            path,
            sep="|",
            encoding="utf-8-sig"
        )

    except Exception as exc:

        print(
            f"ADVERTENCIA: no se pudo leer "
            f"{path.name}: {exc}"
        )

        return None


# ============================================================
# CONSOLIDATE MOVEMENTS
# ============================================================

print()
print("=" * 70)
print(
    "Generando consolidado de movimientos..."
)


movimientos_dfs = []


for csv_file in sorted(
    generated_movimientos
):

    df = read_csv_safe(
        csv_file
    )

    if df is None:
        continue

    if df.empty:

        print(
            f"ADVERTENCIA: "
            f"{csv_file.name} está vacío."
        )

        continue


    required_columns = {
        "fecha_oper",
        "fecha_liq",
        "descripcion",
        "cargo",
        "abono",
        "saldo_operacion",
        "saldo_liquidacion",
        "pagina",
    }


    missing = (
        required_columns
        .difference(
            df.columns
        )
    )


    if missing:

        print(
            f"ADVERTENCIA: "
            f"{csv_file.name} no contiene "
            f"{sorted(missing)}"
        )

        continue


    df["archivo_origen"] = (
        csv_file.stem
    )

    movimientos_dfs.append(
        df
    )


if movimientos_dfs:

    df_movimientos = pd.concat(
        movimientos_dfs,
        ignore_index=True
    )

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    for column in [
        "fecha_oper",
        "fecha_liq",
    ]:

        df_movimientos[column] = pd.to_datetime(
            df_movimientos[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------

    numeric_columns = [
        "cargo",
        "abono",
        "saldo_operacion",
        "saldo_liquidacion",
    ]


    for column in numeric_columns:

        df_movimientos[column] = pd.to_numeric(
            df_movimientos[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Text cleanup
    # --------------------------------------------------------

    for column in [
        "descripcion",
        "archivo_origen",
    ]:

        df_movimientos[column] = (
            df_movimientos[column]
            .astype("string")
            .str.replace(
                "|",
                " ",
                regex=False
            )
            .str.replace(
                r"\s+",
                " ",
                regex=True
            )
            .str.strip()
        )

    # --------------------------------------------------------
    # Remove invalid movement dates
    # --------------------------------------------------------

    before = len(
        df_movimientos
    )

    df_movimientos = (
        df_movimientos[
            df_movimientos[
                "fecha_oper"
            ].notna()
        ]
        .copy()
    )

    removed = (
        before
        - len(df_movimientos)
    )


    if removed:

        print(
            f"ADVERTENCIA: se eliminaron "
            f"{removed} movimientos "
            "sin fecha válida."
        )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    df_movimientos = (
        df_movimientos
        .sort_values(
            [
                "fecha_oper",
                "fecha_liq",
                "archivo_origen",
            ],
            na_position="last",
        )
        .reset_index(
            drop=True
        )
    )

    # --------------------------------------------------------
    # Format dates back as ISO
    # --------------------------------------------------------

    df_movimientos[
        "fecha_oper"
    ] = (
        df_movimientos[
            "fecha_oper"
        ]
        .dt.strftime(
            "%Y-%m-%d"
        )
    )

    df_movimientos[
        "fecha_liq"
    ] = (
        df_movimientos[
            "fecha_liq"
        ]
        .dt.strftime(
            "%Y-%m-%d"
        )
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    movimientos_total_path = (
        CONSOLIDADOS_DIR
        / "movimientos_debito_total.csv"
    )

    df_movimientos.to_csv(
        movimientos_total_path,
        index=False,
        sep="|",
        encoding="utf-8-sig",
    )

    print(
        f"Movimientos consolidados: "
        f"{movimientos_total_path}"
    )

    print(
        f"Filas: "
        f"{len(df_movimientos)}"
    )

else:

    print(
        "ADVERTENCIA: no hay movimientos "
        "válidos para consolidar."
    )


# ============================================================
# CONSOLIDATE BALANCES
# ============================================================

print()
print("=" * 70)
print(
    "Generando consolidado de saldos..."
)


saldo_dfs = []


for csv_file in sorted(
    generated_saldos
):

    df = read_csv_safe(
        csv_file
    )

    if df is None or df.empty:
        continue

    saldo_dfs.append(
        df
    )


if saldo_dfs:

    df_saldos = pd.concat(
        saldo_dfs,
        ignore_index=True
    )

    df_saldos[
        "fecha_corte"
    ] = pd.to_datetime(
        df_saldos["fecha_corte"],
        errors="coerce"
    )

    df_saldos = (
        df_saldos
        .sort_values(
            "fecha_corte"
        )
        .reset_index(
            drop=True
        )
    )

    df_saldos[
        "fecha_corte"
    ] = (
        df_saldos[
            "fecha_corte"
        ]
        .dt.strftime(
            "%Y-%m-%d"
        )
    )

    saldo_total_path = (
        CONSOLIDADOS_DIR
        / "saldos_debito_total.csv"
    )

    df_saldos.to_csv(
        saldo_total_path,
        index=False,
        sep="|",
        encoding="utf-8-sig",
    )

    print(
        f"Saldos consolidados: "
        f"{saldo_total_path}"
    )

else:

    print(
        "ADVERTENCIA: no hay saldos "
        "válidos para consolidar."
    )


# ============================================================
# CONSOLIDATE SUMMARIES
# ============================================================

print()
print("=" * 70)
print(
    "Generando consolidado de resúmenes..."
)


resumen_dfs = []


for csv_file in sorted(
    generated_resumenes
):

    df = read_csv_safe(
        csv_file
    )

    if df is None or df.empty:
        continue

    resumen_dfs.append(
        df
    )


if resumen_dfs:

    df_resumenes = pd.concat(
        resumen_dfs,
        ignore_index=True
    )

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    for column in [
        "periodo_inicio",
        "periodo_fin",
        "fecha_corte",
    ]:

        if column in df_resumenes.columns:

            df_resumenes[column] = (
                pd.to_datetime(
                    df_resumenes[column],
                    errors="coerce"
                )
            )

    # --------------------------------------------------------
    # Sort by cut date
    # --------------------------------------------------------

    df_resumenes = (
        df_resumenes
        .sort_values(
            "fecha_corte"
        )
        .reset_index(
            drop=True
        )
    )

    # --------------------------------------------------------
    # ISO date format
    # --------------------------------------------------------

    for column in [
        "periodo_inicio",
        "periodo_fin",
        "fecha_corte",
    ]:

        if column in df_resumenes.columns:

            df_resumenes[column] = (
                df_resumenes[column]
                .dt.strftime(
                    "%Y-%m-%d"
                )
            )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    resumen_total_path = (
        CONSOLIDADOS_DIR
        / "resumenes_debito_total.csv"
    )

    df_resumenes.to_csv(
        resumen_total_path,
        index=False,
        sep="|",
        encoding="utf-8-sig",
    )

    print(
        f"Resúmenes consolidados: "
        f"{resumen_total_path}"
    )

else:

    print(
        "ADVERTENCIA: no hay resúmenes "
        "válidos para consolidar."
    )


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("=" * 70)
print(
    "PROCESO TERMINADO"
)

print(
    f"PDF procesados correctamente: "
    f"{len(generated_movimientos)} "
    f"de {len(pdf_files)}"
)

print()
print(
    f"CSV individuales: "
    f"{OUTPUT_DIR}"
)

print(
    f"Saldos: "
    f"{SALDOS_DIR}"
)

print(
    f"Resúmenes: "
    f"{RESUMENES_DIR}"
)

print(
    f"Consolidados: "
    f"{CONSOLIDADOS_DIR}"
)