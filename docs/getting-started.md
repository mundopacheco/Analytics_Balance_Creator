# Getting Started

Esta guía describe cómo preparar el entorno, descargar los estados de cuenta y ejecutar por primera vez Analytics Balance Creator.

Actualmente, el flujo estable del proyecto corresponde a **estados de cuenta de débito BBVA**.

Los scripts relacionados con tarjeta de crédito (TDC) continúan en desarrollo y no deben mezclarse con los estados de cuenta utilizados por el extractor de débito.

---

## Requisitos

Para ejecutar el proyecto necesitas:

- Python 3.10 o superior.
- `pip`.
- Git.
- Estados de cuenta BBVA de débito en formato PDF.

Las principales dependencias de Python son:

```text
pandas
PyMuPDF
numpy
matplotlib
```

`PyMuPDF` se instala mediante el paquete:

```text
pymupdf
```

---

## Clonar el repositorio

Clona el repositorio y entra en la carpeta del proyecto:

```bash
git clone <URL_DEL_REPOSITORIO>
cd Analytics_Balance_Creator
```

Si ya tienes el repositorio clonado, actualízalo con:

```bash
git pull
```

---

## Crear un entorno virtual

Se recomienda utilizar un entorno virtual para mantener las dependencias del proyecto separadas de otras instalaciones de Python.

### Windows

Desde PowerShell, CMD o Git Bash:

```bash
python -m venv EdosEnv
```

Si utilizas PowerShell o CMD, puedes activar el entorno con:

```powershell
EdosEnv\Scripts\activate
```

Si utilizas Git Bash:

```bash
source EdosEnv/Scripts/activate
```

Cuando el entorno esté activo deberías ver algo similar a:

```text
(EdosEnv)
```

al inicio de la línea de comandos.

### macOS o Linux

```bash
python3 -m venv EdosEnv
source EdosEnv/bin/activate
```

---

## Instalar dependencias

Con el entorno virtual activo:

```bash
pip install pandas pymupdf numpy matplotlib
```

Puedes comprobar que PyMuPDF se instaló correctamente con:

```bash
python -c "import fitz; print(fitz.__doc__)"
```

---

## Estructura del proyecto

Después de clonar el repositorio, la estructura general será similar a:

```text
Analytics_Balance_Creator/
│
├── Estados de cuenta/
│
├── csv_output/
│   ├── consolidados/
│   ├── saldos/
│   └── resumenes/
│
├── docs/
│   ├── index.md
│   ├── getting-started.md
│   ├── debit-extractor.md
│   ├── output-files.md
│   ├── validation.md
│   ├── colab-analysis.md
│   ├── transaction-classification.md
│   ├── monthly-budget.md
│   ├── troubleshooting.md
│   └── tdc-development.md
│
├── extract_bbva_debito.py
├── procesar_estados.py
├── debug_pdf_text.py
├── README.md
└── ...
```

Las carpetas de salida necesarias pueden ser creadas automáticamente por los scripts durante el procesamiento.

---

# Preparar los estados de cuenta

## 1. Descargar los PDF

Descarga desde BBVA los estados de cuenta de débito correspondientes al periodo que quieras analizar.

El extractor espera archivos PDF que contengan texto embebido y seleccionable.

No es necesario convertir los estados de cuenta a imágenes ni extraer manualmente su contenido.

---

## 2. Guardar los archivos

Coloca los estados de cuenta en:

```text
Estados de cuenta/
```

Por ejemplo:

```text
Estados de cuenta/
├── Enero 2025.pdf
├── Febrero 2025.pdf
├── Marzo 2025.pdf
└── Abril 2025.pdf
```

---

## 3. Nombrar correctamente los PDF

El nombre de cada archivo debe incluir el año del estado de cuenta.

Se recomienda utilizar el formato:

```text
Mes Año.pdf
```

Por ejemplo:

```text
Enero 2025.pdf
Febrero 2025.pdf
Marzo 2025.pdf
```

El año contenido en el nombre puede utilizarse durante la extracción para reconstruir o validar las fechas de los movimientos.

Evita nombres como:

```text
Enero.pdf
estado1.pdf
bbva.pdf
```

porque no contienen suficiente información temporal.

---

## 4. No mezclar estados de cuenta

La carpeta utilizada por el flujo de débito debe contener únicamente estados de cuenta compatibles con este extractor.

Por el momento, no coloques en la misma carpeta:

- estados de cuenta de tarjeta de crédito;
- estados de cuenta de otros bancos;
- archivos CSV;
- imágenes;
- documentos escaneados sin texto seleccionable.

Los scripts de TDC se encuentran todavía en desarrollo.

---

# Verificar un PDF

Antes de procesar todo el historial, es recomendable comprobar uno de los estados de cuenta.

Puedes inspeccionar el texto detectado por PyMuPDF mediante:

```bash
python debug_pdf_text.py "Estados de cuenta/Enero 2025.pdf"
```

Esto permite comprobar que el PDF contiene texto que puede ser interpretado por el extractor.

También resulta útil cuando:

- falta algún movimiento;
- un cargo aparece como abono;
- un abono aparece como cargo;
- cambia el formato del estado de cuenta;
- no se detecta alguna sección;
- se necesita investigar cómo está estructurado el PDF.

---

# Probar el extractor con un archivo

Antes de procesar todos los estados de cuenta, prueba un PDF representativo.

