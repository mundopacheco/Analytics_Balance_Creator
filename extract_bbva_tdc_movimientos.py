#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass, asdict
from pathlib import Path

import fitz
import pandas as pd


DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{2}$")
AMOUNT_RE = re.compile(r"\d{1,3}(?:,\d{3})*\.\d{2}")

START_PATTERN = "MOVIMIENTOS EFECTUADOS"
STOP_PATTERN = "TOTAL IMPORTES"


@dataclass
class Movimiento:
    fecha_autorizacion: str
    fecha_aplicacion: str
    concepto: str
    monto: float
    tipo: str  # cargo o abono


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_date(d):
    # 26/07/23 → 2023-07-26
    day, month, year = d.split("/")
    year = "20" + year
    return f"{year}-{month}-{day}"


def extract_lines(pdf_path: Path):
    doc = fitz.open(pdf_path)
    lines_out = []
    in_block = False

    for page in doc:
        lines = [normalize(x) for x in page.get_text("text").splitlines() if x.strip()]

        for line in lines:
            upper = line.upper()

            if not in_block:
                if START_PATTERN in upper:
                    in_block = True
                continue

            if STOP_PATTERN in upper:
                in_block = False
                continue

            lines_out.append(line)

    return lines_out


def parse_movimientos(lines):
    movimientos = []
    i = 0
    n = len(lines)

    while i < n:
        if DATE_RE.match(lines[i]):
            if i + 1 < n and DATE_RE.match(lines[i + 1]):
                fecha_aut = parse_date(lines[i])
                fecha_apl = parse_date(lines[i + 1])

                i += 2

                concepto_parts = []
                cargo = None
                abono = None

                while i < n:
                    line = lines[i]
                    upper = line.upper()

                    # siguiente registro
                    if DATE_RE.match(line) and i + 1 < n and DATE_RE.match(lines[i + 1]):
                        break

                    # 🔥 FILTRO DE RUIDO (CLAVE)
                    if any(x in upper for x in [
                        "TOTAL", "IMPORTES", "SALDO", "BBVA",
                        "ESTADO DE CUENTA", "LINEA", "PAGINA"
                    ]):
                        i += 1
                        continue

                    # detectar montos
                    amounts = AMOUNT_RE.findall(line)

                    # 🔥 SOLO aceptar líneas con EXACTAMENTE 1 monto
                    if len(amounts) == 1:
                        val = float(amounts[0].replace(",", ""))

                        # detectar signo
                        if "-" in line:
                            abono = val
                        else:
                            cargo = val

                        i += 1
                        continue

                    # 🔥 IGNORAR líneas con múltiples montos
                    if len(amounts) > 1:
                        i += 1
                        continue

                    # ignorar RFC y referencia
                    if line.startswith("RFC") or "******" in line:
                        i += 1
                        continue

                    concepto_parts.append(line)
                    i += 1

                concepto = normalize(" ".join(concepto_parts))

                monto = None
                if cargo is not None:
                    monto = cargo
                elif abono is not None:
                    monto = -abono

                # VALIDACIÓN FINAL
                # (detectar ajustes internos)
                if any(x in concepto.upper() for x in [
                    "PROMOCION",
                    "TRASPASO A MESES",
                    "MESES SIN INTERES"
                ]):
                    # ❌ NO agregar como movimiento
                    continue

                # ✅ SOLO aquí agregas el movimiento
                if monto is not None and abs(monto) < 20000:
                    movimientos.append(
                        Movimiento(
                            fecha_autorizacion=fecha_aut,
                            fecha_aplicacion=fecha_apl,
                            concepto=concepto,
                            monto=monto,
                            tipo="cargo" if monto > 0 else "abono",
                        )
                    )

        i += 1

    return movimientos


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    lines = extract_lines(Path(args.input))
    movimientos = parse_movimientos(lines)

    if not movimientos:
        raise RuntimeError("No se encontraron movimientos en el PDF.")

    df = pd.DataFrame([asdict(m) for m in movimientos])

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False, sep="|")

    print(f"Movimientos extraídos: {len(df)}")
    print(f"Archivo generado: {args.output}")


if __name__ == "__main__":
    main()