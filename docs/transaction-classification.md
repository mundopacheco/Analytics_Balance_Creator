# Transaction Classification

Los estados de cuenta describen cómo se mueve el dinero, pero no necesariamente explican su significado financiero.

Por ejemplo, desde la perspectiva bancaria:

```text
cargo = dinero que sale
abono = dinero que entra
```

Sin embargo:

```text
cargo != gasto
abono != ingreso
```

en todos los casos.

Una transferencia hacia otra cuenta propia es un cargo, pero no necesariamente representa consumo.

Un préstamo recibido es un abono, pero no representa ingreso laboral.

Por esta razón, Analytics Balance Creator incorpora una etapa de clasificación posterior a la extracción y validación.

---

# Objetivo

La clasificación intenta transformar movimientos como:

```text
PAGO DE NOMINA
AMAZON MX MARKETPLACE RFC: ...
RETIRO SIN TARJETA QR
PAGO TARJETA DE CREDITO ...
NAFIN ... CETESDIRECTO ...
```

en información más útil:

```text
Ingreso laboral
Compras
Efectivo
Pago TDC
Ahorro / inversión
```

El proceso se realiza sin modificar la descripción original.

---

# Flujo de clasificación

Conceptualmente:

```text
descripcion original
        │
        ▼
normalización
        │
        ▼
descripcion_base
        │
        ▼
identificación de comercio
        │
        ▼
comercio_base
        │
        ▼
clasificación financiera
        │
        ▼
categoría de presupuesto
```

Cada etapa agrega información derivada y conserva los datos originales.

---

# Descripción original

La columna original contiene el texto extraído del estado de cuenta.

Por ejemplo:

```text
AMAZON MX MARKETPLACE RFC: ABC123456 20:05
```

Esta información puede contener:

- comercio;
- RFC;
- referencias;
- números de autorización;
- horarios;
- identificadores bancarios;
- conceptos escritos por el usuario;
- información técnica del estado de cuenta.

La descripción original se conserva para permitir:

- auditoría;
- depuración;
- reclasificación;
- comparación contra el PDF.

---

# Normalización

Las descripciones bancarias suelen contener elementos que dificultan identificar operaciones equivalentes.

Por ejemplo:

```text
AMAZON MX RFC: ... 17:05
AMAZON MX RFC: ... 18:54
AMAZON MX MARKETPLACE RFC: ... 20:05
STRIPE *AMAZON RFC: ... 06:44
```

Aunque las cadenas son diferentes, todas pueden estar relacionadas con el mismo comercio.

La normalización crea una nueva columna:

```text
descripcion_base
```

sin reemplazar:

```text
descripcion_original
```

---

# Limpieza de ruido

Durante la normalización pueden eliminarse elementos técnicos que no aportan información relevante para la clasificación.

Por ejemplo:

```text
RFC
folio
autorización
CLABE
referencias
texto residual del PDF
```

También pueden eliminarse fragmentos que fueron concatenados accidentalmente durante la extracción de texto.

El objetivo no es reducir todas las descripciones a una sola palabra, sino conservar la información semántica útil.

---

# Información que debe conservarse

En transferencias es especialmente importante conservar el concepto cuando exista.

Por ejemplo:

```text
SPEI ENVIADO ... CETES
```

contiene información suficiente para inferir que probablemente corresponde a ahorro o inversión.

De manera similar:

```text
SPEI ENVIADO ... CIRUGIA
```

contiene una señal útil para clasificar el movimiento como salud.

Por esta razón, no se recomienda transformar automáticamente todos los SPEI en una única descripción como:

```text
TRANSFERENCIA
```

antes de analizar su concepto.

---

# Identificación de comercios

Después de normalizar las descripciones, la libreta intenta reconocer comercios e instituciones frecuentes.

Se crea una columna:

```text
comercio_base
```

Por ejemplo:

```text
AMAZON MX RFC: ...
AMAZON MX MARKETPLACE RFC: ...
STRIPE *AMAZON RFC: ...
```

pueden convertirse conceptualmente en:

```text
AMAZON
```

---

# Catálogo de comercios

El catálogo está diseñado para ser reutilizable y no depender de una sola persona.

Puede contener marcas frecuentes en México dentro de grupos como:

```text
Supermercados
E-commerce
Telecomunicaciones
Transporte
Restaurantes
Farmacias
Streaming
Seguros
Inversiones
```

