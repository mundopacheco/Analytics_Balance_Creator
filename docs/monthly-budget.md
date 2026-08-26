# Monthly Budget

Analytics Balance Creator utiliza el historial de movimientos clasificados para generar una primera propuesta automática de presupuesto mensual.

El objetivo no es simplemente calcular el promedio de los gastos pasados.

La metodología intenta responder preguntas como:

- ¿Qué gastos ocurren prácticamente todos los meses?
- ¿Cuánto se gasta normalmente cuando aparece una categoría?
- ¿Qué gastos solamente ocurren algunas veces al año?
- ¿Cuánto convendría provisionar mensualmente para esos gastos?
- ¿El comportamiento reciente es diferente del histórico?
- ¿Cuánto dinero se destina a pagos de tarjeta?
- ¿Cuánto se destina a ahorro o inversión?
- ¿Qué egresos todavía requieren revisión?

El resultado debe interpretarse como un **punto de partida basado en el comportamiento histórico**, no como una recomendación financiera definitiva.

---

# Flujo general

El presupuesto se construye después de las etapas de extracción, validación y clasificación:

```text
Estados de cuenta
       │
       ▼
Extracción
       │
       ▼
Validación
       │
       ▼
Clasificación
       │
       ▼
Gasto mensual por categoría
       │
       ▼
Análisis de frecuencia
       │
       ▼
Estimación mensual
       │
       ▼
Presupuesto sugerido
```

Los movimientos extraordinarios y determinadas transferencias se separan antes de calcular el presupuesto ordinario.

---

# Base del presupuesto

Para cada categoría se construye una serie mensual.

Conceptualmente:

```text
Mes       Alimentación
2025-01      $3,100
2025-02      $2,700
2025-03      $3,400
2025-04      $2,900
...
```

También se incluyen meses donde no hubo gasto:

```text
Mes       Seguros
2025-01    $2,000
2025-02        $0
2025-03        $0
2025-04    $2,000
...
```

La presencia de meses en cero es importante para distinguir un gasto mensual de uno periódico.

---

# Meses analizados

El periodo utilizado se obtiene dinámicamente a partir de los datos.

Conceptualmente:

```text
Primer mes disponible
        ↓
Todos los meses intermedios
        ↓
Último mes disponible
```

No se utilizan fechas específicas de una sola persona.

Esto permite que la misma libreta funcione con historiales de diferente longitud.

---

# Frecuencia

Para cada categoría se calcula la proporción de meses en los que existió al menos un gasto.

La frecuencia se define como:

$$
\mathrm{Frecuencia}
=
\frac{
\mathrm{Meses\;con\;gasto}
}{
\mathrm{Meses\;analizados}
}
$$

Por ejemplo, si una categoría aparece en 40 de 46 meses:

```text
40 / 46 = 86.96%
```

su frecuencia aproximada es:

```text
87%
```

---

# Patrones de gasto

A partir de la frecuencia, las categorías se dividen inicialmente en tres patrones.

| Patrón | Frecuencia | Interpretación |
|---|---:|---|
| Recurrente | ≥ 75% | Aparece prácticamente todos los meses |
| Periódico | 25% a < 75% | Aparece regularmente, pero no cada mes |
| Ocasional | < 25% | Aparece solamente en algunos meses |

Los límites son heurísticos y pueden modificarse en versiones futuras.

Su objetivo es permitir que diferentes tipos de gasto reciban tratamientos diferentes.

---

# Gastos recurrentes

Un gasto recurrente aparece prácticamente todos los meses.

Ejemplos posibles:

```text
alimentación
telecomunicaciones
transporte
algunas suscripciones
```

Para estos gastos tiene sentido estudiar cuánto se gasta en un mes habitual.

---

# Mediana mensual

Para los meses donde una categoría tuvo actividad se calcula la mediana.

Por ejemplo:

```text
$2,500
$2,700
$2,800
$3,000
$15,000
```

El promedio se ve afectado por el gasto de `$15,000`.

La mediana, en cambio, continúa representando mejor el comportamiento habitual:

```text
Mediana = $2,800
```

Por esta razón, la mediana se utiliza como una de las principales referencias para gastos recurrentes.

---

# Mes activo

La métrica:

```text
Mediana mensual
```

se calcula utilizando los meses donde la categoría tuvo un gasto mayor que cero.

Por lo tanto, responde:

> Cuando esta categoría aparece, ¿cuánto gasto normalmente?

No responde:

> ¿Cuánto representa esta categoría distribuida entre todos los meses?

Para esa segunda pregunta se utiliza la provisión mensual.

---

