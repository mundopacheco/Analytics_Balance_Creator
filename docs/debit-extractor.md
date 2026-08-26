# Debit Extractor

El extractor de débito convierte estados de cuenta BBVA en PDF en datos estructurados que pueden utilizarse posteriormente para validación y análisis.

El objetivo del extractor no es únicamente recuperar el texto visible del PDF. También utiliza la **posición de los elementos dentro de la página** para interpretar correctamente tablas y distinguir cargos de abonos.

Actualmente, este es el flujo estable del proyecto.

---

## Objetivos del extractor

Para cada estado de cuenta, el extractor intenta obtener tres grupos principales de información:

1. **Movimientos**
2. **Saldos**
3. **Resumen del periodo**

Estos datos cumplen funciones diferentes.

### Movimientos

Representan las operaciones individuales realizadas durante el periodo.

Entre los campos principales se encuentran:

```text
fecha_oper
fecha_liq
descripcion
cargo
abono
pagina
```

### Saldos

Permiten conocer los saldos reportados directamente por BBVA.

Estos valores son importantes porque una suma acumulada de movimientos no necesariamente representa el saldo real de la cuenta si el historial disponible comienza después de la apertura de la cuenta.

### Resumen

Contiene los totales reportados por BBVA para el periodo y permite validar la extracción.

Entre los valores relevantes se encuentran:

```text
saldo_anterior
total_abonos
total_cargos
saldo_final
```

---

# ¿Por qué no basta con extraer el texto?

Un PDF no funciona como un archivo de texto tradicional.

Visualmente, BBVA puede mostrar una tabla como:

```text
FECHA     DESCRIPCIÓN             CARGOS       ABONOS
03/ENE    COMPRA COMERCIO          350.00
05/ENE    PAGO DE NOMINA                       18,000.00
```

Sin embargo, al extraer únicamente texto mediante:

```python
page.get_text("text")
```

PyMuPDF puede devolver los elementos en un orden que no representa necesariamente la estructura visual de la tabla.

Por ejemplo:

```text
03/ENE
COMPRA COMERCIO
350.00
05/ENE
PAGO DE NOMINA
18,000.00
```

En este resultado ya no existe información suficiente para determinar con certeza si `350.00` pertenece a la columna de cargos o de abonos.

---

# Extracción basada en coordenadas

Para resolver este problema, el extractor utiliza:

```python
page.get_text("words")
```

PyMuPDF devuelve cada palabra junto con su posición dentro de la página.

Conceptualmente, cada elemento contiene información similar a:

```text
x0
y0
x1
y1
texto
```

donde:

- `x0` representa la posición horizontal inicial;
- `y0` representa la posición vertical inicial;
- `x1` representa la posición horizontal final;
- `y1` representa la posición vertical final.

Esto permite reconstruir parcialmente la estructura visual del documento.

---

## Identificación de cargos y abonos

En los estados de cuenta, las columnas de cargos y abonos ocupan regiones horizontales diferentes.

Conceptualmente:

```text
                           coordenada X
                               →

DESCRIPCIÓN             CARGOS          ABONOS
Compra comercio          350.00
Pago nómina                              18,000.00
```

El extractor utiliza la posición horizontal del importe para determinar a qué columna pertenece.

En lugar de asumir:

```text
primer importe = cargo
segundo importe = abono
```

se evalúa la coordenada X del valor.

Conceptualmente:

```python
if x_importe in zona_cargos:
    cargo = importe

elif x_importe in zona_abonos:
    abono = importe
```

Esta estrategia es más fiable para documentos cuya información está organizada visualmente en columnas.

---

# Detección de columnas

El extractor identifica referencias visuales dentro de la página para determinar las posiciones correspondientes a:

```text
CARGOS
ABONOS
```

A partir de esas posiciones se construyen las zonas utilizadas para clasificar los importes.

Esto evita depender exclusivamente de valores de coordenadas completamente fijos.

Sin embargo, la estructura del PDF sigue siendo importante: si BBVA modifica significativamente el diseño del estado de cuenta, puede ser necesario actualizar las reglas de detección.

