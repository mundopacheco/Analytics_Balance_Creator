# Extracción y análisis de estados de cuenta BBVA

Este proyecto contiene herramientas en Python para extraer, validar, consolidar y analizar información financiera proveniente de estados de cuenta BBVA en formato PDF.

El flujo actualmente estable corresponde a **cuentas de débito**.

Además de extraer movimientos, el proyecto obtiene los saldos y resúmenes reportados por BBVA. Esta información permite validar que los cargos y abonos extraídos reproduzcan correctamente el cambio de saldo de cada periodo.

El repositorio también incluye una libreta de Google Colab/Jupyter para analizar los archivos consolidados, visualizar la evolución del saldo, clasificar gastos y generar una primera propuesta automática de presupuesto mensual.

---

## Estado actual

### Cuenta de débito

El flujo de débito se encuentra funcional e incluye:

- extracción de movimientos;
- identificación de cargos y abonos;
- extracción de saldos iniciales y finales;
- extracción del resumen de cada periodo;
- validación de cargos y abonos contra los totales reportados por BBVA;
- generación de archivos individuales;
- generación de archivos consolidados;
- análisis histórico en una libreta de Colab;
- clasificación automática de movimientos;
- generación de una propuesta de presupuesto mensual.

### Tarjeta de crédito

Los scripts relacionados con tarjeta de crédito (`TDC`) siguen en desarrollo y **no forman parte del flujo estable**.

Por el momento, los pagos realizados desde la cuenta de débito hacia una tarjeta de crédito pueden identificarse como `pago_tdc`, pero no se analizan todavía los movimientos internos de la tarjeta.

---

# Funcionalidad disponible

## Extracción

El extractor de débito permite:

- leer estados de cuenta BBVA en PDF;
- detectar diferentes estructuras históricas del estado de cuenta;
- extraer movimientos de la sección de detalle;
- utilizar la posición del texto dentro del PDF para distinguir cargos y abonos;
- normalizar fechas;
- conservar la descripción de cada movimiento;
- identificar la página de origen;
- extraer el saldo inicial y final del periodo;
- extraer los totales de cargos y abonos reportados por BBVA;
- generar archivos CSV individuales.

La identificación de cargos y abonos utiliza la información posicional obtenida mediante:

```python
page.get_text("words")
```

Esto permite utilizar las coordenadas horizontales del PDF para determinar en qué columna se encuentra cada importe, en lugar de depender únicamente del orden en que PyMuPDF devuelve el texto.

---

## Validación

Para cada periodo es posible comprobar la relación:

```text
Saldo final = Saldo anterior + Abonos - Cargos
```

Los totales extraídos de los movimientos también pueden compararse contra los totales reportados directamente por BBVA.

Esto permite detectar errores de extracción antes de utilizar los datos para análisis financieros.

---

## Análisis

La libreta incluida en el repositorio utiliza los archivos consolidados para realizar, entre otros, los siguientes análisis:

- limpieza y normalización de datos;
- validación de cargos y abonos;
- comparación contra los saldos reportados por BBVA;
- flujo mensual de ingresos y egresos;
- evolución histórica del saldo;
- detección de movimientos extraordinarios;
- normalización de descripciones;
- identificación de comercios y contrapartes;
- clasificación de egresos;
- identificación de pagos de tarjeta de crédito;
- separación de ahorro e inversión;
- análisis de frecuencia de gastos;
- generación de una propuesta de presupuesto mensual.

---

# Requisitos

- Python 3.10 o superior.
- `pip`.
- Estados de cuenta BBVA descargados en PDF.

Dependencias principales:

```text
pandas
PyMuPDF
```

Para la libreta de análisis también se utilizan:

```text
numpy
matplotlib
pandas
```

---

# Instalación

Clona el repositorio:

```bash
git clone git@github.com:mundopacheco/Analytics_Balance_Creator.git
cd path/to/Analytics_Balance_Creator
```

