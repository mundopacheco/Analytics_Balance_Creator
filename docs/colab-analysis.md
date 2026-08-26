# Colab Analysis

El repositorio incluye una libreta compatible con **Google Colab** y **Jupyter Notebook** para analizar los datos generados por el extractor.

La libreta comienza después de la etapa de extracción y validación:

```text
Estados de cuenta PDF
        │
        ▼
     Extractor
        │
        ▼
   Validación
        │
        ▼
   Consolidados
        │
        ▼
 Libreta de análisis
```

El objetivo de la libreta es transformar los movimientos bancarios en información útil para comprender:

- la evolución del saldo;
- los ingresos y egresos;
- el flujo mensual;
- los patrones de gasto;
- las categorías de consumo;
- los pagos financieros;
- el ahorro e inversión;
- y una primera propuesta de presupuesto mensual.

---

# Fuentes de datos

El análisis utiliza tres conjuntos principales de información:

```text
Movimientos
Saldos
Resúmenes
```

Cada uno tiene una función diferente.

| Fuente | Uso principal |
|---|---|
| Movimientos | Analizar entradas, salidas y conceptos |
| Saldos | Representar el balance real de la cuenta |
| Resúmenes | Validar movimientos contra BBVA |

Los tres conjuntos son complementarios.

---

# Movimientos

El consolidado de movimientos contiene las operaciones individuales de los estados de cuenta procesados.

Entre las columnas utilizadas se encuentran:

```text
fecha_oper
fecha_liq
descripcion
cargo
abono
pagina
archivo_origen
```

A partir de estos datos se construyen posteriormente:

```text
fecha
monto
descripcion_normalizada
descripcion_base
comercio_base
categoria_presupuesto
tipo_movimiento
```

---

# Saldos

Los saldos reportados directamente por BBVA se utilizan para representar la evolución histórica real de la cuenta.

Esta distinción es importante porque:

```text
flujo acumulado != saldo bancario
```

si el historial disponible no comienza con un saldo de `$0`.

---

# Resúmenes

Los resúmenes contienen información agregada de cada periodo.

Entre los campos utilizados se encuentran:

```text
periodo_inicio
periodo_fin
fecha_corte
saldo_anterior
total_abonos
total_cargos
saldo_final
```

La libreta utiliza esta información para volver a comprobar que los movimientos consolidados reproducen los estados de cuenta originales.

---

# Carga de archivos

La libreta intenta localizar los archivos relevantes dentro del entorno de ejecución.

En Google Colab, los archivos normalmente se encuentran bajo:

```text
/content/
```

La lógica de carga busca evitar rutas específicas de una computadora personal.

Esto permite utilizar la misma libreta con archivos generados por diferentes usuarios.

---

# Normalización de columnas

Después de cargar los CSV, los nombres de las columnas se normalizan.

El proceso puede incluir:

- conversión a minúsculas;
- eliminación de acentos;
- sustitución de espacios;
- eliminación de caracteres especiales;
- conversión a nombres compatibles con pandas.

Por ejemplo:

```text
Fecha Operación
```

puede convertirse en:

```text
fecha_operacion
```

Esto reduce la dependencia de pequeñas variaciones en los encabezados.

---

# Identificación de columnas

La libreta puede buscar diferentes nombres posibles para un mismo concepto.

Por ejemplo, una fecha puede aparecer como:

```text
fecha_oper
fecha_operacion
fecha
```

La lógica intenta identificar la columna disponible en lugar de depender de un único nombre.

Esto hace que el análisis sea más flexible ante cambios menores en los archivos de entrada.

---

# Limpieza de fechas

Las fechas se convierten mediante pandas:

```python
pd.to_datetime(
    serie,
    errors="coerce"
)
```

Los valores que no pueden interpretarse como fechas se convierten en:

```text
NaT
```

y pueden excluirse posteriormente del análisis.

---

# Limpieza de importes

Las columnas monetarias se normalizan antes de realizar cálculos.

El proceso puede eliminar:

```text
$
,
espacios
```

y convertir los valores a números.

Conceptualmente:

```python
cargo = numero(cargo)
abono = numero(abono)
```

Los valores vacíos se interpretan normalmente como:

```text
0
```

---

# Monto neto de un movimiento

La libreta crea una columna:

```text
monto
```

definida como:

```text
monto = abono - cargo
```

Por lo tanto:

```text
abono  -> monto positivo
cargo  -> monto negativo
```

Ejemplo:

```text
Nómina
abono = $20,000
monto = +$20,000
```

mientras que:

```text
Supermercado
cargo = $1,500
monto = -$1,500
```

---

# Fechas futuras

Como medida de limpieza, la libreta puede detectar movimientos cuya fecha sea posterior a la fecha actual.

En lugar de utilizar una fecha fija específica del autor, el límite se obtiene dinámicamente mediante:

```python
pd.Timestamp.today().normalize()
```

Esto permite que la libreta continúe funcionando con nuevos datos sin modificar manualmente una fecha límite.

---

# Outliers