# Comportamiento reciente

El historial completo puede no representar correctamente los hábitos actuales.

Por ejemplo, una persona puede haber:

- contratado un nuevo servicio;
- reducido sus gastos;
- aumentado sus compras;
- cambiado de vivienda;
- comenzado a invertir;
- aumentado sus pagos de tarjeta.

Por esta razón se calculan métricas recientes.

Entre ellas:

```text
Promedio últimos 3 meses
Mediana últimos 6 meses
```

---

# Promedio de los últimos 3 meses

La columna:

```text
Promedio 3 meses
```

permite detectar cambios recientes.

Por ejemplo:

```text
Mediana histórica:       $3,000
Promedio últimos 3 meses: $4,200
```

puede indicar que el gasto reciente está por encima del comportamiento histórico.

Actualmente esta métrica funciona principalmente como indicador de tendencia.

No necesariamente determina por sí sola el presupuesto sugerido.

---

# Mediana de los últimos 6 meses

Para gastos recurrentes también puede utilizarse la mediana de los últimos seis meses.

La lógica actual puede comparar:

```text
Mediana histórica
vs.
Mediana últimos 6 meses
```

y utilizar el mayor de ambos valores.

Conceptualmente:

```python
presupuesto = max(
    mediana_historica,
    mediana_ultimos_6_meses
)
```

Esto ayuda a evitar que una categoría cuyo gasto aumentó recientemente quede presupuestada utilizando únicamente valores antiguos.

---

# Gastos periódicos

Un gasto periódico ocurre con cierta regularidad, pero no necesariamente todos los meses.

Ejemplos posibles:

```text
seguros
mantenimiento
salud
educación
reparaciones
```

En estos casos, utilizar directamente el gasto del mes donde ocurre puede producir un presupuesto mensual excesivo.

---

# Provisión mensual

Para gastos periódicos y ocasionales se calcula una provisión.

$$
\mathrm{Provision\;mensual}
=
\frac{
\mathrm{Gasto\;historico\;total\;de\;la\;categoria}
}{
\mathrm{Numero\;total\;de\;meses\;analizados}
}
$$

La provisión responde:

> ¿Cuánto habría sido necesario reservar cada mes para cubrir históricamente este gasto?

---

# Ejemplo de provisión

Supongamos un seguro de:

```text
$12,000
```

pagado una vez al año.

Presupuestar:

```text
$12,000 cada mes
```

no tendría sentido.

En cambio:

$$
12{,}000 / 12 = 1{,}000
$$

permite reservar:

```text
$1,000 al mes
```

para cubrir el pago cuando ocurra.

---

# Gastos ocasionales

Las categorías con frecuencia inferior al 25% se consideran inicialmente ocasionales.

Pueden incluir:

```text
salud
reparaciones
viajes
compras específicas
educación
mantenimiento
```

dependiendo del comportamiento de cada usuario.

Para estos gastos también puede utilizarse la provisión mensual.

Esto permite crear un fondo gradual en lugar de asumir que el gasto ocurrirá todos los meses.

---

# Presupuesto sugerido

La metodología actual utiliza reglas diferentes dependiendo del patrón.

## Recurrente

Para categorías recurrentes se utiliza principalmente:

```text
Mediana histórica
```

comparada con:

```text
Mediana reciente
```

Conceptualmente:

```text
Presupuesto =
máximo(
    mediana histórica,
    mediana últimos 6 meses
)
```

---

## Periódico

Para categorías periódicas se utiliza principalmente:

```text
Provisión mensual
```

---

## Ocasional

Para categorías ocasionales también se utiliza inicialmente:

```text
Provisión mensual
```

Esto convierte gastos irregulares en una cantidad mensual que puede reservarse.

---

# Redondeo

Después de calcular el presupuesto, el valor puede redondearse hacia arriba.

Por ejemplo:

```text
$2,707
```

puede convertirse en:

```text
$2,750
```

El objetivo es producir cantidades más prácticas para utilizar en un presupuesto.

La precisión original permanece disponible en el DataFrame utilizado para los cálculos.

El redondeo se utiliza principalmente para presentación y planificación.

---

# Ejemplo conceptual

Supongamos:

| Categoría | Frecuencia | Mediana activa | Provisión |
|---|---:|---:|---:|
| Alimentación | 93% | $2,707 | $2,530 |
| Seguros | 52% | $2,000 | $1,751 |
| Salud | 15% | $1,200 | $350 |

El algoritmo podría producir:

```text
Alimentación
Patrón: Recurrente
Presupuesto: aproximadamente $2,750
```

