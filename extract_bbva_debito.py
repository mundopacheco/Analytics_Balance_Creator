#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import fitz
import pandas as pd


# ============================================================
# CONSTANTS
# ============================================================

AMOUNT_RE = re.compile(r"^-?\d{1,3}(?:,\d{3})*\.\d{2}$|^-?\d+\.\d{2}$")
DATE_TOKEN_RE = re.compile(r"^\d{2}/[A-Z]{3}$")

SPANISH_MONTHS = {
    "ENE": 1,
    "FEB": 2,
    "MAR": 3,
    "ABR": 4,
    "MAY": 5,
    "JUN": 6,
    "JUL": 7,
    "AGO": 8,
    "SEP": 9,
    "OCT": 10,
    "NOV": 11,
    "DIC": 12,
}


# ============================================================
# DATA MODEL
# ============================================================

@dataclass
class Movimiento:
    fecha_oper: str
    fecha_liq: str
    descripcion: str
    cargo: Optional[float]
    abono: Optional[float]
    saldo_operacion: Optional[float]
    saldo_liquidacion: Optional[float]
    pagina: int


# ============================================================
# BASIC HELPERS
# ============================================================

def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def normalize_for_match(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return normalize_spaces(text).upper()


def parse_amount(token: str) -> float:
    token = str(token).replace("$", "").replace(",", "").strip()
    return float(token)


def is_amount(token: str) -> bool:
    token = str(token).replace("$", "").strip()
    return bool(AMOUNT_RE.fullmatch(token))


def is_date_token(token: str) -> bool:
    return bool(DATE_TOKEN_RE.fullmatch(normalize_for_match(token)))


def line_text(line: list[dict]) -> str:
    return normalize_spaces(
        " ".join(
            word["text"]
            for word in sorted(line, key=lambda w: w["x0"])
        )
    )


def word_x_center(word: dict) -> float:
    return (float(word["x0"]) + float(word["x1"])) / 2.0


def infer_year_from_filename(path: Path) -> int:
    match = re.search(r"(20\d{2})", path.stem)
    if not match:
        raise ValueError(f"No se pudo inferir el anio del nombre: {path.name}")
    return int(match.group(1))


def infer_month_from_filename(path: Path) -> Optional[int]:
    name = normalize_for_match(path.stem)
    month_names = {
        "ENERO": 1,
        "FEBRERO": 2,
        "MARZO": 3,
        "ABRIL": 4,
        "MAYO": 5,
        "JUNIO": 6,
        "JULIO": 7,
        "AGOSTO": 8,
        "SEPTIEMBRE": 9,
        "OCTUBRE": 10,
        "NOVIEMBRE": 11,
        "DICIEMBRE": 12,
    }
    for month_name, month_num in month_names.items():
        if month_name in name:
            return month_num
    return None


def parse_pdf_date(value: str) -> str:
    return datetime.strptime(value, "%d/%m/%Y").strftime("%Y-%m-%d")


# ============================================================
# MOVEMENT DATE HANDLING
# ============================================================

def expand_date(
    dd_mmm: str,
    default_year: int,
    periodo_inicio: Optional[datetime] = None,
    periodo_fin: Optional[datetime] = None,
    statement_month: Optional[int] = None,
) -> str:
    day_txt, month_txt = normalize_for_match(dd_mmm).split("/")
    day = int(day_txt)
    month = SPANISH_MONTHS[month_txt]

    if periodo_inicio and periodo_fin:
        candidate_years = {periodo_inicio.year, periodo_fin.year}
        candidates = []

        for year in candidate_years:
            try:
                candidate = datetime(year, month, day)
            except ValueError:
                continue

            lower = periodo_inicio - timedelta(days=10)
            upper = periodo_fin + timedelta(days=10)

            if lower <= candidate <= upper:
                candidates.append(candidate)

        if candidates:
            best = min(candidates, key=lambda d: abs((d - periodo_fin).days))
            return best.strftime("%Y-%m-%d")

    year = default_year
    if statement_month is not None and statement_month <= 2 and month >= 11:
        year -= 1

    return datetime(year, month, day).strftime("%Y-%m-%d")


# ============================================================
# DESCRIPTION CLEANING
# ============================================================

def clean_description(text: str) -> str:
    text = normalize_spaces(text)

    replacements = {
        "RECIBIDOSANTANDER": "RECIBIDO SANTANDER",
        "RECIBIDOAZTECA": "RECIBIDO AZTECA",
        "RECIBIDOBANORTE": "RECIBIDO BANORTE",
        "RECIDOBANORTE": "RECIBIDO BANORTE",
        "RECIBIDOBANXICO": "RECIBIDO BANXICO",
        "ENVIADOBANCOPPEL": "ENVIADO BANCOPPEL",
        "ENVIADOHSBC": "ENVIADO HSBC",
        "ENVIADOAZTECA": "ENVIADO AZTECA",
        "ENVIADOBANORTE": "ENVIADO BANORTE",
        "OXXOBBVA": "OXXO BBVA",
        "PAGO DE NOMINA PAGO DE NOMINA": "PAGO DE NOMINA",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return normalize_spaces(text)


# ============================================================
# FULL TEXT AND SUMMARY EXTRACTION
# ============================================================

def extract_full_text(pdf_path: Path) -> str:
    doc = fitz.open(pdf_path)
    try:
        return "\n".join(page.get_text("text") for page in doc)
    finally:
        doc.close()


def regex_money(pattern: str, text: str) -> Optional[float]:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    return parse_amount(match.group(1))


def regex_int(pattern: str, text: str) -> Optional[int]:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def extract_resumen(pdf_path: Path, full_text: Optional[str] = None) -> dict:
    if full_text is None:
        full_text = extract_full_text(pdf_path)

    text = normalize_for_match(full_text)

    periodo_inicio = None
    periodo_fin = None

    period_match = re.search(
        r"PERIODO\s+DEL\s+(\d{2}/\d{2}/\d{4})\s+AL\s+(\d{2}/\d{2}/\d{4})",
        text,
    )
    if period_match:
        periodo_inicio = parse_pdf_date(period_match.group(1))
        periodo_fin = parse_pdf_date(period_match.group(2))

    fecha_corte = None
    cut_match = re.search(
        r"FECHA\s+DE\s+CORTE\s+(\d{2}/\d{2}/\d{4})",
        text,
    )
    if cut_match:
        fecha_corte = parse_pdf_date(cut_match.group(1))

    saldo_anterior = regex_money(
        r"SALDO\s+ANTERIOR\s+(-?[0-9,]+\.\d{2})",
        text,
    )
    saldo_final = regex_money(
        r"SALDO\s+FINAL\s+(-?[0-9,]+\.\d{2})",
        text,
    )
    saldo_promedio = regex_money(
        r"SALDO\s+PROMEDIO\s+(-?[0-9,]+\.\d{2})",
        text,
    )

    abonos_match = re.search(
        r"DEPOSITOS\s*/\s*ABONOS\s*\(\+\)\s+(\d+)\s+([0-9,]+\.\d{2})",
        text,
    )
    num_abonos = None
    total_abonos = None
    if abonos_match:
        num_abonos = int(abonos_match.group(1))
        total_abonos = parse_amount(abonos_match.group(2))

    cargos_match = re.search(
        r"RETIROS\s*/\s*CARGOS\s*\(-\)\s+(\d+)\s+([0-9,]+\.\d{2})",
        text,
    )
    num_cargos = None
    total_cargos = None
    if cargos_match:
        num_cargos = int(cargos_match.group(1))
        total_cargos = parse_amount(cargos_match.group(2))

    saldo_global = regex_money(
        r"SALDO\s+GLOBAL\s+\$?\s*(-?[0-9,]+\.\d{2})",
        text,
    )
    total_apartados = regex_int(
        r"TOTAL\s+DE\s+APARTADOS\s+(\d+)",
        text,
    )

    detalle_total_cargos = regex_money(
        r"TOTAL\s+IMPORTE\s+CARGOS\s+([0-9,]+\.\d{2})",
        text,
    )
    detalle_total_abonos = regex_money(
        r"TOTAL\s+IMPORTE\s+ABONOS\s+([0-9,]+\.\d{2})",
        text,
    )
    detalle_num_cargos = regex_int(
        r"TOTAL\s+MOVIMIENTOS\s+CARGOS\s+(\d+)",
        text,
    )
    detalle_num_abonos = regex_int(
        r"TOTAL\s+MOVIMIENTOS\s+ABONOS\s+(\d+)",
        text,
    )

    saldo_calculado = None
    diferencia_balance = None
    balance_cuadra = None

    if (
        saldo_anterior is not None
        and total_abonos is not None
        and total_cargos is not None
        and saldo_final is not None
    ):
        saldo_calculado = saldo_anterior + total_abonos - total_cargos
        diferencia_balance = saldo_calculado - saldo_final
        balance_cuadra = abs(diferencia_balance) <= 0.02

    return {
        "archivo": pdf_path.stem,
        "periodo_inicio": periodo_inicio,
        "periodo_fin": periodo_fin,
        "fecha_corte": fecha_corte,
        "saldo_anterior": saldo_anterior,
        "num_abonos": num_abonos,
        "total_abonos": total_abonos,
        "num_cargos": num_cargos,
        "total_cargos": total_cargos,
        "saldo_final": saldo_final,
        "saldo_promedio": saldo_promedio,
        "saldo_global": saldo_global,
        "total_apartados": total_apartados,
        "detalle_num_cargos": detalle_num_cargos,
        "detalle_total_cargos": detalle_total_cargos,
        "detalle_num_abonos": detalle_num_abonos,
        "detalle_total_abonos": detalle_total_abonos,
        "saldo_calculado": saldo_calculado,
        "diferencia_balance": diferencia_balance,
        "balance_cuadra": balance_cuadra,
    }


# ============================================================
# WORD EXTRACTION WITH PDF COORDINATES
# ============================================================

def extract_words(pdf_path: Path) -> list[dict]:
    doc = fitz.open(pdf_path)
    rows: list[dict] = []
    in_detail = False

    try:
        for page_num, page in enumerate(doc, start=1):
            page_text = normalize_for_match(page.get_text("text"))

            if "DETALLE DE MOVIMIENTOS REALIZADOS" in page_text:
                in_detail = True

            if not in_detail:
                continue

            for word in page.get_text("words"):
                x0, y0, x1, y1, text = word[:5]
                rows.append({
                    "pagina": page_num,
                    "x0": float(x0),
                    "y0": float(y0),
                    "x1": float(x1),
                    "y1": float(y1),
                    "text": normalize_spaces(text),
                })

            if "TOTAL DE MOVIMIENTOS" in page_text:
                in_detail = False
    finally:
        doc.close()

    return rows


def group_words_by_line(
    words: list[dict],
    y_tolerance: float = 2.5,
) -> list[list[dict]]:
    if not words:
        return []

    words = sorted(
        words,
        key=lambda w: (w["pagina"], w["y0"], w["x0"]),
    )

    lines: list[list[dict]] = []
    current_line: list[dict] = []
    current_page: Optional[int] = None
    current_y: Optional[float] = None

    for word in words:
        starts_new_line = (
            current_page is None
            or word["pagina"] != current_page
            or current_y is None
            or abs(word["y0"] - current_y) > y_tolerance
        )

        if starts_new_line:
            if current_line:
                lines.append(sorted(current_line, key=lambda w: w["x0"]))

            current_line = [word]
            current_page = word["pagina"]
            current_y = word["y0"]
        else:
            current_line.append(word)
            current_y = sum(w["y0"] for w in current_line) / len(current_line)

    if current_line:
        lines.append(sorted(current_line, key=lambda w: w["x0"]))

    return lines


# ============================================================
# COLUMN DETECTION
# ============================================================

def detectar_columnas(lines: list[list[dict]]) -> dict:
    reference_x0 = None
    cargo_x1 = None
    abono_x1 = None
    saldo_operacion_x1 = None
    saldo_liquidacion_x1 = None

    header_index = None

    for idx, line in enumerate(lines):
        upper_line = normalize_for_match(line_text(line))

        if "CARGOS" in upper_line and "ABONOS" in upper_line:
            header_index = idx

            for word in line:
                text = normalize_for_match(word["text"])

                if text == "REFERENCIA":
                    reference_x0 = float(word["x0"])
                elif text == "CARGOS":
                    cargo_x1 = float(word["x1"])
                elif text == "ABONOS":
                    abono_x1 = float(word["x1"])
                elif text == "OPERACION":
                    saldo_operacion_x1 = float(word["x1"])
                elif text == "LIQUIDACION":
                    saldo_liquidacion_x1 = float(word["x1"])

            break

    if header_index is None or cargo_x1 is None or abono_x1 is None:
        raise RuntimeError(
            "No se pudieron detectar las columnas CARGOS y ABONOS. "
            "Ejecuta con --debug-words para inspeccionar el PDF."
        )

    # Some versions render SALDO on one line and
    # OPERACION / LIQUIDACION on the next one.
    if saldo_operacion_x1 is None or saldo_liquidacion_x1 is None:
        start = max(0, header_index - 2)
        end = min(len(lines), header_index + 3)

        for line in lines[start:end]:
            for word in line:
                text = normalize_for_match(word["text"])

                if (
                    saldo_operacion_x1 is None
                    and text == "OPERACION"
                    and float(word["x0"]) > abono_x1
                ):
                    saldo_operacion_x1 = float(word["x1"])

                if (
                    saldo_liquidacion_x1 is None
                    and text == "LIQUIDACION"
                    and float(word["x0"]) > abono_x1
                ):
                    saldo_liquidacion_x1 = float(word["x1"])

    if reference_x0 is None:
        reference_x0 = cargo_x1 - 70.0

    return {
        "referencia_x0": reference_x0,
        "cargo_x1": cargo_x1,
        "abono_x1": abono_x1,
        "saldo_operacion_x1": saldo_operacion_x1,
        "saldo_liquidacion_x1": saldo_liquidacion_x1,
    }


def nearest_numeric_column(x1: float, columns: dict) -> str:
    candidates = {
        "cargo": columns["cargo_x1"],
        "abono": columns["abono_x1"],
        "saldo_operacion": columns["saldo_operacion_x1"],
        "saldo_liquidacion": columns["saldo_liquidacion_x1"],
    }

    candidates = {
        name: position
        for name, position in candidates.items()
        if position is not None
    }

    return min(
        candidates,
        key=lambda name: abs(x1 - candidates[name]),
    )


# ============================================================
# MOVEMENT PARSER
# ============================================================

def movement_start_info(line: list[dict]) -> Optional[tuple[dict, dict]]:
    dates = [word for word in line if is_date_token(word["text"])]

    if len(dates) < 2:
        return None

    dates = sorted(dates, key=lambda w: w["x0"])
    return dates[0], dates[1]


def extract_monetary_values_from_start_line(
    line: list[dict],
    columns: dict,
) -> dict:
    values = {
        "cargo": None,
        "abono": None,
        "saldo_operacion": None,
        "saldo_liquidacion": None,
    }

    for word in line:
        token = word["text"].replace("$", "").strip()

        if not is_amount(token):
            continue

        value = parse_amount(token)
        column = nearest_numeric_column(float(word["x1"]), columns)

        if values[column] is None:
            values[column] = value

    return values


def build_description(
    movement_lines: list[list[dict]],
    date_oper_word: dict,
    date_liq_word: dict,
    columns: dict,
) -> str:
    parts: list[str] = []

    description_left = max(
        float(date_oper_word["x1"]),
        float(date_liq_word["x1"]),
    )
    description_right = float(columns["referencia_x0"])

    ignore_exact = {
        "FECHA",
        "OPER",
        "LIQ",
        "DESCRIPCION",
        "REFERENCIA",
        "CARGOS",
        "ABONOS",
        "SALDO",
        "OPERACION",
        "LIQUIDACION",
    }

    ignore_contains = (
        "NO. DE CUENTA",
        "NO. DE CLIENTE",
        "ESTADO DE CUENTA",
        "PAGINA",
        "LIBRETON",
        "BBVA MEXICO",
        "AV. PASEO",
        "TOTAL DE MOVIMIENTOS",
    )

    for line in movement_lines:
        for word in line:
            text = normalize_spaces(word["text"])
            upper = normalize_for_match(text)

            if not text or is_date_token(text):
                continue

            if upper in ignore_exact:
                continue

            if any(pattern in upper for pattern in ignore_contains):
                continue

            center = word_x_center(word)

            if description_left < center < description_right:
                parts.append(text)

    return clean_description(" ".join(parts))


def lines_to_movimientos(
    lines: list[list[dict]],
    default_year: int,
    statement_month: Optional[int],
    periodo_inicio: Optional[datetime],
    periodo_fin: Optional[datetime],
) -> tuple[list[Movimiento], dict]:
    columns = detectar_columnas(lines)
    movimientos: list[Movimiento] = []

    i = 0
    n = len(lines)

    while i < n:
        current_line = lines[i]
        current_text = normalize_for_match(line_text(current_line))

        if "TOTAL DE MOVIMIENTOS" in current_text:
            break

        start_info = movement_start_info(current_line)
        if start_info is None:
            i += 1
            continue

        date_oper_word, date_liq_word = start_info
        page_num = int(current_line[0]["pagina"])

        movement_lines = [current_line]
        j = i + 1

        while j < n:
            next_line = lines[j]
            next_text = normalize_for_match(line_text(next_line))

            if "TOTAL DE MOVIMIENTOS" in next_text:
                break

            if int(next_line[0]["pagina"]) != page_num:
                break

            if movement_start_info(next_line) is not None:
                break

            movement_lines.append(next_line)
            j += 1

        fecha_oper = expand_date(
            date_oper_word["text"],
            default_year,
            periodo_inicio,
            periodo_fin,
            statement_month,
        )
        fecha_liq = expand_date(
            date_liq_word["text"],
            default_year,
            periodo_inicio,
            periodo_fin,
            statement_month,
        )

        values = extract_monetary_values_from_start_line(
            current_line,
            columns,
        )

        cargo = values["cargo"]
        abono = values["abono"]

        if cargo is not None and abono is not None:
            raise RuntimeError(
                "Se detectaron cargo y abono en la misma fila "
                f"({fecha_oper}, pagina {page_num}). "
                "Ejecuta con --debug-words."
            )

        if cargo is None and abono is None:
            i = max(j, i + 1)
            continue

        descripcion = build_description(
            movement_lines,
            date_oper_word,
            date_liq_word,
            columns,
        )

        movimientos.append(
            Movimiento(
                fecha_oper=fecha_oper,
                fecha_liq=fecha_liq,
                descripcion=descripcion,
                cargo=cargo,
                abono=abono,
                saldo_operacion=values["saldo_operacion"],
                saldo_liquidacion=values["saldo_liquidacion"],
                pagina=page_num,
            )
        )

        i = max(j, i + 1)

    return movimientos, columns


# ============================================================
# VALIDATION AGAINST PDF SUMMARY
# ============================================================

def validar_extraccion(movimientos: list[Movimiento], resumen: dict) -> dict:
    cargos_extraidos = sum(m.cargo or 0.0 for m in movimientos)
    abonos_extraidos = sum(m.abono or 0.0 for m in movimientos)

    num_cargos_extraidos = sum(m.cargo is not None for m in movimientos)
    num_abonos_extraidos = sum(m.abono is not None for m in movimientos)

    resumen["cargos_extraidos"] = cargos_extraidos
    resumen["abonos_extraidos"] = abonos_extraidos
    resumen["num_cargos_extraidos"] = num_cargos_extraidos
    resumen["num_abonos_extraidos"] = num_abonos_extraidos

    if resumen["total_cargos"] is not None:
        resumen["diferencia_cargos"] = cargos_extraidos - resumen["total_cargos"]
        resumen["cargos_cuadran"] = abs(resumen["diferencia_cargos"]) <= 0.02
    else:
        resumen["diferencia_cargos"] = None
        resumen["cargos_cuadran"] = None

    if resumen["total_abonos"] is not None:
        resumen["diferencia_abonos"] = abonos_extraidos - resumen["total_abonos"]
        resumen["abonos_cuadran"] = abs(resumen["diferencia_abonos"]) <= 0.02
    else:
        resumen["diferencia_abonos"] = None
        resumen["abonos_cuadran"] = None

    if resumen["num_cargos"] is not None:
        resumen["diferencia_num_cargos"] = num_cargos_extraidos - resumen["num_cargos"]
        resumen["num_cargos_cuadran"] = resumen["diferencia_num_cargos"] == 0
    else:
        resumen["diferencia_num_cargos"] = None
        resumen["num_cargos_cuadran"] = None

    if resumen["num_abonos"] is not None:
        resumen["diferencia_num_abonos"] = num_abonos_extraidos - resumen["num_abonos"]
        resumen["num_abonos_cuadran"] = resumen["diferencia_num_abonos"] == 0
    else:
        resumen["diferencia_num_abonos"] = None
        resumen["num_abonos_cuadran"] = None

    amount_checks = [
        resumen["cargos_cuadran"],
        resumen["abonos_cuadran"],
    ]
    count_checks = [
        resumen["num_cargos_cuadran"],
        resumen["num_abonos_cuadran"],
    ]

    resumen["extraccion_cuadra"] = (
        all(check is True for check in amount_checks)
        and all(check is True for check in count_checks)
    )

    return resumen


# ============================================================
# CSV WRITER / DEBUG
# ============================================================

def save_csv(dataframe: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(
        path,
        index=False,
        sep="|",
        encoding="utf-8-sig",
        quoting=csv.QUOTE_MINIMAL,
    )


def save_debug_words(words: list[dict], output_path: Path) -> Path:
    debug_path = output_path.with_name(
        output_path.stem + "_debug_words.csv"
    )
    pd.DataFrame(words).to_csv(
        debug_path,
        index=False,
        sep="|",
        encoding="utf-8-sig",
    )
    return debug_path


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--input", required=True, help="PDF de entrada")
    parser.add_argument("--output", required=True, help="CSV de movimientos")
    parser.add_argument("--saldo-output", help="CSV de saldo inicial/final")
    parser.add_argument("--resumen-output", help="CSV del resumen completo")
    parser.add_argument(
        "--debug-words",
        action="store_true",
        help="Guardar palabras y coordenadas X/Y",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    full_text = extract_full_text(input_path)
    resumen = extract_resumen(input_path, full_text)

    default_year = infer_year_from_filename(input_path)
    statement_month = infer_month_from_filename(input_path)

    periodo_inicio_dt = None
    periodo_fin_dt = None

    if resumen["periodo_inicio"]:
        periodo_inicio_dt = datetime.strptime(
            resumen["periodo_inicio"],
            "%Y-%m-%d",
        )

    if resumen["periodo_fin"]:
        periodo_fin_dt = datetime.strptime(
            resumen["periodo_fin"],
            "%Y-%m-%d",
        )

    words = extract_words(input_path)

    if not words:
        raise RuntimeError(
            "No se encontraron palabras en el bloque de movimientos."
        )

    if args.debug_words:
        debug_path = save_debug_words(words, output_path)
        print(f"Debug words guardado en: {debug_path}")

    lines = group_words_by_line(words)

    movimientos, columns = lines_to_movimientos(
        lines=lines,
        default_year=default_year,
        statement_month=statement_month,
        periodo_inicio=periodo_inicio_dt,
        periodo_fin=periodo_fin_dt,
    )

    if not movimientos:
        raise RuntimeError(
            "No se extrajeron movimientos. Ejecuta con --debug-words."
        )

    resumen = validar_extraccion(movimientos, resumen)

    resumen["x1_columna_cargos"] = columns["cargo_x1"]
    resumen["x1_columna_abonos"] = columns["abono_x1"]
    resumen["x1_columna_saldo_operacion"] = columns["saldo_operacion_x1"]
    resumen["x1_columna_saldo_liquidacion"] = columns["saldo_liquidacion_x1"]

    df_movimientos = pd.DataFrame(
        [asdict(movimiento) for movimiento in movimientos]
    )
    save_csv(df_movimientos, output_path)

    if args.saldo_output:
        saldo_path = Path(args.saldo_output)
        df_saldo = pd.DataFrame([
            {
                "archivo": input_path.stem,
                "fecha_corte": resumen["fecha_corte"],
                "saldo_anterior": resumen["saldo_anterior"],
                "saldo_final": resumen["saldo_final"],
            }
        ])
        save_csv(df_saldo, saldo_path)

    if args.resumen_output:
        resumen_path = Path(args.resumen_output)
        df_resumen = pd.DataFrame([resumen])
        save_csv(df_resumen, resumen_path)

    print()
    print(f"Movimientos extraidos: {len(df_movimientos)}")
    print(f"CSV generado: {output_path}")
    print()

    print("CARGOS")
    if resumen["total_cargos"] is not None:
        print(f"  PDF:             ${resumen['total_cargos']:,.2f}")
    else:
        print("  PDF:             no detectado")
    print(f"  Extraido:        ${resumen['cargos_extraidos']:,.2f}")
    if resumen["diferencia_cargos"] is not None:
        print(f"  Diferencia:      ${resumen['diferencia_cargos']:,.2f}")
    print(f"  Conteo PDF:      {resumen['num_cargos']}")
    print(f"  Conteo extraido: {resumen['num_cargos_extraidos']}")

    print()
    print("ABONOS")
    if resumen["total_abonos"] is not None:
        print(f"  PDF:             ${resumen['total_abonos']:,.2f}")
    else:
        print("  PDF:             no detectado")
    print(f"  Extraido:        ${resumen['abonos_extraidos']:,.2f}")
    if resumen["diferencia_abonos"] is not None:
        print(f"  Diferencia:      ${resumen['diferencia_abonos']:,.2f}")
    print(f"  Conteo PDF:      {resumen['num_abonos']}")
    print(f"  Conteo extraido: {resumen['num_abonos_extraidos']}")

    print()
    if resumen["extraccion_cuadra"]:
        print("VALIDACION OK: montos y conteos cuadran con el PDF.")
    else:
        print(
            "VALIDACION FALLIDA: revisar diferencias y ejecutar "
            "con --debug-words."
        )


if __name__ == "__main__":
    main()