Ejemplos de comercios o servicios que pueden reconocerse incluyen:

```text
Walmart
Sam's Club
Costco
Soriana
Chedraui
La Comer
OXXO

Amazon
Mercado Libre
Mercado Pago

Telmex
Telcel
AT&T
Movistar
Izzi
Totalplay
Megacable

Uber
DiDi

Netflix
Spotify
Disney

GNP
AXA
Allianz
MetLife
Mapfre
Qualitas

CETESDirecto
GBM
Actinver
Kuspit
```

El catálogo puede ampliarse sin modificar los movimientos originales.

---

# Evitar reglas personales

Para mantener la libreta reutilizable, las reglas generales no deben depender de:

```text
nombres de familiares
nombres de amigos
fechas personales
montos específicos
conceptos utilizados únicamente por una persona
```

Por ejemplo, una regla como:

```text
TRANSF A <NOMBRE>
```

no es apropiada como regla general del proyecto.

En esos casos es preferible utilizar patrones como:

```text
SPEI ENVIADO
TRANSFERENCIA
TRASPASO ENTRE CUENTAS
```

y conservar el concepto para una clasificación posterior.

---

# Clasificación financiera

Después de normalizar los movimientos se determina primero su naturaleza financiera.

La columna:

```text
tipo_movimiento
```

puede contener valores como:

```text
gasto
ingreso
transferencia
ahorro_inversion
financiamiento
deuda
gasto_extraordinario
desconocido
```

Esta clasificación es diferente de la categoría del presupuesto.

---

# Ejemplos

## Nómina

```text
PAGO DE NOMINA
```

puede clasificarse como:

```text
tipo_movimiento:
ingreso

categoria_presupuesto:
ingreso_laboral
```

---

## Préstamo recibido

```text
PRESTAMO OTORGADO
```

puede clasificarse como:

```text
tipo_movimiento:
financiamiento

categoria_presupuesto:
financiamiento
```

Aunque sea un abono, no se considera ingreso laboral.

---

## Transferencia entre cuentas

```text
TRASPASO ENTRE CUENTAS
```

puede clasificarse como:

```text
tipo_movimiento:
transferencia
```

El movimiento afecta el saldo de la cuenta analizada, pero puede no representar consumo.

---

# Clasificación de egresos

Los movimientos identificados como gastos pueden clasificarse en categorías generales orientadas a presupuesto.

Actualmente pueden utilizarse categorías como:

```text
vivienda
alimentacion
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
otros
```

También existen categorías especiales:

```text
pago_tdc
ahorro_inversion
extraordinarios
```

---

# Vivienda

Puede incluir conceptos relacionados con:

```text
renta
hipoteca
mantenimiento
reparaciones
agua
electricidad
gas
muebles
mejoras del hogar
```

Esta categoría puede contener gastos de naturalezas distintas.

En análisis futuros puede resultar útil dividirla en subcategorías como:

```text
vivienda_fija
servicios_vivienda
mantenimiento
mobiliario
```

---

# Alimentación

Puede incluir:

```text
supermercados
despensa
restaurantes
comida
desayunos
delivery
cafeterías
```

Es una de las categorías que con mayor frecuencia presenta comportamiento mensual recurrente.

---

# Transporte

Puede incluir:

```text
Uber
DiDi
gasolina
estacionamiento
casetas
TAG
transporte público
```

---

# Telecomunicaciones

Puede incluir:

```text
internet
telefonía fija
telefonía móvil
servicios de telecomunicaciones
```

Ejemplos:

```text
Telmex
Telcel
AT&T
Movistar
Izzi
Totalplay
Megacable
```

---

# Salud

Puede incluir:

```text
consultas
médicos
pediatría
dentista
hospital
laboratorios
farmacias
cirugía
terapia
```

---

# Educación

Puede incluir:

```text
colegiaturas
inscripciones
escuelas
universidades
cursos
academias
clases
```

---

# Seguros

Puede incluir:

```text
seguro de vida
seguro médico
seguro de automóvil
seguro de hogar
otros seguros
```

El reconocimiento puede apoyarse tanto en palabras genéricas como:

```text
SEGURO
```

como en instituciones conocidas.

---

# Compras

Puede incluir comercios generales y e-commerce.

Ejemplos:

```text
Amazon
Mercado Libre
Liverpool
Sears
Palacio de Hierro
```

La categoría no necesariamente indica que el gasto sea innecesario; simplemente identifica consumo que no pudo asignarse a una categoría más específica.

