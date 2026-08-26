# Output Files

Analytics Balance Creator genera diferentes archivos CSV a partir de los estados de cuenta procesados.

Los archivos no contienen todos el mismo tipo de información. El proyecto separa los datos en tres conjuntos principales:

1. **Movimientos**
2. **Saldos**
3. **Resúmenes**

Esta separación permite utilizar los movimientos para análisis detallado y, al mismo tiempo, conservar información independiente del estado de cuenta para validar la extracción.

---

# Estructura de salida

Los archivos generados se organizan bajo:

```text
csv_output/
├── consolidados/
├── saldos/
└── resumenes/
```

Además, durante el procesamiento pueden generarse CSV individuales correspondientes a cada estado de cuenta.

Conceptualmente:

```text
Estados de cuenta PDF
        │
        ▼
     Extractor
        │
        ├──────────────► Movimientos individuales
        │
        ├──────────────► Saldos
        │
        └──────────────► Resúmenes
                              │
                              ▼
                        Consolidados
```

---

# Movimientos

Los archivos de movimientos contienen las operaciones individuales detectadas dentro de cada estado de cuenta.

Los campos principales son:

```text
fecha_oper
fecha_liq
descripcion
cargo
abono
pagina
```

Durante la consolidación también puede agregarse información sobre el archivo de origen.

Por ejemplo:

```text
archivo_origen
```

---

## Ejemplo

```text
fecha_oper|fecha_liq|descripcion|cargo|abono|pagina|archivo_origen
2025-01-03|2025-01-03|PAGO DE NOMINA||17821.00|2|Enero 2025
2025-01-05|2025-01-06|COMPRA COMERCIO|350.00||3|Enero 2025
```

Los archivos utilizan:

```text
|
```

como separador.

---

# Significado de las columnas de movimientos

## `fecha_oper`

Fecha en la que se realizó la operación.

Ejemplo:

```text
2025-01-05
```

---

## `fecha_liq`

Fecha de liquidación reportada por BBVA.

Puede ser diferente de `fecha_oper`.

Por ejemplo, una compra realizada durante un fin de semana puede liquidarse posteriormente.

---

## `descripcion`

Descripción extraída del estado de cuenta.

Puede incluir información como:

```text
nombre del comercio
referencias
RFC
autorizaciones
conceptos de transferencia
```

El extractor intenta conservar suficiente información para permitir posteriormente la clasificación del movimiento.

La libreta de análisis crea versiones normalizadas de esta descripción sin modificar el valor original.

---

## `cargo`

Importe que salió de la cuenta.

Ejemplo:

```text
350.00
```

Un cargo representa una salida desde la perspectiva de la cuenta bancaria.

---

## `abono`

Importe que entró a la cuenta.

Ejemplo:

```text
17821.00
```

Un abono representa una entrada desde la perspectiva de la cuenta bancaria.

---

## `pagina`

Página del PDF donde fue detectado el movimiento.

Este campo es útil para:

- depuración;
- validación manual;
- localizar rápidamente una operación dentro del documento original.

---

## `archivo_origen`

Identifica el estado de cuenta del cual provino el movimiento.

Por ejemplo:

```text
Enero 2025
```

Este campo resulta especialmente útil después de consolidar múltiples estados de cuenta.

---

# Cargo y abono no equivalen necesariamente a gasto e ingreso

Es importante distinguir la dirección bancaria del movimiento de su significado financiero.

Desde la perspectiva de la cuenta:

```text
cargo = dinero que sale
abono = dinero que entra
```

Pero esto no significa necesariamente:

```text
cargo = gasto
abono = ingreso
```

Por ejemplo:

```text
Transferencia hacia una cuenta propia
```

es un cargo, pero puede no representar consumo.

De manera similar:

```text
Préstamo recibido
```

es un abono, pero no representa ingreso laboral ni aumento permanente del patrimonio.

Esta distinción se realiza posteriormente durante la etapa de clasificación.

Consulta [Transaction Classification](transaction-classification.md).

---

