# Analytics Balance Creator

BBVA Bank Statement Extractor

This project extracts transaction data from BBVA bank statement PDFs and converts them into structured CSV files for further financial analysis.

## Current Status

✅ **Debit account extraction is fully functional.**

⚠️ **Credit card (TDC) extraction is still under development and should not be considered stable.**

---

# Features

The current implementation supports:

- Extracting debit account transactions from BBVA PDF statements.
- Parsing transaction dates, descriptions, charges, and deposits.
- Generating one CSV per PDF.
- Merging all extracted transactions into a single consolidated CSV.
- Exporting data using a pipe (`|`) separator.

---

# Requirements

- Python 3.10+
- pip

Required packages:

```bash
pip install pandas pymupdf
```

---

# Project Structure

```
.
├── Estados de cuenta/
│   ├── January 2025.pdf
│   ├── February 2025.pdf
│   └── ...
│
├── csv_output/
│
├── extract_bbva_debito.py
├── procesar_estados.py
├── debug_pdf_text.py
│
├── extract_bbva_tdc_*.py        # Work in progress
├── procesar_tdc.py              # Work in progress
├── limpiar_tdc.py               # Work in progress
│
└── README.md
```

The `csv_output` folder will be created automatically if it does not exist.

---

# Preparing the PDF Statements

1. Download your BBVA **debit account** statements in PDF format.

2. Place all PDFs inside:

```
Estados de cuenta/
```

3. Make sure each file name contains the year.

Examples:

```
January 2025.pdf
February 2025.pdf
March 2025.pdf
```

The extractor uses the year found in the filename to reconstruct complete transaction dates.

---

# Running the Project

## 1. Inspect a PDF (optional)

If you want to verify that the PDF contains selectable text:

```bash
python debug_pdf_text.py "Estados de cuenta/January 2025.pdf"
```

The extractor expects the section:

```
DETALLE DE MOVIMIENTOS REALIZADOS
```

to be present in the document.

---

## 2. Extract a Single Statement

```bash
python extract_bbva_debito.py \
    --input "Estados de cuenta/January 2025.pdf" \
    --output "csv_output/January 2025.csv"
```

If you want to inspect the detected tokens:

```bash
python extract_bbva_debito.py \
    --input "Estados de cuenta/January 2025.pdf" \
    --output "csv_output/January 2025.csv" \
    --debug-tokens
```

This generates:

```
csv_output/January 2025_debug_tokens.txt
```

which can be useful for debugging extraction issues.

---

## 3. Process All Statements

```bash
python procesar_estados.py
```

The script will:

1. Scan the `Estados de cuenta/` directory.
2. Extract each PDF individually.
3. Generate one CSV per statement.
4. Merge every CSV into a single dataset.
5. Export:

```
csv_output/movimientos_debito_total.csv
```

---

# Output Format

The consolidated CSV contains:

```
fecha_oper
fecha_liq
descripcion
cargo
abono
pagina
archivo_origen
```

Example:

```
fecha_oper|fecha_liq|descripcion|cargo|abono|pagina|archivo_origen
2025-01-03|2025-01-03|Payroll Deposit||17821.00|2|January 2025
2025-01-05|2025-01-06|Grocery Store|350.00||3|January 2025
```

---

# Recommended Workflow

```
1. Download BBVA debit statements.
2. Place them inside "Estados de cuenta/".
3. Verify that filenames include the year.
4. (Optional) Run debug_pdf_text.py.
5. Test one PDF with extract_bbva_debito.py.
6. Run procesar_estados.py.
7. Analyze csv_output/movimientos_debito_total.csv.
```

---

# Troubleshooting

## No year detected

The filename must contain a four-digit year.

Correct:

```
January 2025.pdf
```

Incorrect:

```
January.pdf
```

---

## No transactions extracted

Run:

```bash
python extract_bbva_debito.py --debug-tokens
```

or inspect the PDF using:

```bash
python debug_pdf_text.py "Estados de cuenta/statement.pdf"
```

---

## PDF contains scanned images

The current extractor expects machine-readable PDFs.

Scanned documents require an OCR step before extraction.

---

# Credit Card (TDC)

The following scripts are experimental and are **not part of the stable workflow**:

```
extract_bbva_tdc_desglose.py
extract_bbva_tdc_movimientos.py
extract_bbva_tdc_regulares.py
extract_bbva_tdc_resumen.py
procesar_tdc.py
limpiar_tdc.py
```

These scripts are still being developed and should not be used for financial reconciliation.

---

# Recommended .gitignore

```gitignore
# Virtual environments
EdosEnv/
venv/
.venv/

# Python
__pycache__/
*.pyc

# Personal bank statements
Estados de cuenta/

# Generated CSV files
csv_output/
csv_output_tdc/
tmp/

# Operating system
.DS_Store
Thumbs.db
```

This prevents accidentally committing personal financial information.

---

# Disclaimer

This project processes personal financial data.

Always verify the generated CSV files before using them for financial analysis, budgeting, or accounting.

Do **not** commit bank statements or generated transaction files to public repositories.
