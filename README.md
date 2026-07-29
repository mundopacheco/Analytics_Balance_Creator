# Extracción de estados de cuenta BBVA

Este proyecto contiene scripts en Python para extraer movimientos desde estados de cuenta BBVA en PDF y consolidarlos en archivos CSV.

## Estado actual

Actualmente, el flujo funcional es el de **cuenta de débito**. Los scripts relacionados con tarjeta de crédito (`TDC`) siguen en desarrollo y no forman parte del flujo estable.

## Funcionalidad disponible

El flujo de débito permite:

- Leer estados de cuenta BBVA en PDF.
- Extraer movimientos de la sección `DETALLE DE MOVIMIENTOS REALIZADOS`.
- Separar cargos y abonos.
- Normalizar fechas y descripciones.
- Generar un CSV por cada PDF.
- Combinar todos los CSV en un archivo consolidado.

## Requisitos

- Python 3.10 o superior.
- `pip`.
- Estados de cuenta BBVA descargados en PDF.

Dependencias:

```text
pandas
PyMuPDF
```

## Instalación

```bash
git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DEL_REPOSITORIO>
```

### Windows

```powershell
python -m venv EdosEnv
EdosEnv\Scripts\activate
pip install pandas pymupdf
```

### macOS o Linux

```bash
python3 -m venv EdosEnv
source EdosEnv/bin/activate
pip install pandas pymupdf
```

## Estructura esperada

```text
.
├── Estados de cuenta/
│   ├── Enero 2025.pdf
│   ├── Febrero 2025.pdf
│   └── Marzo 2025.pdf
├── csv_output/
├── extract_bbva_debito.py
├── procesar_estados.py
├── debug_pdf_text.py
└── README.md
```

La carpeta `csv_output` se crea automáticamente.

## Preparación de los PDF

1. Descarga desde BBVA los estados de cuenta de débito que quieras analizar.
2. Guarda los PDF en `Estados de cuenta/`.
3. Asegúrate de que el nombre de cada archivo incluya el año, por ejemplo:

```text
Enero 2025.pdf
Febrero 2025.pdf
Marzo 2025.pdf
```

El extractor usa el año del nombre para reconstruir las fechas de los movimientos. No mezcles por ahora estados de cuenta de tarjeta de crédito en esta carpeta.

## Ejecución

### 1. Revisar un PDF de forma opcional

```powershell
python debug_pdf_text.py "Estados de cuenta/Enero 2025.pdf"
```

Esto permite comprobar que el PDF contiene texto seleccionable y que aparece la sección:

```text
DETALLE DE MOVIMIENTOS REALIZADOS
```

### 2. Probar un solo estado de cuenta

```powershell
python extract_bbva_debito.py --input "Estados de cuenta/Enero 2025.pdf" --output "csv_output/Enero 2025.csv"
```

Para guardar también los tokens detectados:

```powershell
python extract_bbva_debito.py --input "Estados de cuenta/Enero 2025.pdf" --output "csv_output/Enero 2025.csv" --debug-tokens
```

### 3. Procesar todos los estados de cuenta

```powershell
python procesar_estados.py
```

Este script:

1. Busca todos los PDF en `Estados de cuenta/`.
2. Ejecuta `extract_bbva_debito.py` para cada archivo.
3. Guarda un CSV por PDF en `csv_output/`.
4. Combina los resultados.
5. Genera `csv_output/movimientos_debito_total.csv`.

## Formato de salida

El CSV consolidado utiliza `|` como separador y contiene:

```text
fecha_oper
fecha_liq
descripcion
cargo
abono
pagina
archivo_origen
```

Ejemplo:

```text
fecha_oper|fecha_liq|descripcion|cargo|abono|pagina|archivo_origen
2025-01-03|2025-01-03|PAGO DE NOMINA||17821.00|2|Enero 2025
2025-01-05|2025-01-06|COMPRA COMERCIO|350.00||3|Enero 2025
```

## Orden recomendado

```text
1. Descargar los PDF.
2. Colocarlos en Estados de cuenta/.
3. Verificar que el nombre incluya el año.
4. Ejecutar debug_pdf_text.py si es necesario.
5. Probar extract_bbva_debito.py con un archivo.
6. Ejecutar procesar_estados.py.
7. Analizar csv_output/movimientos_debito_total.csv.
```

## Solución de problemas

### No se puede inferir el año

El nombre debe incluir un año de cuatro dígitos, por ejemplo `Enero 2025.pdf`.

### No se extrajeron movimientos

Ejecuta el extractor con `--debug-tokens` y revisa el archivo generado. También puedes inspeccionar el texto con:

```powershell
python debug_pdf_text.py "Estados de cuenta/Archivo.pdf"
```

### El PDF no contiene texto seleccionable

El extractor usa PyMuPDF y espera texto embebido. Si el documento es una imagen escaneada, será necesario añadir OCR.

### El CSV está vacío o incompleto

Revisa que el PDF contenga `DETALLE DE MOVIMIENTOS REALIZADOS` y fechas con un formato similar a `22/ENE`.

## Scripts de tarjeta de crédito

Los siguientes archivos corresponden a pruebas de extracción de TDC y todavía no forman parte del flujo estable:

```text
extract_bbva_tdc_desglose.py
extract_bbva_tdc_movimientos.py
extract_bbva_tdc_regulares.py
extract_bbva_tdc_resumen.py
procesar_tdc.py
limpiar_tdc.py
```

Pueden conservarse como trabajo en progreso, pero no se recomienda usarlos para resultados financieros definitivos.

## `.gitignore` recomendado

```gitignore
EdosEnv/
.venv/
venv/
__pycache__/
*.pyc
Estados de cuenta/
csv_output/
csv_output_tdc/
tmp/
.DS_Store
Thumbs.db
```

Esto evita subir accidentalmente estados de cuenta, CSV generados o información financiera sensible.

## Aviso

Este proyecto procesa información financiera personal. Revisa los resultados antes de utilizarlos para análisis contables o financieros y evita subir al repositorio estados de cuenta o archivos CSV generados.