## Windows

```powershell
python -m venv EdosEnv
EdosEnv\Scripts\activate
pip install pandas pymupdf numpy matplotlib
```

## macOS o Linux

```bash
python3 -m venv EdosEnv
source EdosEnv/bin/activate
pip install pandas pymupdf numpy matplotlib
```

---

# Estructura del proyecto

La estructura general esperada es similar a:

```text
.
├── Estados de cuenta/
│   ├── Enero 2025.pdf
│   ├── Febrero 2025.pdf
│   └── Marzo 2025.pdf
│
├── csv_output/
│   ├── consolidados/
│   ├── saldos/
│   └── resumenes/
│
├── extract_bbva_debito.py
├── procesar_estados.py
├── debug_pdf_text.py
├── Análisis_Débito_Publicar.ipynb
└── README.md
```

Las carpetas de salida se crean automáticamente cuando es necesario.

---

# Preparación de los PDF

1. Descarga desde BBVA los estados de cuenta de débito que quieras analizar.
2. Guarda los archivos PDF en:

```text
Estados de cuenta/
```

3. Asegúrate de que el nombre de cada archivo incluya el mes y el año.

Por ejemplo:

```text
Enero 2025.pdf
Febrero 2025.pdf
Marzo 2025.pdf
```

El nombre del archivo puede utilizarse durante la extracción para ayudar a reconstruir o validar las fechas del periodo.

No mezcles estados de cuenta de tarjeta de crédito con los estados de cuenta de débito utilizados por este flujo.

---

# Ejecución

## 1. Revisar un PDF de forma opcional

Para inspeccionar el texto que PyMuPDF detecta dentro de un estado de cuenta:

```powershell
python debug_pdf_text.py "Estados de cuenta/Enero 2025.pdf"
```

Esto puede ser útil cuando:

- cambia el formato del estado de cuenta;
- no se detecta algún movimiento;
- un cargo aparece como abono o viceversa;
- no se encuentra alguna sección esperada;
- se necesita inspeccionar cómo PyMuPDF interpreta el PDF.

---

## 2. Probar un solo estado de cuenta

Ejecuta:

```powershell
python extract_bbva_debito.py --input "Estados de cuenta/Enero 2025.pdf" --output "csv_output/Enero 2025.csv"
```

Para guardar información adicional utilizada durante la detección:

```powershell
python extract_bbva_debito.py --input "Estados de cuenta/Enero 2025.pdf" --output "csv_output/Enero 2025.csv" --debug-tokens
```

Es recomendable probar primero uno o varios estados de cuenta representativos antes de procesar todo el historial.

---

## 3. Procesar todos los estados de cuenta

Ejecuta:

```powershell
python procesar_estados.py
```

El flujo procesa todos los PDF disponibles y genera los archivos individuales y consolidados correspondientes.

---

# Archivos generados

El procesamiento genera tres tipos principales de información.

## 1. Movimientos

Contienen el detalle de las operaciones detectadas en los estados de cuenta.

Entre los campos principales se encuentran:

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

---

## 2. Saldos

Los archivos de saldos contienen la información necesaria para reconstruir la evolución real de la cuenta a partir de los estados de cuenta.

Dependiendo de la versión del PDF, el extractor obtiene los campos correspondientes al saldo reportado por BBVA para cada periodo.

Estos datos son especialmente importantes porque permiten visualizar el saldo histórico real sin intentar reconstruirlo únicamente mediante una suma acumulada de movimientos.

---

## 3. Resúmenes

Los resúmenes contienen información agregada de cada estado de cuenta, incluyendo los valores necesarios para validar el periodo.

Entre los campos utilizados por el análisis se encuentran:

```text
periodo_inicio
periodo_fin
fecha_corte
saldo_anterior
total_abonos
total_cargos
saldo_final
```

La información permite verificar:

```text
saldo_anterior + total_abonos - total_cargos = saldo_final
```