---

# Diferentes versiones de estados de cuenta

BBVA ha modificado el diseño de sus estados de cuenta a lo largo del tiempo.

Por este motivo, no todos los PDF presentan exactamente:

- las mismas páginas;
- los mismos encabezados;
- las mismas coordenadas;
- el mismo orden del texto;
- las mismas tablas;
- la misma estructura del resumen.

El extractor contiene lógica para manejar las estructuras observadas en diferentes periodos.

Esto es especialmente importante al analizar historiales de varios años.

---

## Principio de diseño

El extractor intenta evitar reglas dependientes de un único estado de cuenta.

Siempre que es posible, utiliza:

- encabezados;
- palabras clave;
- posiciones relativas;
- coordenadas de columnas;
- estructura del periodo;
- información del nombre del archivo.

El objetivo es mantener compatibilidad con diferentes estados de cuenta sin crear una regla específica para cada PDF.

---

# Sección de movimientos

El extractor busca la sección correspondiente al detalle de movimientos del periodo.

En diferentes versiones del documento puede aparecer con encabezados similares a:

```text
DETALLE DE MOVIMIENTOS REALIZADOS
```

Una vez identificada la sección, se analizan las filas que contienen operaciones.

Cada movimiento puede contener:

```text
Fecha de operación
Fecha de liquidación
Descripción
Referencia
Cargo
Abono
```

No todos estos campos aparecen necesariamente con la misma estructura en todas las versiones del PDF.

---

# Reconstrucción de movimientos

Una operación bancaria puede ocupar varias líneas visuales.

Por ejemplo:

```text
24/MAR    SAMS VENTA EN LINEA               1,893.76
          RFC: XXX 15:33 AUT: 667722
```

El extractor debe reconocer que la segunda línea forma parte del movimiento anterior y no representa una operación independiente.

Por este motivo, la extracción combina información textual y espacial para reconstruir cada registro.

El resultado esperado es una sola fila:

```text
fecha_oper | fecha_liq | descripcion | cargo | abono
2025-03-24 | 2025-03-21 | SAMS VENTA EN LINEA ... | 1893.76 |
```

---

# Fechas

Los estados de cuenta pueden mostrar fechas sin incluir explícitamente el año en cada movimiento.

Por ejemplo:

```text
24/MAR
```

El extractor utiliza la información disponible en el estado de cuenta y el año incluido en el nombre del PDF para reconstruir la fecha completa.

Por esta razón se recomienda utilizar nombres como:

```text
Marzo 2025.pdf
Abril 2025.pdf
```

y evitar:

```text
estado.pdf
documento1.pdf
```

---

# Cambio de año

Un estado de cuenta puede incluir movimientos correspondientes al mes anterior.

Esto es especialmente relevante alrededor de diciembre y enero.

El extractor debe evitar interpretar incorrectamente, por ejemplo:

```text
31/DIC
```

como diciembre del mismo año que un estado de cuenta correspondiente a enero.

La reconstrucción de fechas considera el periodo del estado de cuenta para asignar correctamente el año.

---

# Extracción del resumen

Además de los movimientos, el extractor obtiene información agregada reportada por BBVA.

Dependiendo de la versión del PDF, esta información puede aparecer con diferentes etiquetas o estructuras.

Los campos de interés incluyen conceptualmente:

```text
saldo_anterior
abonos
cargos
saldo_final
```

Estos valores no sustituyen los movimientos individuales.

Su función principal es permitir la **validación independiente de la extracción**.

---

# Validación durante la extracción

Una extracción de movimientos puede parecer correcta visualmente y aun así contener errores.

Por ejemplo:

- un movimiento omitido;
- un cargo clasificado como abono;
- un importe asociado a la fila incorrecta;
- una fecha reconstruida incorrectamente.

Por este motivo, el extractor compara los movimientos recuperados contra los totales reportados por BBVA.

Las principales comprobaciones son:

```text
Cargos extraídos = Cargos reportados por BBVA
```

```text
Abonos extraídos = Abonos reportados por BBVA
```

y:

```text
Saldo final = Saldo anterior + Abonos - Cargos
```

