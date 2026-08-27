# Analytics Balance Creator

Analytics Balance Creator es un proyecto en Python para **extraer, validar, consolidar y analizar información financiera** proveniente de estados de cuenta BBVA en formato PDF.

Actualmente, el flujo estable del proyecto está enfocado en **estados de cuenta de débito BBVA**.

El proyecto permite extraer movimientos, saldos y resúmenes de los estados de cuenta, validar los datos obtenidos contra los valores reportados por BBVA y consolidar múltiples periodos para construir un historial financiero.

También se incluye una libreta compatible con **Google Colab y Jupyter Notebook** para analizar los datos, visualizar la evolución del saldo, clasificar movimientos y generar una primera propuesta automática de presupuesto mensual.

---

## Funcionalidades

### Extracción de cuenta de débito

- Extrae movimientos desde estados de cuenta BBVA en PDF.
- Identifica cargos y abonos utilizando la posición espacial de los elementos dentro del PDF.
- Soporta diferentes estructuras históricas de estados de cuenta.
- Extrae saldos iniciales y finales.
- Extrae los totales reportados por BBVA.
- Genera archivos CSV individuales y consolidados.

### Validación

Los movimientos extraídos se validan contra los valores reportados directamente por BBVA.

La principal comprobación de consistencia es:

```text
Saldo final = Saldo anterior + Abonos - Cargos
```

También se comparan:

```text
Abonos extraídos = Abonos reportados por BBVA
Cargos extraídos = Cargos reportados por BBVA
```

Esta validación debe completarse antes de utilizar los datos para análisis financieros.

### Análisis financiero

La libreta de Google Colab/Jupyter permite realizar:

- visualización histórica del saldo;
- análisis mensual de ingresos y egresos;
- análisis de flujo de efectivo;
- normalización de descripciones;
- identificación de comercios;
- clasificación automática de movimientos;
- detección de movimientos extraordinarios;
- identificación de pagos de tarjeta de crédito;
- separación de ahorro e inversión;
- generación automática de una propuesta de presupuesto mensual.

---

## Ejemplo de análisis

La libreta transforma los estados de cuenta consolidados en información que permite visualizar la evolución de la cuenta y analizar los patrones históricos de gasto.

Las siguientes imágenes fueron generadas utilizando **datos financieros completamente sintéticos**. No contienen movimientos bancarios ni información financiera personal real.

### Evolución histórica del saldo

Los saldos extraídos directamente de los estados de cuenta permiten reconstruir la evolución histórica real de la cuenta.

![Ejemplo de evolución histórica del saldo](docs/assets/balance-example.png)

### Presupuesto mensual sugerido

Después de clasificar los movimientos, la libreta analiza la frecuencia y comportamiento histórico de cada categoría para construir una primera propuesta de presupuesto mensual.

![Ejemplo de presupuesto mensual sugerido](docs/assets/budget-example.png)

El presupuesto generado debe interpretarse como un punto de partida basado en el comportamiento histórico y no como una recomendación financiera definitiva.

Consulta la [documentación completa](docs/index.md) para conocer la metodología utilizada.

---

## Estado del proyecto

| Componente | Estado |
|---|---|
| Extracción de movimientos de débito | Estable |
| Extracción de saldos de débito | Estable |
| Extracción de resúmenes de débito | Estable |
| Validación de débito | Estable |
| Consolidación de débito | Estable |
| Análisis en Colab/Jupyter | Funcional |
| Clasificación de movimientos | Funcional / en evolución |
| Estimación de presupuesto mensual | Funcional / en evolución |
| Extracción de tarjeta de crédito | En desarrollo |
| Integración débito + tarjeta de crédito | Planeada |

Los scripts relacionados con tarjeta de crédito (`TDC`) son experimentales y actualmente no deben utilizarse para obtener resultados financieros definitivos.

---

