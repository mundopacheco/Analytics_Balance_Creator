#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import fitz
import pandas as pd


DATE_TOKEN_RE = re.compile(r"^\d{2}/[A-Z]{3}$")
AMOUNT_RE = re.compile(r"^\d{1,3}(?:,\d{3})*\.\d{2}$|^\d+\.\d{2}$")

SPANISH_MONTHS = {
    "ENE": "01",
    "FEB": "02",
    "MAR": "03",
    "ABR": "04",
    "MAY": "05",
    "JUN": "06",
    "JUL": "07",
    "AGO": "08",
    "SEP": "09",
    "OCT": "10",
    "NOV": "11",
    "DIC": "12",
}

HEADER_TOKENS = {
    "FECHA", "OPER", "LIQ", "DESCRIPCION", "REFERENCIA",
    "CARGOS", "ABONOS", "OPERACION", "LIQUIDACION", "SALDO"
}

STOP_PATTERNS = (
    "TOTAL DE MOVIMIENTOS",
)

IGNORE_PATTERNS = (
    "NO. DE CUENTA",
    "NO. DE CLIENTE",
    "ESTADO DE CUENTA",
    "PAGINA",
    "LIBRETÓN",
    "LIBRETON",
    "BBVA MEXICO",
    "AV. PASEO",
    "PRODUCTO PROTEGIDO",
    "LA GAT",
    "COMISIONES",
)


@dataclass
class Movimiento:
    fecha_oper: str
    fecha_liq: str
    descripcion: str
    cargo: Optional[float]
    abono: Optional[float]
    pagina: int


CREDIT_HINTS = (
    "SPEI RECIBIDO",
    "PAGO DE NOMINA",
    "DEPOSITO",
    "ABONO",
    "TRASPASO ENTRE CUENTAS",
    "PRESTAMO OTORGADO",
    "DEP TERCERO",
)


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def infer_year_from_filename(path: Path) -> int:
    m = re.search(r"(20\d{2})", path.stem)
    if not m:
        raise ValueError(f"No pude inferir el año del nombre del archivo: {path.name}")
    return int(m.group(1))


def expand_date(dd_mmm: str, year: int) -> str:
    day, mon = dd_mmm.split("/")
    return f"{year}-{SPANISH_MONTHS[mon.upper()]}-{day}"


def parse_amount(token: str) -> float:
    return float(token.replace(",", ""))


def is_amount(token: str) -> bool:
    return bool(AMOUNT_RE.match(token))


def is_date_token(token: str) -> bool:
    return bool(DATE_TOKEN_RE.match(token))


def should_ignore(token: str) -> bool:
    upper = token.upper()
    if upper in HEADER_TOKENS:
        return True
    return any(p in upper for p in IGNORE_PATTERNS)


def clean_description(text: str) -> str:
    text = normalize_spaces(text)

    replacements = {
        "RECIBIDOSANTANDER": "RECIBIDO SANTANDER",
        "RECIBIDOAZTECA": "RECIBIDO AZTECA",
        "ENVIADOBANCOPPEL": "ENVIADO BANCOPPEL",
        "OXXOBBVA": "OXXO BBVA",
        "SPEI ENVIADOBANCOPPEL": "SPEI ENVIADO BANCOPPEL",
        "SPEI RECIBIDOSANTANDER": "SPEI RECIBIDO SANTANDER",
        "SPEI RECIBIDOAZTECA": "SPEI RECIBIDO AZTECA",
        "SPEI RECIBIDOBANORTE": "SPEI RECIBIDO BANORTE",
        "SPEI ENVIADOHSBC": "SPEI ENVIADO HSBC",
        "SPEI ENVIADOAZTECA": "SPEI ENVIADO AZTECA",
        "SPEI ENVIADOBANORTE": "SPEI ENVIADO BANORTE",
        "PAGO DE NOMINA PAGO DE NOMINA": "PAGO DE NOMINA",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\b\d{7,}\b", "", text)
    text = re.sub(r"\bD\d{7,}\b", "", text)
    text = normalize_spaces(text)
    return text


def extract_tokens(pdf_path: Path) -> list[tuple[int, str]]:
    doc = fitz.open(pdf_path)
    out: list[tuple[int, str]] = []
    in_detail_block = False

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text")
        lines = [normalize_spaces(x) for x in text.splitlines()]
        lines = [x for x in lines if x]

        for line in lines:
            upper = line.upper()

            if not in_detail_block:
                if "DETALLE DE MOVIMIENTOS REALIZADOS" in upper:
                    in_detail_block = True
                continue

            if any(p in upper for p in STOP_PATTERNS):
                in_detail_block = False
                continue

            out.append((page_num, line))

    return out


def tokens_to_movimientos(tokens: list[tuple[int, str]], year: int) -> list[Movimiento]:
    movimientos: list[Movimiento] = []
    i = 0
    n = len(tokens)

    while i < n:
        page_num, tok = tokens[i]

        if is_date_token(tok):
            if i + 1 < n and is_date_token(tokens[i + 1][1]):
                fecha_oper = expand_date(tok, year)
                fecha_liq = expand_date(tokens[i + 1][1], year)

                i += 2
                desc_parts = []
                first_amount = None

                while i < n:
                    page_num_i, tok_i = tokens[i]
                    upper = tok_i.upper()

                    if is_date_token(tok_i) and i + 1 < n and is_date_token(tokens[i + 1][1]):
                        break

                    if should_ignore(tok_i):
                        i += 1
                        continue

                    if upper.startswith("REFERENCIA"):
                        i += 1
                        continue

                    if is_amount(tok_i):
                        if first_amount is None:
                            first_amount = parse_amount(tok_i)
                        i += 1
                        continue

                    desc_parts.append(tok_i)
                    i += 1

                descripcion = clean_description(" ".join(desc_parts))

                cargo = None
                abono = None
                if first_amount is not None:
                    upper_desc = descripcion.upper()
                    if any(h in upper_desc for h in CREDIT_HINTS):
                        abono = first_amount
                    else:
                        cargo = first_amount

                movimientos.append(
                    Movimiento(
                        fecha_oper=fecha_oper,
                        fecha_liq=fecha_liq,
                        descripcion=descripcion,
                        cargo=cargo,
                        abono=abono,
                        pagina=page_num,
                    )
                )
                continue

        i += 1

    return movimientos


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="PDF de entrada")
    parser.add_argument("--output", required=True, help="Archivo de salida")
    parser.add_argument("--debug-tokens", action="store_true", help="Guardar tokens detectados")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    year = infer_year_from_filename(input_path)
    tokens = extract_tokens(input_path)

    if args.debug_tokens:
        debug_path = output_path.with_name(output_path.stem + "_debug_tokens.txt")
        with debug_path.open("w", encoding="utf-8") as fh:
            for p, t in tokens:
                fh.write(f"[p{p}] {t}\n")
        print(f"Debug tokens guardado en: {debug_path}")

    movimientos = tokens_to_movimientos(tokens, year)

    if not movimientos:
        raise RuntimeError(
            "No se extrajeron movimientos. Revisa el archivo debug y valida que existan pares de fechas DD/MES."
        )

    df = pd.DataFrame([asdict(m) for m in movimientos])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.suffix.lower() != ".csv":
        output_path = output_path.with_suffix(".csv")

    df.to_csv(output_path, index=False, sep="|", quoting=csv.QUOTE_MINIMAL)

    print(f"Movimientos extraídos: {len(df)}")
    print(f"CSV generado en: {output_path}")
    print("Delimitador usado: |")


if __name__ == "__main__":
    main()