Consulta [Validation](validation.md) para conocer esta etapa con mayor detalle.

---

# Ejecutar el extractor

Para procesar un estado de cuenta:

```bash
python extract_bbva_debito.py --input "Estados de cuenta/Enero 2025.pdf" --output "csv_output/Enero 2025.csv"
```

El script procesa el PDF y genera los archivos correspondientes.

---

## Modo de depuración

Cuando una extracción no coincide con el estado de cuenta, utiliza:

```bash
python extract_bbva_debito.py --input "Estados de cuenta/Enero 2025.pdf" --output "csv_output/Enero 2025.csv" --debug-tokens
```

Este modo permite inspeccionar información adicional relacionada con los elementos detectados dentro del PDF.

Es especialmente útil para investigar:

- movimientos faltantes;
- importes incorrectos;
- cargos detectados como abonos;
- abonos detectados como cargos;
- encabezados no reconocidos;
- cambios en la estructura del PDF.

---

# Inspeccionar el texto del PDF

También puedes utilizar:

```bash
python debug_pdf_text.py "Estados de cuenta/Enero 2025.pdf"
```

Este script permite observar cómo PyMuPDF interpreta el contenido textual.

Es útil para comparar:

```python
page.get_text("text")
```

con la información visible en el documento.

Para problemas relacionados con columnas, la extracción basada en:

```python
page.get_text("words")
```

es generalmente más informativa porque conserva las coordenadas.

---

# Procesamiento masivo

Una vez validado el extractor con uno o varios archivos representativos, procesa todos los estados de cuenta mediante:

```bash
python procesar_estados.py
```

Este script:

1. localiza los estados de cuenta;
2. ejecuta el extractor para cada PDF;
3. genera los archivos individuales;
4. recopila saldos;
5. recopila resúmenes;
6. genera los consolidados históricos.

El procesamiento de múltiples archivos permite detectar también problemas que no aparecen al probar un único PDF.

---

# Comprobación recomendada

Después de modificar el extractor, no es suficiente verificar que el script termine sin errores.

Se recomienda comprobar al menos:

```text
PDF procesados correctamente
Cargos reportados
Cargos extraídos
Diferencia

Abonos reportados
Abonos extraídos
Diferencia
```

El objetivo es obtener diferencias de:

```text
$0.00
```

en los periodos procesados correctamente.

---

# Errores de punto flotante

Durante algunas validaciones pueden aparecer diferencias similares a:

```text
9.094947e-13
-3.637979e-12
1.455192e-11
```

Estas cantidades se producen por la representación binaria de números decimales en punto flotante.

Para importes monetarios, estos valores son efectivamente equivalentes a:

```text
$0.00
```

y no representan una discrepancia real entre el estado de cuenta y la extracción.

---

# Limitaciones

El extractor depende de la estructura de los estados de cuenta observados hasta el momento.

Una nueva versión del PDF puede requerir ajustes si BBVA modifica:

- los encabezados;
- la posición de las columnas;
- la estructura del resumen;
- el formato de las fechas;
- la organización de las páginas.

Por este motivo, la validación contra los totales reportados por BBVA es una parte esencial del flujo.

---

## PDF escaneados

El extractor utiliza PyMuPDF y espera texto embebido en el documento.

Si un PDF contiene únicamente imágenes escaneadas, `page.get_text()` puede no recuperar la información necesaria.

En ese caso sería necesario incorporar un proceso de OCR, funcionalidad que actualmente no forma parte del flujo estable.

---

# Principio de confiabilidad

El proyecto sigue este principio:

> Una extracción no debe considerarse correcta únicamente porque produjo un archivo CSV.

Para considerarla fiable, los movimientos extraídos deben reproducir los totales y saldos reportados por el banco.

Esto permite utilizar posteriormente los datos para análisis de flujo, clasificación de gastos y presupuesto con una base verificable.

---

## Siguiente paso

Una vez procesados los estados de cuenta, continúa con:

**[Output Files →](output-files.md)**

para conocer los archivos generados, su organización y la función de cada conjunto de datos.