y comparar esos totales contra la suma de los movimientos extraídos.

---

# Archivos consolidados

Los resultados históricos se almacenan en:

```text
csv_output/consolidados/
```

Los consolidados permiten analizar múltiples estados de cuenta como una sola serie histórica.

El análisis utiliza tres fuentes conceptuales:

```text
Movimientos
Saldos
Resúmenes
```

Cada una cumple una función distinta:

- **Movimientos:** qué ocurrió dentro de la cuenta.
- **Saldos:** cuánto dinero había realmente en determinados puntos del tiempo.
- **Resúmenes:** información de control para validar que la extracción sea consistente con el estado de cuenta.

---

# Validación de la extracción

Antes de realizar análisis financieros, se recomienda comprobar que los movimientos extraídos coincidan con los valores reportados por BBVA.

Para cada periodo se validan:

```text
Abonos extraídos = Abonos reportados por BBVA
Cargos extraídos = Cargos reportados por BBVA
```

y:

```text
Saldo anterior + Abonos - Cargos = Saldo final
```

Pequeñas diferencias del orden de:

```text
1e-12
1e-13
```

pueden aparecer debido a la representación de números de punto flotante y equivalen, para efectos financieros, a una diferencia de `$0.00`.

---

# Libreta de análisis

El repositorio incluye una libreta compatible con Google Colab/Jupyter que utiliza los archivos consolidados generados por el extractor.

La libreta está diseñada para que el análisis no dependa de rutas, fechas o cantidades específicas de una sola persona.

---

## Carga y limpieza

La libreta:

- carga los archivos consolidados;
- normaliza nombres de columnas;
- convierte fechas;
- limpia importes;
- elimina registros inválidos;
- prepara los DataFrames utilizados por las etapas posteriores.

---

## Evolución del saldo

Los saldos extraídos directamente de los estados de cuenta se utilizan para visualizar la evolución histórica real de la cuenta.

Esto es preferible a interpretar una simple suma acumulada de movimientos como si fuera el saldo bancario, ya que el primer estado de cuenta disponible puede comenzar con un saldo distinto de cero.

---

## Flujo mensual

Los movimientos se agrupan para analizar:

```text
Ingresos
Gastos
Flujo neto
```

por mes.

También es posible utilizar los periodos reales de cada estado de cuenta para comprobar que el flujo calculado reproduzca correctamente el cambio de saldo reportado por BBVA.

---

# Clasificación de movimientos

La libreta incluye reglas generales para normalizar descripciones y reconocer patrones frecuentes.

La clasificación intenta distinguir conceptos como:

```text
alimentacion
vivienda
transporte
telecomunicaciones
salud
educacion
seguros
compras
entretenimiento
suscripciones
comisiones
efectivo
pago_tdc
ahorro_inversion
otros
```

También distingue movimientos cuya naturaleza no corresponde directamente a consumo:

```text
transferencias
financiamiento
gastos extraordinarios
ahorro e inversión
```

Las reglas están diseñadas para ser genéricas y pueden reconocer comercios, servicios e instituciones frecuentes en México.

Sin embargo, ningún clasificador basado únicamente en la descripción bancaria puede determinar correctamente el propósito de todos los movimientos.

Los conceptos que no pueden clasificarse con suficiente confianza permanecen en:

```text
otros
```

o en categorías que requieren revisión.

---

# Pagos de tarjeta de crédito

Los pagos realizados desde la cuenta de débito hacia una tarjeta se clasifican actualmente como:

```text
pago_tdc
```

y se muestran explícitamente en el presupuesto.

No se asume automáticamente que estos pagos representen deuda, ya que una tarjeta de crédito también puede utilizarse como medio de pago para gastos corrientes.

Cuando se incorpore el análisis estable de movimientos de TDC será necesario evitar contar dos veces el mismo consumo:

1. cuando se realiza la compra con la tarjeta;
2. cuando se paga posteriormente la tarjeta desde la cuenta de débito.