Durante las primeras etapas del análisis se exploró la detección estadística de movimientos atípicos.

Un método utilizado fue el rango intercuartílico:

```text
IQR = Q3 - Q1
```

y un límite como:

```text
Q3 + 3 × IQR
```

Sin embargo, un movimiento grande no necesariamente es un error.

Puede representar:

- un préstamo;
- una inversión;
- una compra extraordinaria;
- una transferencia;
- la compra de un inmueble;
- un gasto notarial;
- un bono;
- una liquidación.

Por esta razón, el análisis posterior prefiere clasificar los movimientos según su **naturaleza financiera** en lugar de eliminarlos únicamente por su magnitud.

---

# Flujo acumulado

Una primera aproximación al análisis puede calcular:

```python
df["saldo"] = (
    df["monto"]
    .cumsum()
)
```

Sin embargo, este valor debe interpretarse correctamente.

Representa:

```text
Flujo acumulado desde el primer movimiento disponible
```

y no necesariamente:

```text
Saldo bancario real
```

---

# ¿Por qué `cumsum()` no representa necesariamente el saldo?

Supongamos que el primer estado de cuenta disponible comienza con:

```text
Saldo inicial = $30,000
```

y los movimientos posteriores producen:

```text
Flujo neto acumulado = -$5,000
```

Entonces:

```text
cumsum() = -$5,000
```

pero el saldo real sería:

```text
$30,000 - $5,000 = $25,000
```

Por esta razón, una gráfica basada únicamente en:

```python
df["monto"].cumsum()
```

puede mostrar valores negativos aunque la cuenta nunca haya tenido ese saldo.

---

# Evolución real del saldo

Para representar correctamente el balance de la cuenta, la libreta utiliza los saldos extraídos directamente de los estados de cuenta.

Conceptualmente:

```text
Fecha de corte      Saldo
2024-01-20          $914
2024-02-20          $2,069
2024-03-20         $50,133
...
```

Estos valores permiten construir una serie histórica del saldo real.

---

# Gráfica de saldo

La gráfica de saldo permite observar:

- acumulación de efectivo;
- disminuciones importantes;
- recuperación del saldo;
- periodos de mayor liquidez;
- efectos de movimientos extraordinarios.

El eje horizontal representa el tiempo y el eje vertical el saldo reportado por BBVA.

Los meses pueden mostrarse explícitamente para facilitar la comparación temporal.

---

# Mes calendario

Para análisis de hábitos y presupuesto, los movimientos se agrupan por mes calendario.

Por ejemplo:

```text
2025-01
2025-02
2025-03
```

Para cada mes se calculan:

```text
ingresos
gastos
movimientos
flujo_neto
```

donde:

```text
flujo_neto = ingresos - gastos
```

---

# Ejemplo de flujo mensual

Conceptualmente:

| Mes | Ingresos | Gastos | Flujo neto |
|---|---:|---:|---:|
| Enero | $30,000 | $28,000 | $2,000 |
| Febrero | $35,000 | $29,000 | $6,000 |
| Marzo | $30,000 | $34,000 | -$4,000 |

Esta tabla responde:

> ¿Entró más dinero del que salió durante el mes?

No responde directamente:

> ¿Cuál era el saldo de la cuenta?

Para esa pregunta se utilizan los saldos.

---

# Periodo bancario

Además del mes calendario, la libreta utiliza los periodos reales de los estados de cuenta.

Por ejemplo:

```text
21/03/2025
a
20/04/2025
```

Esto permite comparar exactamente los movimientos contra los resúmenes de BBVA.

---

# Validación dentro de la libreta

Para cada periodo se calculan nuevamente:

```text
abonos_calculados
cargos_calculados
flujo_calculado
```

y se comparan contra:

```text
abonos_bbva
cargos_bbva
saldo_anterior
saldo_final
```

La comprobación fundamental es:

```text
Saldo final
=
Saldo anterior
+ Abonos calculados
- Cargos calculados
```

La tabla puede incluir una columna:

```text
cuadra
```

cuyo valor esperado es:

```text
True
```

para todos los periodos.

---

# Mes calendario vs. periodo bancario

Ambos análisis son válidos, pero responden preguntas distintas.

| Agrupación | Uso |
|---|---|
| Mes calendario | Presupuesto y hábitos |
| Periodo bancario | Validación contra BBVA |

No deben confundirse.

Por ejemplo, el gasto total de abril calendario puede ser diferente al total del estado de cuenta cuyo corte ocurre en abril.

---

# Exploración de descripciones

Una vez validados los datos, la libreta analiza las descripciones de los movimientos.

Se estudian aspectos como:

```text
apariciones
primera_fecha
ultima_fecha
total_cargos
total_abonos
monto_total
```

Esto permite identificar:

- operaciones recurrentes;
- comercios frecuentes;
- nómina;
- retiros;
- pagos de tarjeta;
- inversiones;
- transferencias;
- conceptos que requieren clasificación.

---

# Normalización de descripciones

Las descripciones bancarias suelen contener ruido.