```text
Seguros
Patrón: Periódico
Presupuesto: aproximadamente $1,800
```

```text
Salud
Patrón: Ocasional
Presupuesto: aproximadamente $350
```

Las tres categorías utilizan métodos diferentes porque su comportamiento temporal es diferente.

---

# Grupos del presupuesto

Además de la categoría, la tabla puede incluir una columna:

```text
Grupo
```

que distingue la naturaleza del monto.

Los grupos actuales pueden incluir:

```text
Gasto
Salida financiera
Ahorro
Requiere revisión
```

---

# Gastos

El grupo:

```text
Gasto
```

contiene categorías de consumo o compromisos ordinarios identificables.

Ejemplos:

```text
alimentación
vivienda
transporte
salud
educación
seguros
compras
entretenimiento
telecomunicaciones
suscripciones
comisiones
```

---

# Pago de tarjeta de crédito

Los pagos de tarjeta se muestran explícitamente como:

```text
Pago TDC
```

y pertenecen conceptualmente a:

```text
Salida financiera
```

No se asume automáticamente que sean deuda.

---

## ¿Por qué se incluyen?

Mientras los movimientos internos de la tarjeta no formen parte del flujo estable, el estado de cuenta de débito solamente permite observar cuánto dinero salió para pagar la tarjeta.

Por lo tanto:

```text
pago_tdc
```

se conserva dentro de la planificación mensual para mostrar esa salida de efectivo.

---

# Limitación de Pago TDC

El pago de tarjeta no permite saber directamente si el dinero corresponde a:

```text
supermercado
servicios
compras
entretenimiento
deuda revolvente
meses sin intereses
```

Cuando se incorpore el análisis detallado de TDC, será necesario evitar doble conteo.

Por ejemplo:

```text
Compra con TDC
      ↓
Gasto real

Pago posterior de TDC
      ↓
Transferencia financiera
```

---

# Ahorro e inversión

La categoría:

```text
ahorro_inversion
```

se muestra separada del consumo.

Actualmente, la estimación puede utilizar el comportamiento histórico para calcular una provisión mensual.

Sin embargo, esta cantidad no debe interpretarse necesariamente como la meta óptima de ahorro.

---

# Meta de ahorro

En una versión más avanzada, el ahorro puede definirse como porcentaje del ingreso.

Conceptualmente:

```text
Ahorro objetivo =
Ingreso mensual × Porcentaje objetivo
```

Por ejemplo:

```text
Ingreso mensual: $30,000
Meta de ahorro: 15%
```

produciría:

```text
Ahorro objetivo = $4,500
```

independientemente de cuánto se haya ahorrado históricamente.

---

# Efectivo

Los retiros de efectivo se muestran como:

```text
efectivo
```

pero requieren una interpretación especial.

El estado de cuenta permite saber:

> ¿Cuánto efectivo salió de la cuenta?

pero no:

> ¿En qué se gastó posteriormente ese efectivo?

Por esta razón, el monto calculado para efectivo no debe interpretarse automáticamente como una recomendación.

---

# Otros

La categoría:

```text
otros
```

contiene movimientos que no pudieron clasificarse con suficiente confianza.

Un presupuesto elevado en `otros` no significa:

> Se recomienda gastar esta cantidad en otros.

Significa:

> Existe esta cantidad histórica de egresos cuyo destino todavía no está suficientemente identificado.

---

# Requiere revisión

Por esta razón:

```text
efectivo
otros
```

pueden agruparse bajo:

```text
Requiere revisión
```

Estos valores deben mostrarse separadamente del gasto identificado.

---

# Gastos extraordinarios

Los movimientos clasificados como:

```text
gasto_extraordinario
```

no forman parte del presupuesto mensual ordinario.

Ejemplos posibles:

```text
compra de inmueble
gastos notariales
enganches
operaciones patrimoniales excepcionales
```

Estos movimientos permanecen en el historial, pero se utiliza:

```text
incluir_presupuesto = False
```

para evitar que distorsionen la estimación mensual.

---

# Financiamiento

Un préstamo recibido tampoco debe confundirse con ingreso.

Por ejemplo:

```text
PRESTAMO OTORGADO
```

puede producir un abono considerable.

Sin embargo:

```text
financiamiento != ingreso laboral
```

Por ello puede excluirse de la base utilizada para determinar la capacidad ordinaria de gasto.

---

# Tabla de presupuesto

La tabla generada puede incluir:

| Columna | Significado |
|---|---|
| Categoría | Clasificación del egreso |
| Grupo | Naturaleza financiera |
| Patrón | Recurrente, periódico u ocasional |
| Meses con gasto | Número de meses con actividad |
| Frecuencia | Porcentaje de meses con actividad |
| Mediana mensual | Gasto típico cuando ocurre |
| Promedio 3 meses | Comportamiento reciente |
| Provisión mensual | Gasto histórico distribuido |
| Presupuesto sugerido | Primera estimación mensual |

---

# Presentación

La libreta utiliza `pandas.Styler` para presentar la tabla de forma más legible.

Esto permite:

- ocultar el índice;
- mostrar porcentajes;
- mostrar importes como moneda;
- eliminar decimales innecesarios en la presentación;
- destacar grupos mediante color;
- resaltar el presupuesto sugerido.

El formato visual no modifica los valores originales utilizados para los cálculos.

---

# Precisión vs. presentación

El DataFrame puede conservar valores como:

```text
2706.913953
```

mientras que la tabla muestra:

```text
$2,707
```

Esto permite mantener precisión para cálculos posteriores y utilizar una presentación más fácil de leer.

---

# Presupuesto total

La libreta puede calcular diferentes subtotales:

```text
Gastos identificados
Pago TDC
Ahorro / inversión
Rubros por revisar
```

y posteriormente:

```text
Presupuesto mensual total sugerido
```

Sin embargo, debe tenerse cuidado con:

```text
Rubros por revisar
```

porque no representan necesariamente una meta de gasto.

---

# Interpretación del total

Supongamos:

```text
Gastos identificados       $15,000
Pago TDC                     $5,000
Ahorro / inversión           $3,000
Requiere revisión            $8,000
```

No debe interpretarse automáticamente como:

```text
Presupuesto recomendado = $31,000
```

porque los `$8,000` que requieren revisión podrían corresponder parcialmente a gastos ya representados conceptualmente por otras categorías.

La clasificación debe mejorarse antes de utilizar ese total como límite financiero definitivo.

---

# Ingreso mensual

Una evolución natural del modelo consiste en incorporar el ingreso mensual típico.

Esto permitiría evaluar:

```text
Ingreso mensual
-
Gastos ordinarios
-
Pagos financieros
-
Ahorro
=
Disponible
```

El presupuesto dejaría entonces de ser únicamente una extrapolación histórica y comenzaría a representar una distribución explícita del ingreso.

---

# Presupuesto descriptivo vs. presupuesto objetivo

Es importante distinguir dos conceptos.

## Presupuesto descriptivo

Responde:

> Según mi historial, ¿cuánto suelo necesitar para cada categoría?

La implementación actual se aproxima principalmente a este concepto.

---

## Presupuesto objetivo

Responde:

> ¿Cuánto quiero permitirme gastar en cada categoría en el futuro?

Este segundo concepto requiere incorporar decisiones personales.

Por ejemplo:

```text
reducir entretenimiento
aumentar ahorro
disminuir compras
liquidar deuda
crear fondo de emergencia
```

Estas decisiones no pueden inferirse únicamente del historial bancario.

---

# Evolución futura

Una versión más avanzada puede permitir que el usuario defina:

```text
Presupuesto histórico sugerido
Presupuesto objetivo
Diferencia
```

Por ejemplo:

| Categoría | Histórico | Objetivo | Ajuste |
|---|---:|---:|---:|
| Alimentación | $3,500 | $3,000 | -$500 |
| Compras | $2,500 | $1,500 | -$1,000 |
| Ahorro | $2,000 | $4,000 | +$2,000 |

Esto convertiría el análisis histórico en una herramienta activa de planificación.

---

# Limitaciones

El presupuesto depende de la calidad de:

```text
extracción
validación
clasificación
```

Si una cantidad importante permanece en:

```text
otros
efectivo
transferencia_sin_clasificar
```

la estimación debe interpretarse con mayor cautela.

También deben considerarse cambios futuros que el historial no puede predecir, como:

```text
cambio de empleo
mudanza
nuevos créditos
nuevas inversiones
cambios familiares
inflación
cambios de hábitos
```

---

# Principio de interpretación

La metodología sigue este criterio:

> El historial financiero es una referencia para construir el presupuesto, no una obligación de repetir los mismos gastos.

El objetivo final no es predecir exactamente cuánto se gastará, sino proporcionar información suficiente para tomar decisiones más conscientes sobre la distribución mensual del dinero.

---

## Siguiente paso

Si necesitas investigar problemas de extracción, clasificación o análisis, continúa con:

**[Troubleshooting →](troubleshooting.md)**

Para conocer el estado del soporte de tarjeta de crédito, consulta:

**[TDC Development →](tdc-development.md)**