---

# Presupuesto mensual sugerido

La libreta genera una primera estimación automática de presupuesto utilizando el comportamiento histórico de los gastos.

Para cada categoría se calculan métricas como:

```text
Meses con gasto
Frecuencia
Mediana mensual
Promedio de los últimos 3 meses
Provisión mensual
Presupuesto sugerido
```

---

## Frecuencia

La frecuencia representa la proporción de meses en los que apareció una categoría.

Las categorías se clasifican inicialmente como:

```text
Recurrente:  frecuencia >= 75%
Periódico:   frecuencia entre 25% y 75%
Ocasional:   frecuencia < 25%
```

---

## Gastos recurrentes

Para los gastos que aparecen prácticamente todos los meses se utiliza principalmente la mediana histórica.

La mediana es menos sensible que el promedio a meses extraordinariamente caros.

También se considera el comportamiento reciente para detectar cambios en los hábitos de gasto.

---

## Gastos periódicos y ocasionales

Para gastos que no ocurren todos los meses se calcula una provisión mensual:

```text
Provisión mensual =
Gasto histórico total / Meses analizados
```

Por ejemplo, un gasto anual de `$12,000` equivale aproximadamente a una provisión de:

```text
$12,000 / 12 = $1,000 al mes
```

Esto permite convertir pagos periódicos en cantidades mensuales que pueden reservarse anticipadamente.

---

## Ahorro e inversión

Las aportaciones a instrumentos de ahorro e inversión se muestran separadas de los gastos de consumo.

La estimación actual utiliza el comportamiento histórico como referencia.

En análisis posteriores puede sustituirse por una meta definida como porcentaje del ingreso mensual.

---

## Efectivo y movimientos no clasificados

Los retiros de efectivo representan dinero que salió de la cuenta, pero no necesariamente permiten saber en qué se gastó.

Por este motivo:

```text
efectivo
otros
```

se muestran como rubros que requieren revisión y no deben interpretarse automáticamente como recomendaciones de gasto.

---

## Gastos extraordinarios

Las operaciones identificadas como extraordinarias se excluyen del presupuesto mensual ordinario.

Por ejemplo:

```text
compra de inmuebles
gastos notariales
enganches
operaciones excepcionales de gran magnitud
```

Estos movimientos siguen formando parte del historial financiero, pero incluirlos en el presupuesto mensual distorsionaría el comportamiento ordinario.

---

# Interpretación del presupuesto

El presupuesto generado debe considerarse un **punto de partida basado en el comportamiento histórico**, no una recomendación financiera definitiva.

El objetivo es utilizar los datos observados para responder preguntas como:

- ¿Cuánto gasto normalmente en alimentación?
- ¿Qué gastos aparecen todos los meses?
- ¿Qué gastos requieren una provisión mensual?
- ¿Cuánto se destina a pagos de TDC?
- ¿Cuánto se destina a ahorro o inversión?
- ¿Qué porcentaje de los egresos todavía no está correctamente clasificado?
- ¿Qué categorías han aumentado recientemente?
- ¿Cuánto dinero debería reservarse mensualmente para gastos periódicos?

Una estructura objetivo puede expresarse como:

```text
Ingreso mensual
=
Gastos ordinarios
+ Pagos financieros
+ Ahorro e inversión
+ Disponible
```

La propuesta de presupuesto puede ajustarse posteriormente según las metas financieras de cada usuario.

---

# Orden recomendado de uso

```text
1. Descargar los estados de cuenta de débito desde BBVA.

2. Colocar los PDF en:
   Estados de cuenta/

3. Verificar que los nombres incluyan mes y año.

4. Opcionalmente inspeccionar un PDF con:
   debug_pdf_text.py

5. Probar extract_bbva_debito.py con un archivo representativo.

6. Ejecutar:
   procesar_estados.py

7. Revisar que se hayan generado movimientos, saldos y resúmenes.

8. Abrir la libreta de análisis.

9. Cargar los archivos consolidados.

10. Validar que cargos, abonos y saldos coincidan.

11. Revisar la clasificación automática.

12. Revisar especialmente:
    - otros
    - efectivo
    - transferencias sin clasificar

13. Analizar la evolución del saldo y el flujo mensual.

14. Revisar y ajustar el presupuesto mensual sugerido.
```