---

# Entretenimiento

Puede incluir:

```text
cine
eventos
boletos
videojuegos
viajes
hoteles
hobbies
```

---

# Suscripciones

Puede incluir servicios recurrentes como:

```text
Netflix
Spotify
Disney
Max
YouTube
servicios digitales
```

---

# Comisiones

Incluye cargos bancarios como:

```text
comisiones
IVA de comisiones
reposición de tarjeta
servicios bancarios
administración
```

Separar estas cantidades permite conocer el costo directo asociado al uso de servicios financieros.

---

# Pago de tarjeta de crédito

Los pagos realizados desde la cuenta de débito hacia una tarjeta de crédito se clasifican explícitamente como:

```text
pago_tdc
```

y no automáticamente como:

```text
deuda
```

---

## ¿Por qué?

Una tarjeta de crédito puede utilizarse para:

- gastos corrientes;
- servicios domiciliados;
- compras;
- meses sin intereses;
- financiamiento;
- deuda revolvente.

El estado de cuenta de débito solamente muestra:

```text
PAGO TARJETA DE CREDITO
```

pero no permite conocer qué compras originaron ese pago.

Por lo tanto, asumir:

```text
pago_tdc = deuda
```

sería demasiado restrictivo.

---

# Tratamiento actual de `pago_tdc`

Mientras los movimientos internos de TDC no formen parte del flujo estable, el pago se trata como:

```text
tipo_movimiento:
transferencia

categoria_presupuesto:
pago_tdc

incluir_presupuesto:
True
```

Esto permite mostrar explícitamente cuánto dinero sale de la cuenta de débito para cubrir tarjetas.

---

# Integración futura de TDC

Cuando se incorporen los movimientos individuales de tarjeta de crédito será necesario evitar doble conteo.

Por ejemplo:

```text
Compra en supermercado con TDC
            ↓
gasto de alimentación

Posteriormente:
Pago de TDC desde débito
            ↓
transferencia
```

Si ambos se contabilizaran como gasto, el mismo consumo aparecería dos veces.

Por ello, una integración futura deberá separar:

```text
consumo
```

de:

```text
liquidación de la tarjeta
```

---

# Ahorro e inversión

Las salidas hacia instrumentos de ahorro o inversión se separan del consumo.

Ejemplos:

```text
CETESDirecto
GBM
Actinver
fondos de inversión
otras cuentas de ahorro
```

Pueden clasificarse como:

```text
tipo_movimiento:
ahorro_inversion

categoria_presupuesto:
ahorro_inversion
```

Aunque el dinero sale de la cuenta, financieramente no tiene la misma naturaleza que una compra.

---

# Efectivo

Los retiros pueden identificarse mediante conceptos como:

```text
RETIRO SIN TARJETA
RETIRO SIN TARJETA QR
RETIRO CAJERO
EFECTIVO
```

Estos movimientos representan salidas reales de la cuenta.

Sin embargo, el estado de cuenta no permite conocer el destino posterior del efectivo.

Por esta razón:

```text
efectivo
```

se considera una categoría que requiere interpretación adicional.

---

# Limitación del efectivo

Supongamos que se retiran:

```text
$2,000
```

Ese dinero puede utilizarse posteriormente en:

```text
alimentación
transporte
compras
entretenimiento
salud
```

pero el banco solamente registra:

```text
retiro de efectivo
```

Por lo tanto, el clasificador no debe inventar una categoría final.

---

# Otros

Los movimientos que no pueden clasificarse con suficiente confianza permanecen en:

```text
otros
```

Esta categoría es deliberada.

Es preferible:

```text
otros
```

a asignar incorrectamente un gasto a una categoría específica.

---

# Auditoría de `otros`

La libreta permite analizar los movimientos no clasificados agrupándolos por:

```text
comercio_base
```

y calcular:

```text
movimientos
gasto_total
gasto_promedio
primera_fecha
ultima_fecha
```

Después se ordenan por:

```text
gasto_total
```

Esto permite priorizar las reglas que tengan mayor impacto económico.

---

# Cobertura del clasificador

Una métrica útil es:

```text
Porcentaje de gasto todavía en otros
```

Conceptualmente:

```text
Gasto en otros
------------------------- × 100
Gasto presupuestable
```

El objetivo no necesariamente es alcanzar 100%.

Una clasificación excesivamente agresiva puede producir errores.

