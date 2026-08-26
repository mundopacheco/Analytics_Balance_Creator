# TDC Development

El soporte para estados de cuenta de **tarjeta de crédito (TDC)** se encuentra actualmente en desarrollo.

Los scripts relacionados con TDC forman parte del repositorio para facilitar su evolución y experimentación, pero **no deben considerarse parte del flujo estable de Analytics Balance Creator**.

Actualmente, el flujo validado corresponde a estados de cuenta de **débito BBVA**.

---

# Estado actual

El proyecto distingue actualmente entre:

| Componente | Estado |
|---|---|
| Extracción de débito | Estable |
| Extracción de saldos de débito | Estable |
| Extracción de resúmenes de débito | Estable |
| Validación de débito | Estable |
| Consolidación de débito | Estable |
| Libreta de análisis | Funcional |
| Clasificación de movimientos | Funcional / en evolución |
| Presupuesto mensual | Funcional / en evolución |
| Extracción de TDC | En desarrollo |
| Consolidación de TDC | En desarrollo |
| Integración débito + TDC | Pendiente |

La clasificación y el presupuesto continúan evolucionando porque dependen de reglas heurísticas, aunque utilizan datos de débito previamente validados.

---

# Scripts relacionados con TDC

El repositorio puede contener archivos como:

```text
extract_bbva_tdc_desglose.py
extract_bbva_tdc_movimientos.py
extract_bbva_tdc_regulares.py
extract_bbva_tdc_resumen.py
procesar_tdc.py
limpiar_tdc.py
```

Estos archivos corresponden a diferentes experimentos realizados para interpretar estados de cuenta de tarjeta de crédito.

No existe todavía garantía de que funcionen correctamente con todos los periodos o versiones de PDF.

---

# Diferentes versiones del estado de cuenta

Al igual que ocurre con los estados de cuenta de débito, BBVA ha modificado la estructura de los estados de cuenta de TDC a lo largo del tiempo.

Dependiendo del periodo pueden existir diferencias en:

```text
encabezados
posición de tablas
estructura del resumen
nombres de campos
paginación
descripción de movimientos
formato de fechas
saldo al corte
saldo deudor total
```

Por esta razón, un extractor que funciona con un PDF no necesariamente funciona con todo el historial.

---

# Objetivo futuro

El objetivo del soporte de TDC es obtener información suficiente para analizar las compras realizadas con tarjeta sin duplicar los egresos observados en la cuenta de débito.

Conceptualmente:

```text
Tarjeta de crédito
        │
        ├──► Compras
        ├──► Servicios
        ├──► MSI
        ├──► Intereses
        ├──► Comisiones
        └──► Otros cargos
```

y posteriormente relacionar esa información con:

```text
Cuenta de débito
        │
        └──► Pago TDC
```

---

# Problema del doble conteo

Actualmente, el análisis de débito puede identificar:

```text
PAGO TARJETA DE CREDITO
```

como:

```text
categoria_presupuesto = pago_tdc
```

Esto permite observar cuánto dinero salió de la cuenta de débito para pagar una tarjeta.

Sin embargo, cuando se incorporen los movimientos internos de TDC, será necesario cambiar la interpretación.

---

## Ejemplo

Supongamos una compra con tarjeta:

```text
Supermercado con TDC
$2,000
```

El movimiento real de consumo debería clasificarse como:

```text
alimentacion = $2,000
```

Posteriormente, la cuenta de débito puede mostrar:

```text
PAGO TARJETA DE CREDITO
$2,000
```

Si ambos movimientos se contabilizaran como gasto:

```text
Gasto calculado = $4,000
```

aunque el consumo real fue:

```text
$2,000
```

---

# Tratamiento futuro de Pago TDC

Cuando los movimientos de tarjeta estén disponibles y validados, el pago desde débito debería tratarse principalmente como una transferencia financiera:

```text
Cuenta de débito
      │
      ▼
Tarjeta de crédito
```

mientras que el gasto real se atribuiría a las compras realizadas con la tarjeta.

Conceptualmente:

```text
Compra con TDC
      ↓
Categoría de consumo
```

y:

```text
Pago de TDC
      ↓
Transferencia / liquidación
```

Esto permitirá construir un presupuesto basado en el destino real del dinero.

---

# Servicios domiciliados

No se debe asumir que:

```text
Pago TDC = deuda
```

Una tarjeta puede utilizarse para:

- servicios domiciliados;
- supermercado;
- transporte;
- compras en línea;
- entretenimiento;
- meses sin intereses;
- financiamiento;
- deuda revolvente.

Por esta razón, mientras no exista el detalle estable de la tarjeta, la categoría:

```text
pago_tdc
```

se conserva explícitamente.

---

# Información que interesa extraer

Una implementación estable de TDC debería permitir obtener, cuando el estado de cuenta lo proporcione:

```text
fecha de corte
periodo
saldo al corte
saldo deudor total
pago para no generar intereses
pago mínimo
límite de crédito
crédito disponible
movimientos
compras regulares
compras a meses
intereses
comisiones
pagos
abonos
```

No todos estos campos necesariamente estarán disponibles con la misma estructura en todas las versiones del PDF.

---

# Saldo de la tarjeta

Durante el desarrollo se han observado diferentes nombres para representar el balance de la tarjeta.

Por ejemplo:

```text
SALDO AL CORTE
```

y en otras versiones:

```text
SALDO DEUDOR TOTAL
```

Una implementación estable debe detectar correctamente la versión del documento antes de interpretar estos valores.

---

# Fecha de corte

En los estados de cuenta analizados, la fecha de corte puede reconstruirse utilizando:

- información explícita del PDF;
- el periodo reportado;
- el nombre del archivo.

Cuando el día de corte es conocido y consistente, el nombre:

```text
Abril 2025.pdf
```

puede proporcionar el mes y año necesarios para completar la fecha.

Sin embargo, una implementación general no debería depender innecesariamente de supuestos que puedan variar entre usuarios o productos.

---

# Extracción de movimientos TDC

La extracción de movimientos de tarjeta presenta desafíos adicionales.

Un estado de cuenta puede separar:

```text
compras regulares
compras a meses
promociones
intereses
comisiones
pagos
disposiciones
```

y una misma operación puede ocupar múltiples líneas dentro del PDF.

Por esta razón, la extracción debe validarse antes de integrarse con el análisis de débito.

---

# Validación requerida

El soporte de TDC no debe considerarse estable hasta que pueda comprobarse sistemáticamente contra los valores reportados por BBVA.

El principio debe ser el mismo utilizado para débito:

> Generar un CSV no es suficiente para considerar correcta una extracción.

La información extraída debe poder compararse contra:

```text
saldos
totales
pagos
cargos
resúmenes
```

reportados por el estado de cuenta.

---

# Pruebas con múltiples periodos

Una nueva versión del extractor no debe probarse únicamente con un PDF.

Debe evaluarse con estados de cuenta correspondientes a diferentes periodos y estructuras.

Conceptualmente:

```text
Formato histórico A
        +
Formato histórico B
        +
Formato actual
        │
        ▼
Pruebas de regresión
```

Un cambio que corrige un formato reciente no debe romper los formatos anteriores.

---

# Integración futura con la clasificación

Cuando la extracción de TDC sea fiable, los movimientos podrán incorporarse al clasificador existente.

Por ejemplo:

```text
Compra supermercado
        ↓
alimentacion
```

```text
Netflix
        ↓
suscripciones
```

```text
Farmacia
        ↓
salud
```

```text
Uber
        ↓
transporte
```

Esto permitirá que el presupuesto refleje el consumo independientemente del medio de pago utilizado.

---

# Arquitectura objetivo

Una posible arquitectura futura es:

```text
                Estados de cuenta
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
       Débito                      TDC
          │                         │
          ▼                         ▼
     Movimientos               Movimientos
          │                         │
          └────────────┬────────────┘
                       │
                       ▼
              Normalización común
                       │
                       ▼
                Clasificación
                       │
                       ▼
             Presupuesto mensual
```

El objetivo es que la clasificación dependa del significado económico del movimiento y no de la cuenta o tarjeta utilizada para pagarlo.

---

# Estado experimental

Hasta completar esta integración:

- no mezcles los CSV de TDC con los consolidados estables de débito;
- no utilices los scripts de TDC para resultados financieros definitivos;
- valida manualmente cualquier resultado producido por estos scripts;
- conserva los cambios de TDC separados conceptualmente del flujo estable.

---

# Contribuciones futuras

Las mejoras más importantes para TDC incluyen:

1. detectar automáticamente diferentes versiones del PDF;
2. extraer de forma fiable el saldo al corte;
3. extraer y validar movimientos;
4. distinguir compras regulares y MSI;
5. identificar intereses y comisiones;
6. consolidar múltiples periodos;
7. crear validaciones automáticas;
8. integrar TDC con el clasificador;
9. eliminar el doble conteo de `pago_tdc`;
10. incorporar los gastos de TDC al presupuesto mensual.

---

# Privacidad

Los estados de cuenta de tarjeta pueden contener:

```text
nombre
número de tarjeta
número de cliente
RFC
CLABE
dirección
límites de crédito
saldos
movimientos
```

No subas estados de cuenta reales ni archivos generados al repositorio.

Las rutas utilizadas para datos financieros deben permanecer excluidas mediante `.gitignore`.

---

## Documentación relacionada

Para conocer el flujo actualmente estable:

**[Debit Extractor](debit-extractor.md)**

Para comprender la validación:

**[Validation](validation.md)**

Para conocer cómo se clasifican actualmente los pagos de tarjeta:

**[Transaction Classification](transaction-classification.md)**

Para comprender su efecto actual en el presupuesto:

**[Monthly Budget](monthly-budget.md)**