Por ejemplo:

```text
AMAZON MX MARKETPLACE RFC: XXXXX 20:05
```

y:

```text
STRIPE *AMAZON RFC: XXXXX 06:44
```

pueden corresponder al mismo comercio.

La libreta conserva la descripción original y crea columnas adicionales para análisis.

Conceptualmente:

```text
descripcion_original
        ↓
descripcion_base
        ↓
comercio_base
```

Esto permite limpiar información técnica sin destruir el dato original.

---

# Identificación de comercios

La libreta contiene un catálogo general de comercios y servicios frecuentes.

El objetivo no es depender de los movimientos de una sola persona, sino reconocer patrones reutilizables.

Ejemplos de familias que pueden reconocerse:

```text
supermercados
e-commerce
telecomunicaciones
transporte
restaurantes
farmacias
streaming
seguros
inversiones
```

El catálogo puede ampliarse con el tiempo.

---

# Clasificación financiera

Después de normalizar los movimientos, la libreta intenta distinguir entre:

```text
gasto
ingreso
transferencia
ahorro_inversion
financiamiento
gasto_extraordinario
```

Esta separación es importante porque:

```text
cargo != gasto
```

y:

```text
abono != ingreso
```

en todos los casos.

---

# Ejemplo

Una transferencia hacia una cuenta propia puede aparecer como:

```text
cargo = $10,000
```

pero no necesariamente representa consumo.

De manera similar:

```text
PRESTAMO OTORGADO
abono = $1,750,000
```

representa una entrada de dinero, pero financieramente corresponde a:

```text
financiamiento
```

y no a ingreso laboral.

---

# Gastos extraordinarios

Algunos movimientos pueden ser correctos y reales, pero poco representativos de un presupuesto mensual ordinario.

Ejemplos:

```text
compra de inmueble
gastos notariales
enganches
operaciones excepcionales
```

Estos movimientos se conservan en el historial, pero pueden marcarse como:

```text
es_extraordinario = True
```

y excluirse de ciertas estimaciones de presupuesto.

---

# Preparación para el presupuesto

Después de limpiar y clasificar los movimientos, la libreta puede construir una estructura mensual por categorías.

Ejemplos:

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
pago_tdc
ahorro_inversion
efectivo
otros
```

Estas categorías permiten transformar miles de movimientos individuales en una vista mensual más fácil de interpretar.

---

# Efectivo y `otros`

Dos categorías requieren especial atención.

## Efectivo

Un retiro significa que el dinero salió de la cuenta, pero no permite conocer necesariamente su destino final.

Por ejemplo:

```text
RETIRO SIN TARJETA
```

puede terminar utilizándose en:

- comida;
- transporte;
- compras;
- entretenimiento;
- otros gastos.

El estado de cuenta de débito no contiene esa información.

---

## Otros

La categoría:

```text
otros
```

contiene movimientos que no pudieron clasificarse automáticamente con suficiente confianza.

Un porcentaje elevado en esta categoría indica que conviene:

- revisar los movimientos de mayor importe;
- ampliar reglas generales;
- mejorar el catálogo de comercios;
- realizar clasificación manual cuando sea necesario.

---

# Principio del análisis

La libreta intenta mantener separadas tres etapas:

```text
Datos observados
       ↓
Clasificación
       ↓
Interpretación financiera
```

Esto evita modificar los movimientos originales para hacerlos coincidir con una expectativa.

Los datos originales permanecen disponibles y las categorías se agregan como información derivada.

---

# Reutilización

La libreta intenta evitar variables específicas de una sola persona.

Por ejemplo, no deberían hardcodearse:

```text
fechas personales
nombres de personas
montos específicos
fechas límite fijas
categorías personales
```

Las reglas generales pueden incluir comercios o instituciones conocidas, pero deben estar diseñadas para funcionar con diferentes usuarios.

---

# Flujo completo de la libreta

Conceptualmente:

```text
Consolidados
     │
     ▼
Carga
     │
     ▼
Limpieza
     │
     ▼
Validación
     │
     ├────────► Saldo real
     │
     ├────────► Flujo mensual
     │
     ▼
Normalización de descripciones
     │
     ▼
Identificación de comercios
     │
     ▼
Clasificación financiera
     │
     ▼
Clasificación de egresos
     │
     ▼
Presupuesto mensual
```

---

# Qué no intenta hacer la libreta

Actualmente, la libreta no pretende:

- realizar contabilidad formal;
- preparar declaraciones fiscales;
- sustituir asesoría financiera;
- inferir con certeza el propósito de todas las transferencias;
- determinar automáticamente todas las metas personales de ahorro;
- analizar de forma estable los movimientos internos de TDC.

Su objetivo es proporcionar una base verificable para comprender el comportamiento financiero histórico y construir un presupuesto informado.

---

## Siguiente paso

Después de comprender el flujo general del análisis, continúa con:

**[Transaction Classification →](transaction-classification.md)**

para conocer cómo se normalizan las descripciones y cómo se asignan categorías financieras a los movimientos.