Como referencia práctica, una cobertura automática alta con una categoría `otros` relativamente pequeña suele ser preferible a clasificar incorrectamente todos los movimientos.

---

# Transferencias sin clasificar

Los SPEI y otras transferencias requieren especial cuidado.

Si el concepto contiene información útil:

```text
SPEI ... CETES
```

puede clasificarse como inversión.

Si contiene:

```text
SPEI ... CIRUGIA
```

puede clasificarse como salud.

Pero si solamente se sabe que es:

```text
SPEI ENVIADO
```

sin suficiente contexto, puede clasificarse como:

```text
transferencia_sin_clasificar
```

y excluirse temporalmente del gasto de consumo.

---

# Gastos extraordinarios

Algunos movimientos son reales pero no representan comportamiento mensual ordinario.

Pueden incluir:

```text
compraventa de inmueble
gastos notariales
enganches
operaciones patrimoniales
otros movimientos excepcionales
```

Estos movimientos pueden clasificarse como:

```text
tipo_movimiento:
gasto_extraordinario

categoria_presupuesto:
extraordinarios

incluir_presupuesto:
False
```

---

# ¿Por qué excluir extraordinarios?

Supongamos que durante varios años el gasto mensual habitual se encuentra alrededor de:

```text
$30,000
```

pero en un mes existe una compra extraordinaria de:

```text
$1,750,000
```

Incluir ese movimiento en el promedio histórico distorsionaría significativamente cualquier presupuesto mensual.

El movimiento no se elimina.

Simplemente se separa del comportamiento ordinario.

---

# Outlier estadístico vs. movimiento extraordinario

Un movimiento extraordinario no es necesariamente lo mismo que un outlier estadístico.

Un gasto puede ser:

```text
muy grande
```

y aun así ser completamente correcto.

Por ejemplo:

```text
compra de inmueble
```

La clasificación financiera proporciona más contexto que eliminar automáticamente todos los valores que superen un límite estadístico.

---

# Prioridad de las reglas

El orden de clasificación es importante.

Conceptualmente:

```text
1. Identificar ingresos especiales
2. Identificar financiamiento
3. Identificar extraordinarios
4. Buscar categorías específicas
5. Analizar transferencias
6. Aplicar fallback
```

Por ejemplo:

```text
SPEI ENVIADO ... CETES
```

debe evaluarse contra:

```text
ahorro_inversion
```

antes de asignarlo simplemente a:

```text
transferencia_sin_clasificar
```

---

# Clasificación jerárquica

El diseño permite separar diferentes niveles:

```text
tipo_movimiento
categoria_presupuesto
comercio_base
descripcion_base
descripcion_original
```

Ejemplo:

```text
descripcion_original:
AMAZON MX MARKETPLACE RFC: ...

descripcion_base:
AMAZON MX MARKETPLACE

comercio_base:
AMAZON

tipo_movimiento:
gasto

categoria_presupuesto:
compras
```

Esto conserva trazabilidad desde la categoría final hasta el movimiento original.

---

# Clasificación manual

Las reglas automáticas no pueden resolver todos los casos.

Una implementación futura puede permitir una tabla de correcciones como:

```text
patron
categoria
subcategoria
```

que cada usuario pueda personalizar sin modificar el código principal.

Esto permitiría mantener:

```text
reglas generales
```

separadas de:

```text
preferencias personales
```

---

# Principio de diseño

La clasificación sigue este criterio:

> Es preferible conservar incertidumbre explícita que inventar precisión.

Por eso existen categorías como:

```text
otros
efectivo
transferencia_sin_clasificar
```

Estas categorías indican que conocemos el movimiento bancario, pero no necesariamente su destino económico final.

---

# Relación con el presupuesto

La clasificación transforma movimientos individuales en categorías que pueden agregarse mensualmente.

Conceptualmente:

```text
Miles de movimientos
        │
        ▼
Clasificación
        │
        ▼
Categorías
        │
        ▼
Gasto mensual por categoría
        │
        ▼
Presupuesto sugerido
```

La calidad del presupuesto depende directamente de la calidad de esta clasificación.

---

## Siguiente paso

Una vez clasificados los movimientos, continúa con:

**[Monthly Budget →](monthly-budget.md)**

para conocer cómo se utilizan la frecuencia, la mediana, el comportamiento reciente y la provisión mensual para construir una primera propuesta automática de presupuesto.