# CSV individuales

Durante el procesamiento puede generarse un archivo de movimientos por cada estado de cuenta.

Por ejemplo:

```text
csv_output/
├── Enero 2025.csv
├── Febrero 2025.csv
├── Marzo 2025.csv
└── ...
```

Estos archivos son útiles para:

- validar un PDF individual;
- comparar movimientos contra el documento original;
- investigar problemas de extracción;
- comprobar periodos específicos antes de consolidarlos.

No se recomienda utilizar únicamente estos archivos para análisis históricos de varios años.

Para ello se generan los consolidados.

---

# Consolidados

Los archivos históricos consolidados se almacenan en:

```text
csv_output/consolidados/
```

Su objetivo es combinar los resultados individuales en conjuntos de datos que puedan utilizarse directamente para análisis.

El consolidado de movimientos contiene las operaciones de todos los estados de cuenta procesados.

Conceptualmente:

```text
Enero 2025.csv
       +
Febrero 2025.csv
       +
Marzo 2025.csv
       +
      ...
       │
       ▼
movimientos_debito_total.csv
```

El nombre exacto puede depender de la versión actual de los scripts, pero su función es mantener un historial único de movimientos.

---

# Saldos

Los archivos relacionados con saldos se almacenan en:

```text
csv_output/saldos/
```

y sus versiones consolidadas pueden utilizarse posteriormente desde:

```text
csv_output/consolidados/
```

Los saldos representan valores reportados directamente por BBVA.

Esto es diferente de calcular:

```text
abonos - cargos
```

a partir de los movimientos.

---

## ¿Por qué extraer los saldos?

Supongamos que el primer estado de cuenta disponible comienza con:

```text
Saldo inicial: $25,000
```

y durante el periodo ocurre:

```text
Abonos: $20,000
Cargos: $18,000
```

El flujo neto es:

```text
$20,000 - $18,000 = $2,000
```

pero el saldo final real sería:

```text
$25,000 + $2,000 = $27,000
```

Si solamente acumuláramos movimientos desde cero, obtendríamos:

```text
$2,000
```

en lugar de:

```text
$27,000
```

Por esta razón, los saldos reportados por el banco son la fuente adecuada para representar la evolución histórica real de la cuenta.

---

# Resúmenes

Los archivos de resumen se almacenan en:

```text
csv_output/resumenes/
```

Los resúmenes contienen información agregada del periodo reportada por BBVA.

Los campos utilizados pueden incluir:

```text
periodo_inicio
periodo_fin
fecha_corte
saldo_anterior
total_abonos
total_cargos
saldo_final
```

La estructura exacta puede variar dependiendo de la versión del estado de cuenta y del extractor.

---

# Función de los resúmenes

Los resúmenes permiten comprobar independientemente que los movimientos extraídos sean correctos.

Por ejemplo, si el estado de cuenta reporta:

```text
Saldo anterior: $10,000
Abonos:         $25,000
Cargos:         $22,000
Saldo final:    $13,000
```

debe cumplirse:

```text
$10,000 + $25,000 - $22,000 = $13,000
```

Además, la suma de los movimientos extraídos debería reproducir:

```text
Abonos extraídos = $25,000
Cargos extraídos = $22,000
```

Esto convierte al resumen en una fuente de control independiente.

---

# Relación entre los tres conjuntos

Los tres conjuntos de datos responden preguntas distintas.

| Fuente | Pregunta principal |
|---|---|
| Movimientos | ¿Qué ocurrió? |
| Saldos | ¿Cuánto dinero había? |
| Resúmenes | ¿La extracción coincide con BBVA? |

No se recomienda sustituir uno por otro.

---

## Movimientos

Son adecuados para:

- analizar gastos;
- analizar ingresos;
- clasificar operaciones;
- detectar recurrencias;
- estudiar comercios;
- calcular flujo.

---

## Saldos

Son adecuados para:

- visualizar el balance histórico;
- conocer el saldo real al cierre;
- comparar periodos;
- validar reconstrucciones del flujo.