---

# Solución de problemas

## No se puede inferir el año

El nombre del PDF debe incluir un año de cuatro dígitos.

Ejemplo:

```text
Enero 2025.pdf
```

---

## No se extrajeron movimientos

Ejecuta el extractor con:

```powershell
python extract_bbva_debito.py --input "Estados de cuenta/Archivo.pdf" --output "csv_output/Archivo.csv" --debug-tokens
```

También puedes inspeccionar el texto con:

```powershell
python debug_pdf_text.py "Estados de cuenta/Archivo.pdf"
```

---

## Cargos y abonos aparecen intercambiados

El extractor utiliza las coordenadas horizontales de las palabras detectadas mediante:

```python
page.get_text("words")
```

Si BBVA modifica nuevamente la estructura visual de sus estados de cuenta, puede ser necesario ajustar las zonas utilizadas para identificar las columnas de cargos y abonos.

Utiliza el modo de depuración para inspeccionar las coordenadas detectadas.

---

## Los totales no coinciden con BBVA

No continúes con el análisis financiero hasta identificar la causa.

Comprueba:

```text
Cargos extraídos vs. cargos del resumen
Abonos extraídos vs. abonos del resumen
Saldo anterior + abonos - cargos vs. saldo final
```

Esto permite distinguir un problema de extracción de un problema posterior de análisis.

---

## El PDF no contiene texto seleccionable

El extractor utiliza PyMuPDF y espera encontrar texto embebido.

Si el estado de cuenta es una imagen escaneada será necesario implementar OCR.

---

## Muchos movimientos aparecen como `otros`

La clasificación es heurística y se basa en las descripciones disponibles en el estado de cuenta.

Puedes:

- revisar los conceptos de mayor importe;
- agregar palabras clave genéricas;
- ampliar el catálogo de comercios;
- corregir manualmente casos particulares.

Evita crear reglas demasiado específicas para una sola persona si deseas conservar la reutilización del proyecto.

---

# Scripts de tarjeta de crédito

Los siguientes archivos corresponden a pruebas relacionadas con TDC y todavía no forman parte del flujo estable:

```text
extract_bbva_tdc_desglose.py
extract_bbva_tdc_movimientos.py
extract_bbva_tdc_regulares.py
extract_bbva_tdc_resumen.py
procesar_tdc.py
limpiar_tdc.py
```

Pueden conservarse como trabajo en progreso, pero no se recomienda utilizarlos todavía para resultados financieros definitivos.

---

# `.gitignore` recomendado

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

Esto evita subir accidentalmente:

- estados de cuenta;
- archivos CSV generados;
- datos financieros personales;
- archivos temporales;
- entornos virtuales.

---

# Privacidad y advertencias

Este proyecto procesa información financiera personal.

Los estados de cuenta y archivos CSV generados pueden contener:

- nombres;
- números de cuenta;
- referencias bancarias;
- comercios;
- patrones de gasto;
- ingresos;
- saldos;
- otra información financiera sensible.

No subas estos archivos al repositorio.

Antes de utilizar los resultados para decisiones financieras, revisa que:

1. los cargos y abonos coincidan con BBVA;
2. los saldos hayan sido extraídos correctamente;
3. las categorías automáticas tengan sentido;
4. los movimientos extraordinarios estén identificados;
5. los movimientos en `otros` y `efectivo` hayan sido considerados adecuadamente.

El presupuesto generado por la libreta es una estimación basada en datos históricos y debe ajustarse según las circunstancias y objetivos de cada usuario.