```bash
python extract_bbva_debito.py \
  --input "Estados de cuenta/Enero 2025.pdf" \
  --output "csv_output/Enero 2025.csv"
```

En Windows, si tu terminal no admite fácilmente comandos multilínea, puedes escribirlo en una sola línea:

```bash
python extract_bbva_debito.py --input "Estados de cuenta/Enero 2025.pdf" --output "csv_output/Enero 2025.csv"
```

El extractor mostrará información sobre el procesamiento y las validaciones disponibles para ese estado de cuenta.

---

## Modo de depuración

Si necesitas inspeccionar con mayor detalle cómo se está interpretando el PDF, utiliza:

```bash
python extract_bbva_debito.py --input "Estados de cuenta/Enero 2025.pdf" --output "csv_output/Enero 2025.csv" --debug-tokens
```

Este modo es especialmente útil cuando BBVA modifica la estructura visual de sus estados de cuenta.

El extractor utiliza información posicional del PDF para distinguir, entre otras cosas, las columnas correspondientes a cargos y abonos.

---

# Procesar todos los estados de cuenta

Una vez que un PDF representativo haya sido procesado correctamente, ejecuta:

```bash
python procesar_estados.py
```

Este script automatiza el procesamiento del conjunto de estados de cuenta disponibles.

El flujo general es:

```text
PDF
 │
 ▼
Extracción de movimientos
 │
 ├──► Saldos
 │
 ├──► Resumen del periodo
 │
 ▼
Validación
 │
 ▼
Archivos CSV individuales
 │
 ▼
Consolidados históricos
```

Al finalizar, revisa el resumen mostrado en la terminal para confirmar que los PDF fueron procesados correctamente.

---

# Archivos de salida

El procesamiento genera diferentes tipos de información.

Los archivos consolidados se organizan bajo:

```text
csv_output/
├── consolidados/
├── saldos/
└── resumenes/
```

Conceptualmente, el análisis utiliza tres conjuntos de datos:

### Movimientos

Permiten responder:

> ¿Qué operaciones ocurrieron dentro de la cuenta?

Incluyen cargos, abonos, fechas y descripciones.

### Saldos

Permiten responder:

> ¿Cuánto dinero había realmente en la cuenta?

Los saldos reportados por BBVA son utilizados posteriormente para visualizar la evolución histórica real de la cuenta.

### Resúmenes

Permiten responder:

> ¿La extracción coincide con los totales reportados por BBVA?

Los resúmenes contienen los valores utilizados para validar cargos, abonos y cambios de saldo.

Consulta [Output Files](output-files.md) para conocer en detalle la estructura de estos archivos.

---

# Validar antes de analizar

Antes de utilizar los datos para análisis financieros, comprueba que la extracción sea consistente con el estado de cuenta.

La relación fundamental es:

```text
Saldo final = Saldo anterior + Abonos - Cargos
```

También deben compararse:

```text
Abonos extraídos = Abonos reportados por BBVA

Cargos extraídos = Cargos reportados por BBVA
```

Si estas validaciones no coinciden, revisa el problema antes de continuar con la libreta de análisis.

Consulta [Validation](validation.md) para conocer el proceso completo de validación.

---

# Ejecutar el análisis

Después de generar y validar los archivos consolidados, puedes utilizar la libreta de análisis incluida en el repositorio.

La libreta permite:

- visualizar la evolución histórica del saldo;
- analizar ingresos y egresos mensuales;
- validar el flujo contra los estados de cuenta;
- normalizar descripciones;
- identificar comercios;
- clasificar gastos;
- detectar movimientos extraordinarios;
- separar ahorro e inversión;
- identificar pagos de tarjeta de crédito;
- generar una propuesta automática de presupuesto mensual.

Consulta [Colab Analysis](colab-analysis.md) para continuar con esta etapa.

---

# Orden recomendado

El flujo recomendado completo es:

```text
1. Clonar o actualizar el repositorio.

2. Crear y activar el entorno virtual.

3. Instalar las dependencias.

4. Descargar los estados de cuenta desde BBVA.

5. Colocar los PDF en:
   Estados de cuenta/

6. Verificar que los nombres incluyan mes y año.

7. Inspeccionar un PDF con debug_pdf_text.py si es necesario.

8. Probar extract_bbva_debito.py con un archivo representativo.

9. Confirmar que cargos, abonos y saldos sean correctos.

10. Ejecutar procesar_estados.py.

11. Revisar los archivos consolidados.

12. Abrir la libreta de análisis.

13. Validar los datos antes de realizar análisis financieros.

14. Revisar la clasificación automática.

15. Analizar el presupuesto mensual sugerido.
```

---

# Privacidad

Los estados de cuenta contienen información financiera sensible.

No subas al repositorio:

```text
Estados de cuenta/
csv_output/
```

Estas rutas deben permanecer excluidas mediante `.gitignore`.

Antes de realizar un `git add`, puedes comprobar los archivos pendientes con:

```bash
git status
```

Esto ayuda a evitar que estados de cuenta o archivos financieros generados sean incluidos accidentalmente en un commit.

---

## Siguiente paso

Una vez preparado el entorno y los estados de cuenta, continúa con:

**[Debit Extractor →](debit-extractor.md)**

para conocer cómo funciona el proceso de extracción y cómo se identifican los movimientos dentro de los PDF.