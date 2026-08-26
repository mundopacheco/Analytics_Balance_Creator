# Validation

La validación es una parte fundamental de Analytics Balance Creator.

El hecho de que un extractor genere un archivo CSV sin errores no garantiza que los datos sean correctos.

Un movimiento puede:

- faltar;
- duplicarse;
- tener un importe incorrecto;
- clasificarse como cargo cuando era abono;
- clasificarse como abono cuando era cargo;
- asociarse al periodo incorrecto.

Por esta razón, el proyecto utiliza la información de resumen reportada directamente por BBVA para comprobar independientemente los movimientos extraídos.

---

# Principio de validación

Para cada estado de cuenta se comparan dos fuentes de información:

```text
Movimientos extraídos
        │
        ▼
Suma de cargos y abonos
```

contra:

```text
Resumen reportado por BBVA
        │
        ▼
Total de cargos y abonos
```

Además, se comprueba que el cambio de saldo sea consistente.

Conceptualmente:

```text
Movimientos ──────┐
                  │
                  ├──► Validación
                  │
Resumen BBVA ─────┘
```

El objetivo es que ambas fuentes describan exactamente el mismo periodo financiero.

---

# Ecuación fundamental

Para una cuenta de débito debe cumplirse:

```text
Saldo final = Saldo anterior + Abonos - Cargos
```

Por ejemplo:

```text
Saldo anterior    $10,000
Abonos            $25,000
Cargos            $22,000
                  -------
Saldo final       $13,000
```

porque:

```text
$10,000 + $25,000 - $22,000 = $13,000
```

Esta relación permite comprobar que el resumen del estado de cuenta sea internamente consistente.

---

# Validación de movimientos

La segunda comprobación consiste en sumar los movimientos individuales extraídos.

Para cada periodo:

```text
Abonos calculados =
suma de la columna abono
```

y:

```text
Cargos calculados =
suma de la columna cargo
```

Estos valores deben coincidir con:

```text
total_abonos
total_cargos
```

reportados por BBVA.

Por lo tanto:

```text
Abonos calculados = Abonos BBVA
Cargos calculados = Cargos BBVA
```

---

# Validación completa

Un periodo puede considerarse correctamente reconstruido cuando se cumplen simultáneamente:

```text
Abonos calculados = Abonos BBVA
```

```text
Cargos calculados = Cargos BBVA
```

```text
Saldo anterior + Abonos calculados - Cargos calculados
=
Saldo final
```

Estas comprobaciones permiten detectar diferentes tipos de errores.

---

# ¿Qué puede detectar la validación?

## Movimiento faltante

Supongamos que BBVA reporta:

```text
Cargos: $20,000
```

pero el extractor obtiene:

```text
Cargos: $18,500
```

La diferencia:

```text
$1,500
```

indica que probablemente falta uno o varios movimientos.

---

## Movimiento duplicado

Si BBVA reporta:

```text
Cargos: $20,000
```

pero el extractor obtiene:

```text
Cargos: $21,200
```

puede existir:

- un movimiento duplicado;
- un importe asociado a dos registros;
- una línea interpretada incorrectamente como una nueva operación.

---

## Cargo interpretado como abono

Este problema puede producir simultáneamente:

```text
Cargos calculados < Cargos BBVA
```

y:

```text
Abonos calculados > Abonos BBVA
```

Este tipo de error fue una de las razones para utilizar las coordenadas horizontales obtenidas mediante:

```python
page.get_text("words")
```

en lugar de depender únicamente del orden del texto extraído.

Consulta [Debit Extractor](debit-extractor.md) para conocer esta lógica.

---

## Fecha incorrecta

Un movimiento puede estar correctamente extraído pero asignado al periodo equivocado.

Esto puede ocurrir especialmente alrededor de:

```text
diciembre / enero
```

o cuando el estado de cuenta contiene movimientos correspondientes a dos meses calendario.

La validación debe realizarse utilizando el **periodo real del estado de cuenta**, no solamente el mes calendario.

---

# Periodo bancario vs. mes calendario

Para análisis de presupuesto puede ser útil agrupar movimientos por:

```text
2025-01
2025-02
2025-03
```

Sin embargo, esta agrupación no debe utilizarse para validar el estado de cuenta si el periodo bancario no coincide exactamente con el mes calendario.