## Inicio rápido

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd Analytics_Balance_Creator
```

### 2. Crear un entorno virtual

```bash
python -m venv EdosEnv
```

Activa el entorno según tu sistema.

#### Windows PowerShell / CMD

```powershell
EdosEnv\Scripts\activate
```

#### Git Bash

```bash
source EdosEnv/Scripts/activate
```

#### macOS / Linux

```bash
source EdosEnv/bin/activate
```

### 3. Instalar las dependencias

```bash
pip install pandas pymupdf numpy matplotlib
```

### 4. Descargar los estados de cuenta

Descarga desde BBVA los estados de cuenta de débito que quieras analizar y colócalos en:

```text
Estados de cuenta/
```

Utiliza nombres que incluyan el mes y el año:

```text
Enero 2025.pdf
Febrero 2025.pdf
Marzo 2025.pdf
```

### 5. Procesar los estados de cuenta

Ejecuta:

```bash
python procesar_estados.py
```

Los datos generados se organizan bajo:

```text
csv_output/
├── consolidados/
├── saldos/
└── resumenes/
```

Antes de realizar el análisis, comprueba que los cargos, abonos y saldos extraídos coincidan con los valores reportados por BBVA.

---

## Flujo general

El proyecto sigue el siguiente flujo:

```text
Estados de cuenta PDF
        │
        ▼
     Extracción
        │
        ├──► Movimientos
        ├──► Saldos
        └──► Resúmenes
                 │
                 ▼
             Validación
                 │
                 ▼
           Consolidación
                 │
                 ▼
        Libreta de análisis
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
      Saldo    Gastos   Ingresos
                 │
                 ▼
          Clasificación
                 │
                 ▼
       Presupuesto mensual
```

---

## Documentación

La documentación completa del proyecto está disponible en:

**[Abrir la documentación](docs/index.md)**

El manual incluye:

- [Primeros pasos](docs/getting-started.md)
- [Extractor de débito](docs/debit-extractor.md)
- [Archivos de salida](docs/output-files.md)
- [Validación](docs/validation.md)
- [Análisis en Colab](docs/colab-analysis.md)
- [Clasificación de movimientos](docs/transaction-classification.md)
- [Presupuesto mensual](docs/monthly-budget.md)
- [Solución de problemas](docs/troubleshooting.md)
- [Desarrollo de TDC](docs/tdc-development.md)

---

## Documentación con MkDocs

La documentación está construida con [MkDocs](https://www.mkdocs.org/).

Instala MkDocs con:

```bash
pip install mkdocs
```

Para ejecutar la documentación localmente:

```bash
mkdocs serve
```

Después abre:

```text
http://127.0.0.1:8000/
```

Los archivos fuente de la documentación se encuentran en:

```text
docs/
```

y la navegación del manual se configura mediante:

```text
mkdocs.yml
```

---

## Estructura general

La estructura principal del proyecto es:

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
│   ├── assets/
│   │   ├── balance-example.png
│   │   └── budget-example.png
│   │
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
├── mkdocs.yml
└── README.md
```

---

## Privacidad

Este proyecto procesa información financiera personal.

No deben incluirse en el repositorio:

```text
Estados de cuenta/
csv_output/
csv_output_tdc/
```

Estas rutas deben permanecer excluidas mediante `.gitignore`.

Antes de realizar cualquier commit, revisa:

```bash
git status
```

y confirma que no aparezcan:

- estados de cuenta en PDF;
- archivos CSV generados;
- datos bancarios;
- información financiera personal.

Las imágenes utilizadas como ejemplo en la documentación deben generarse utilizando **datos sintéticos o completamente anonimizados**.

---

## Limitaciones

El proyecto depende de la estructura de los estados de cuenta observados hasta el momento.

Una nueva versión del PDF de BBVA puede requerir ajustes si cambian:

- los encabezados;
- la posición de las columnas;
- la estructura del resumen;
- el formato de las fechas;
- la organización de las páginas.

La clasificación automática de movimientos también utiliza reglas heurísticas y puede requerir revisión manual para operaciones que no puedan identificarse con suficiente confianza.

---

## Aviso

Las herramientas de extracción y análisis están diseñadas para facilitar el análisis de finanzas personales.

Antes de utilizar los resultados para tomar decisiones financieras, valida siempre los movimientos, cargos, abonos y saldos contra los estados de cuenta originales.

La clasificación automática puede cometer errores y el presupuesto mensual generado es una estimación basada en el comportamiento histórico. Debe ajustarse de acuerdo con las circunstancias, necesidades y objetivos financieros de cada usuario.