---

## Resúmenes

Son adecuados para:

- comprobar cargos;
- comprobar abonos;
- validar cambios de saldo;
- detectar errores del extractor.

---

# Flujo neto

A partir de los movimientos puede calcularse:

```text
Flujo neto = Abonos - Cargos
```

Por ejemplo:

```text
Abonos = $30,000
Cargos = $27,000
```

entonces:

```text
Flujo neto = $3,000
```

Esto significa que durante el periodo entraron `$3,000` más de los que salieron.

Sin embargo:

> **El flujo neto no es el saldo de la cuenta.**

Para obtener el saldo es necesario conocer también el saldo inicial:

```text
Saldo final = Saldo anterior + Flujo neto
```

Esta diferencia es fundamental para interpretar correctamente las gráficas generadas posteriormente.

---

# Periodos bancarios y meses calendario

Los estados de cuenta no necesariamente comienzan el primer día del mes ni terminan el último.

Por este motivo existen dos formas diferentes de analizar los movimientos:

### Mes calendario

Agrupa por:

```text
enero
febrero
marzo
...
```

Es útil para:

- presupuestos;
- ingresos mensuales;
- gastos mensuales;
- comparaciones de hábitos.

### Periodo del estado de cuenta

Utiliza las fechas reales reportadas por BBVA.

Es útil para:

- validar cargos;
- validar abonos;
- reproducir cambios de saldo;
- comparar contra el resumen bancario.

La libreta utiliza ambas perspectivas dependiendo del objetivo del análisis.

---

# Formato CSV

Los archivos generados utilizan generalmente:

```text
|
```

como delimitador.

En pandas pueden cargarse mediante:

```python
import pandas as pd

df = pd.read_csv(
    "archivo.csv",
    sep="|",
    encoding="utf-8-sig"
)
```

El uso de `utf-8-sig` ayuda a manejar correctamente archivos que puedan contener una marca BOM.

---

# Precisión monetaria

Los archivos CSV conservan los valores numéricos necesarios para realizar cálculos posteriores.

Durante el análisis pueden aparecer pequeñas diferencias de punto flotante como:

```text
9.094947e-13
```

Estas diferencias no representan centavos reales y pueden considerarse equivalentes a:

```text
$0.00
```

cuando se encuentran muy por debajo de la precisión monetaria.

La validación debe realizarse utilizando una tolerancia apropiada.

---

# Archivos generados y Git

Los archivos financieros generados no deben subirse al repositorio.

El `.gitignore` debe incluir:

```gitignore
Estados de cuenta/
csv_output/
csv_output_tdc/
```

Antes de realizar un commit, comprueba:

```bash
git status
```

y verifica que no aparezcan:

- PDF de estados de cuenta;
- CSV individuales;
- consolidados;
- saldos;
- resúmenes.

---

# Privacidad

Los archivos generados pueden contener información sensible como:

- nombres;
- referencias bancarias;
- descripciones de transferencias;
- comercios;
- ingresos;
- gastos;
- saldos;
- números de cuenta;
- patrones financieros.

Trátalos como información privada.

La exclusión mediante `.gitignore` ayuda a prevenir cargas accidentales, pero no sustituye una revisión de:

```bash
git status
```

antes de realizar cada commit.

---

# Flujo hacia el análisis

Una vez generados los consolidados, el flujo continúa conceptualmente así:

```text
Movimientos consolidados ──┐
                           │
Saldos consolidados ───────┼──► Libreta de análisis
                           │
Resúmenes consolidados ────┘
                                  │
                                  ├──► Validación
                                  ├──► Gráficas
                                  ├──► Clasificación
                                  └──► Presupuesto
```

Los tres conjuntos son complementarios y permiten que el análisis no dependa únicamente de una suma acumulada de movimientos.

---

## Siguiente paso

Después de generar los archivos, continúa con:

**[Validation →](validation.md)**

para comprobar que los movimientos, cargos, abonos y saldos coincidan con los valores reportados por BBVA.