Por ejemplo, un estado de cuenta puede corresponder a:

```text
21 de marzo
a
20 de abril
```

mientras que el mes calendario de abril corresponde a:

```text
1 de abril
a
30 de abril
```

Son conjuntos de movimientos diferentes.

---

# Campos utilizados para validar periodos

Los archivos de resumen contienen información similar a:

```text
periodo_inicio
periodo_fin
fecha_corte
saldo_anterior
total_abonos
total_cargos
saldo_final
```

Los movimientos se filtran utilizando:

```text
periodo_inicio <= fecha_oper <= periodo_fin
```

y después se calculan los totales correspondientes.

---

# Ejemplo de validación con pandas

Conceptualmente, la validación puede realizarse de la siguiente manera:

```python
movimientos_periodo = df_movimientos.loc[
    (df_movimientos["fecha_oper"] >= inicio)
    &
    (df_movimientos["fecha_oper"] <= fin)
]

cargos_calculados = (
    movimientos_periodo["cargo"]
    .fillna(0)
    .sum()
)

abonos_calculados = (
    movimientos_periodo["abono"]
    .fillna(0)
    .sum()
)
```

Posteriormente:

```python
diferencia_cargos = (
    cargos_calculados
    - cargos_bbva
)

diferencia_abonos = (
    abonos_calculados
    - abonos_bbva
)
```

y:

```python
flujo_calculado = (
    abonos_calculados
    - cargos_calculados
)

cambio_saldo = (
    saldo_final
    - saldo_anterior
)

diferencia_flujo = (
    flujo_calculado
    - cambio_saldo
)
```

---

# Tolerancia numérica

Los cálculos realizados con números de punto flotante pueden producir diferencias extremadamente pequeñas.

Por ejemplo:

```text
9.094947e-13
```

```text
-3.637979e-12
```

```text
1.455192e-11
```

Estas diferencias son consecuencia de la representación binaria de números decimales en las computadoras.

No representan una diferencia monetaria real.

---

## Ejemplo

Un resultado como:

```text
0.000000000003637
```

pesos es efectivamente:

```text
$0.00
```

para efectos financieros.

Por esta razón, la validación utiliza una tolerancia.

Por ejemplo:

```python
TOLERANCIA = 0.02
```

y:

```python
cuadra = (
    abs(diferencia_abonos) <= TOLERANCIA
    and
    abs(diferencia_cargos) <= TOLERANCIA
    and
    abs(diferencia_flujo) <= TOLERANCIA
)
```

Esto permite aceptar diferencias inferiores a unos cuantos centavos provocadas por representación numérica.

---

# Resultado esperado

Una tabla de validación puede contener columnas como:

```text
fecha_corte
saldo_anterior
abonos_bbva
abonos_calculados
cargos_bbva
cargos_calculados
flujo_calculado
saldo_final
dif_abonos
dif_cargos
dif_flujo
cuadra
```

El resultado deseado es:

```text
cuadra = True
```

para todos los periodos.

---

# Interpretación de `cuadra`

## `True`

Significa que:

- los cargos extraídos coinciden con BBVA;
- los abonos extraídos coinciden con BBVA;
- el flujo reproduce correctamente el cambio de saldo;
- las diferencias se encuentran dentro de la tolerancia establecida.

Esto proporciona una base razonable para utilizar el periodo en análisis posteriores.

---

## `False`

No debe ignorarse automáticamente.

Un resultado `False` puede indicar:

- movimiento faltante;
- movimiento duplicado;
- importe incorrecto;
- cargo/abono invertido;
- fecha incorrecta;
- periodo incorrectamente reconstruido;
- resumen extraído incorrectamente;
- cambio en el formato del PDF.

Se recomienda investigar la causa antes de utilizar ese periodo en análisis financieros.

---

# Cómo investigar una diferencia

Cuando un periodo no cuadra, comienza comparando:

```text
Cargos BBVA
vs.
Cargos calculados
```

y:

```text
Abonos BBVA
vs.
Abonos calculados
```

Esto permite determinar rápidamente qué tipo de movimiento buscar.

---

## Si solamente difieren los cargos

Busca:

- compras faltantes;
- retiros;
- transferencias enviadas;
- comisiones;
- movimientos clasificados accidentalmente como abono.

---

## Si solamente difieren los abonos

Busca:

- depósitos faltantes;
- nómina;
- transferencias recibidas;
- devoluciones;
- movimientos clasificados accidentalmente como cargo.

---

## Si ambos totales coinciden pero el saldo no

Revisa:

- `saldo_anterior`;
- `saldo_final`;
- periodo del estado de cuenta;
- extracción del resumen.

En este caso el problema probablemente no se encuentra en los movimientos individuales.

---

# Herramientas de depuración

## Inspeccionar texto

Ejecuta:

```bash
python debug_pdf_text.py "Estados de cuenta/Archivo.pdf"
```

Esto permite observar el texto recuperado mediante PyMuPDF.

---

## Inspeccionar tokens y coordenadas

Ejecuta:

```bash
python extract_bbva_debito.py --input "Estados de cuenta/Archivo.pdf" --output "csv_output/Archivo.csv" --debug-tokens
```

Esto es especialmente útil cuando el problema está relacionado con:

```text
CARGOS
ABONOS
```

porque el extractor utiliza la posición horizontal de los importes para identificar la columna correspondiente.

---

# Validación visual

Aunque la validación automática es muy útil, durante el desarrollo del extractor también es recomendable realizar comprobaciones manuales.

Por ejemplo:

1. seleccionar un estado de cuenta;
2. identificar algunos movimientos visibles;
3. localizar esos movimientos en el CSV;
4. comprobar fecha;
5. comprobar descripción;
6. comprobar importe;
7. comprobar si fue clasificado como cargo o abono.

Esta revisión es especialmente importante cuando se agrega soporte para una nueva versión del formato PDF.

---

# Validación histórica

Cuando se procesan varios años de estados de cuenta, una validación exitosa periodo por periodo proporciona una señal mucho más fuerte que comprobar únicamente algunos movimientos.

Conceptualmente:

```text
Periodo 1  ──► True
Periodo 2  ──► True
Periodo 3  ──► True
...
Periodo N  ──► True
```

Si todos los periodos reproducen los totales y saldos reportados por BBVA, es mucho menos probable que exista un error sistemático importante en la extracción.

---

# Validación antes de modificar el extractor

Cuando se realiza un cambio en:

```text
extract_bbva_debito.py
```

se recomienda volver a ejecutar el procesamiento sobre el historial disponible.

Esto ayuda a detectar regresiones.

Un cambio puede corregir una versión del PDF y accidentalmente romper otra.

Por esta razón, un historial con diferentes versiones de estados de cuenta funciona también como un conjunto práctico de pruebas de regresión.

---

# Validación antes del análisis

La libreta de análisis asume que los movimientos representan correctamente los estados de cuenta.

Por lo tanto, el orden recomendado es:

```text
Extracción
    ↓
Validación
    ↓
Análisis
    ↓
Clasificación
    ↓
Presupuesto
```

y no:

```text
Extracción
    ↓
Presupuesto
    ↓
Descubrir posteriormente que faltaban movimientos
```

---

# Saldo real vs. flujo acumulado

La validación también ayuda a distinguir dos conceptos diferentes.

## Flujo acumulado

Si calculamos:

```python
df["monto"] = (
    df["abono"]
    - df["cargo"]
)

df["saldo_acumulado"] = (
    df["monto"]
    .cumsum()
)
```

el resultado representa el flujo acumulado desde el primer movimiento disponible.

No necesariamente representa el saldo bancario real.

---

## Saldo reportado por BBVA

El saldo real utiliza:

```text
saldo_anterior
```

como punto de partida.

Por eso:

```text
Saldo real
=
Saldo inicial real
+
Flujo acumulado
```

Los archivos de saldos permiten utilizar directamente los valores reportados por el banco en lugar de asumir que el historial comienza en `$0`.

---

# Criterio de confiabilidad

Dentro del proyecto se utiliza el siguiente principio:

> Los datos no se consideran confiables solamente porque pudieron extraerse; deben ser verificables contra la información reportada por el banco.

Esto permite separar claramente:

```text
Extracción técnica
```

de:

```text
Validación financiera
```

y proporciona una base más sólida para los análisis posteriores.

---

## Siguiente paso

Una vez validada la extracción, continúa con:

**[Colab Analysis →](colab-analysis.md)**

para utilizar los consolidados en el análisis histórico, las gráficas y las etapas posteriores de clasificación y presupuesto.