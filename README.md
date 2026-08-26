# Analytics Balance Creator

Analytics Balance Creator is a Python project for extracting, validating, consolidating, and analyzing financial information from BBVA account statements in PDF format.

The current stable workflow supports **BBVA debit account statements**.

The project can extract transactions, balances, and statement summaries, validate the extracted data against the values reported by BBVA, and consolidate multiple statements into historical datasets.

A Google Colab/Jupyter notebook is also included for financial analysis, transaction classification, balance visualization, and automatic monthly budget estimation.

## Features

### Debit account extraction

- Extract transactions from BBVA PDF statements.
- Identify debits and credits using the spatial position of PDF elements.
- Support different historical statement layouts.
- Extract initial and final balances.
- Extract statement-level totals.
- Generate individual and consolidated CSV files.

### Validation

Extracted transactions are validated against the values reported by BBVA.

The main consistency check is:

```text
Final balance = Previous balance + Credits - Debits
```

The workflow also compares:

```text
Extracted credits = BBVA reported credits
Extracted debits  = BBVA reported debits
```

This validation should be completed before using the data for financial analysis.

### Financial analysis

The included Colab/Jupyter notebook provides:

- historical balance visualization;
- monthly income and expense analysis;
- cash-flow analysis;
- transaction description normalization;
- merchant identification;
- automatic transaction classification;
- detection of extraordinary transactions;
- identification of credit-card payments;
- separation of savings and investments;
- automatic monthly budget estimation.

## Project status

| Component | Status |
|---|---|
| Debit transaction extraction | Stable |
| Debit balance extraction | Stable |
| Debit statement summaries | Stable |
| Debit validation | Stable |
| Debit consolidation | Stable |
| Colab/Jupyter analysis | Functional |
| Transaction classification | Functional / evolving |
| Monthly budget estimation | Functional / evolving |
| Credit card extraction | In development |
| Debit + credit card integration | Planned |

Credit card (`TDC`) scripts are experimental and should not currently be used for definitive financial analysis.

## Quick start

Clone the repository:

```bash
git clone <REPOSITORY_URL>
cd Analytics_Balance_Creator
```

Create a virtual environment:

```bash
python -m venv EdosEnv
```

Activate it.

### Windows PowerShell / CMD

```powershell
EdosEnv\Scripts\activate
```

### Git Bash

```bash
source EdosEnv/Scripts/activate
```

### macOS / Linux

```bash
source EdosEnv/bin/activate
```

Install the dependencies:

```bash
pip install pandas pymupdf numpy matplotlib
```

Download the BBVA debit statements you want to analyze and place them in:

```text
Estados de cuenta/
```

Use filenames containing the month and year:

```text
Enero 2025.pdf
Febrero 2025.pdf
Marzo 2025.pdf
```

Process all statements with:

```bash
python procesar_estados.py
```

Generated data is organized under:

```text
csv_output/
├── consolidados/
├── saldos/
└── resumenes/
```

## Documentation

The complete project documentation is available in:

**[Open the documentation](docs/index.md)**

The manual includes:

- [Getting Started](docs/getting-started.md)
- [Debit Extractor](docs/debit-extractor.md)
- [Output Files](docs/output-files.md)
- [Validation](docs/validation.md)
- [Colab Analysis](docs/colab-analysis.md)
- [Transaction Classification](docs/transaction-classification.md)
- [Monthly Budget](docs/monthly-budget.md)
- [Troubleshooting](docs/troubleshooting.md)
- [TDC Development](docs/tdc-development.md)

## Documentation development

The documentation is built with [MkDocs](https://www.mkdocs.org/).

Install MkDocs:

```bash
pip install mkdocs
```

Run the documentation locally:

```bash
mkdocs serve
```

Then open:

```text
http://127.0.0.1:8000/
```

The documentation source files are stored under:

```text
docs/
```

and the navigation is configured in:

```text
mkdocs.yml
```

## Privacy

This project processes personal financial information.

Do not commit or publish:

```text
Estados de cuenta/
csv_output/
csv_output_tdc/
```

These directories should remain excluded through `.gitignore`.

Always review:

```bash
git status
```

before committing changes to make sure PDFs, generated CSV files, or other sensitive financial data are not included.

## Disclaimer

The extraction and analysis tools are intended to assist with personal financial analysis.

Always validate extracted transactions, balances, and classifications against the original bank statements before using the results for financial decisions.

The generated monthly budget is an estimate based on historical behavior and should be adjusted according to each user's financial circumstances and goals.