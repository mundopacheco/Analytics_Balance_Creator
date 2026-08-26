# Troubleshooting

Esta guía reúne problemas comunes durante la extracción, validación y análisis de estados de cuenta.

El flujo recomendado para diagnosticar problemas es:

```text
PDF
 ↓
Extracción
 ↓
Validación
 ↓
Consolidación
 ↓
Análisis
 ↓
Clasificación
 ↓
Presupuesto
```

Cuando aparece un error, conviene identificar primero en qué etapa se origina antes de modificar las etapas posteriores.

---

# El PDF no se procesa

## Verificar que el archivo exista

Comprueba que el PDF se encuentre dentro de:

```text
Estados de cuenta/
```

Por ejemplo:

```text
Estados de cuenta/Enero 2025.pdf
```

Puedes revisar el contenido de la carpeta desde la terminal.

En Git Bash:

```bash
ls "Estados de cuenta"
```

En PowerShell:

```powershell
Get-ChildItem "Estados de cuenta"
```

---

# No se puede inferir el año

El extractor puede utilizar el nombre del archivo para determinar el año correspondiente al estado de cuenta.

Utiliza nombres como:

```text
Enero 2025.pdf
Febrero 2025.pdf
Marzo 2025.pdf
```

Evita nombres como:

```text
Enero.pdf
estado.pdf
documento1.pdf
```

El nombre debe contener un año de cuatro dígitos.

---

# El PDF no contiene texto seleccionable

El extractor utiliza PyMuPDF y espera encontrar texto embebido dentro del PDF.

Puedes comprobarlo con:

```bash
python debug_pdf_text.py "Estados de cuenta/Enero 2025.pdf"
```

Si no aparece contenido útil, el documento puede estar compuesto únicamente por imágenes.

Actualmente, el flujo estable no incluye OCR.

---

# Inspeccionar el texto extraído

Cuando el contenido visible del PDF no coincide con lo que obtiene el extractor, ejecuta:

```bash
python debug_pdf_text.py "Estados de cuenta/Archivo.pdf"
```

Esto permite observar cómo PyMuPDF interpreta el documento.

Recuerda que:

```python
page.get_text("text")
```

recupera texto, pero no necesariamente conserva correctamente la estructura visual de una tabla.

---

# No se detectan movimientos

Comprueba primero que el PDF contenga la sección correspondiente al detalle de operaciones.

Dependiendo de la versión del estado de cuenta puede existir un encabezado similar a:

```text
DETALLE DE MOVIMIENTOS REALIZADOS
```

Si BBVA modificó el diseño, el extractor puede necesitar ajustes.

Utiliza:

```bash
python debug_pdf_text.py "Estados de cuenta/Archivo.pdf"
```

para identificar los encabezados disponibles.

---

# Faltan algunos movimientos

Si el CSV contiene movimientos pero faltan operaciones visibles en el PDF, no asumas que el problema se encuentra en la consolidación.

Primero revisa el CSV individual correspondiente al estado de cuenta.

El flujo de diagnóstico recomendado es:

```text
PDF original
      ↓
CSV individual
      ↓
CSV consolidado
```

Si el movimiento falta en el CSV individual, el problema está en la extracción.

Si aparece en el CSV individual pero no en el consolidado, el problema se encuentra en la consolidación o en el archivo utilizado durante el análisis.

---

# El movimiento aparece en el CSV individual pero no en la libreta

Comprueba que la libreta esté cargando el consolidado correcto.

En entornos como Google Colab pueden existir varias versiones de un mismo archivo.

Revisa:

```python
print(ruta)
```

o la información mostrada por la celda de carga.

También comprueba:

```python
df.shape
```

y:

```python
df.columns
```

para confirmar que el DataFrame corresponde al archivo esperado.

---

# Cargos y abonos aparecen invertidos

Este problema puede ocurrir si se intenta interpretar el PDF únicamente mediante el orden del texto.

El extractor utiliza:

```python
page.get_text("words")
```

para recuperar las coordenadas de cada elemento.

Las posiciones horizontales permiten identificar las columnas correspondientes a:

```text
CARGOS
ABONOS
```

Si BBVA modifica nuevamente el diseño del PDF, estas zonas pueden requerir ajustes.

---

## Depurar cargos y abonos

Ejecuta:

```bash
python extract_bbva_debito.py --input "Estados de cuenta/Archivo.pdf" --output "csv_output/Archivo.csv" --debug-tokens
```

Revisa:

- coordenada X del importe;
- encabezado de cargos;
- encabezado de abonos;
- posición relativa del importe;
- página donde se detectó el movimiento.

Consulta [Debit Extractor](debit-extractor.md) para conocer la lógica utilizada.

---

# La descripción contiene texto extraño

Los PDF pueden contener texto adicional cerca de una operación.

Por ejemplo:

```text
RENDIMIENTO QUE OBTENDRIA...
INSTITUCION DE BANCA MULTIPLE...
```

puede terminar concatenado accidentalmente a una descripción.

Esto ocurre porque un PDF almacena elementos posicionados y no necesariamente filas estructuradas.

La etapa de normalización intenta eliminar parte de este ruido sin modificar la descripción original.

---

# Los totales no coinciden con BBVA

Si:

```text
Cargos calculados != Cargos BBVA
```

o:

```text
Abonos calculados != Abonos BBVA
```

no continúes directamente con el presupuesto.

Primero identifica la discrepancia.

---

## Diferencia en cargos

Busca:

- movimientos faltantes;
- movimientos duplicados;
- retiros;
- transferencias enviadas;
- comisiones;
- importes clasificados accidentalmente como abono.

---

## Diferencia en abonos

Busca:

- nómina;
- depósitos;
- transferencias recibidas;
- devoluciones;
- importes clasificados accidentalmente como cargo.

---

# Cargos y abonos coinciden, pero el saldo no

Si:

```text
Cargos calculados = Cargos BBVA
```

y:

```text
Abonos calculados = Abonos BBVA
```

pero:

```text
Saldo anterior + Abonos - Cargos != Saldo final
```

revisa:

```text
saldo_anterior
saldo_final
periodo_inicio
periodo_fin
```

El problema probablemente se encuentre en la extracción del resumen o del saldo, no en los movimientos.

---

# Aparecen diferencias extremadamente pequeñas

Una validación puede mostrar valores como:

```text
9.094947e-13
```

o:

```text
-3.637979e-12
```

Esto es normal cuando se utilizan números de punto flotante.

Para efectos monetarios:

```text
0.000000000003637
```

equivale a:

```text
$0.00
```

Utiliza una tolerancia razonable al comparar cantidades.

Por ejemplo:

```python
TOLERANCIA = 0.02
```

---

# La gráfica de saldo muestra valores imposibles

Si una gráfica construida con:

```python
df["monto"].cumsum()
```

muestra un saldo negativo que no coincide con la cuenta real, probablemente no exista un error en la suma.

El problema es la interpretación.

`cumsum()` calcula:

```text
Flujo acumulado desde el primer movimiento disponible
```

y no:

```text
Saldo bancario real
```

si el historial comenzó con un saldo diferente de cero.

---

# Cómo graficar el saldo real

Utiliza los saldos extraídos directamente de los estados de cuenta.

Conceptualmente:

```text
Saldo real
=
Saldo inicial real
+
Flujo acumulado
```

Los archivos de saldos permiten evitar la suposición de que el historial comienza en `$0`.

Consulta [Colab Analysis](colab-analysis.md).

---

# La gráfica mensual no coincide con el estado de cuenta

Comprueba si estás comparando:

```text
mes calendario
```

contra:

```text
periodo bancario
```

No necesariamente representan las mismas fechas.

Por ejemplo:

```text
Abril calendario:
01/04 al 30/04
```

puede ser diferente de:

```text
Estado de cuenta:
21/03 al 20/04
```

Utiliza periodos bancarios para validar contra BBVA y meses calendario para análisis de presupuesto.

---

# Aparecen fechas futuras

La libreta detecta fechas posteriores al día actual.

El límite debe calcularse dinámicamente mediante:

```python
pd.Timestamp.today().normalize()
```

y no mediante una fecha fija.

Si aparecen muchas fechas futuras, revisa:

- reconstrucción del año;
- formato de fecha;
- cambio diciembre/enero;
- nombre del PDF.

---

# Un movimiento grande aparece como outlier

Un movimiento estadísticamente grande no necesariamente es incorrecto.

Puede representar:

```text
préstamo
compra de inmueble
inversión
transferencia
bono
gasto extraordinario
```

No elimines automáticamente todos los movimientos grandes.

La clasificación financiera debe determinar primero su naturaleza.

---

# Un préstamo aparece como ingreso

Desde la perspectiva bancaria, un préstamo recibido es un abono.

Sin embargo:

```text
abono != ingreso laboral
```

La clasificación debe identificar conceptos como:

```text
PRESTAMO OTORGADO
```

como:

```text
tipo_movimiento = financiamiento
```

y excluirlos de la estimación del ingreso ordinario.

---

# Una compra extraordinaria distorsiona el presupuesto

Movimientos como:

```text
compraventa de inmueble
gastos notariales
enganches
```

pueden ser completamente válidos pero no representativos del comportamiento mensual.

Estos movimientos deben conservarse en el historial y clasificarse como:

```text
gasto_extraordinario
```

con:

```text
incluir_presupuesto = False
```

---

# Pago de TDC aparece como deuda

Mientras no se analicen los movimientos internos de la tarjeta, un pago desde débito hacia TDC no debe asumirse automáticamente como deuda.

Debe utilizarse:

```text
categoria_presupuesto = pago_tdc
```

Esto permite mostrar la salida financiera sin asumir qué tipo de consumo existe detrás.

---

# El mismo `pago_tdc` aparece con tipos diferentes

Si observas algo como:

```text
gasto         | pago_tdc
transferencia | pago_tdc
```

revisa el orden de las reglas dentro de:

```python
clasificar_movimiento()
```

El caso especial:

```python
if categoria == "pago_tdc":
```

debe evaluarse antes del retorno genérico utilizado para los gastos.

Todos los pagos TDC deberían utilizar una clasificación consistente.

---

# Demasiados movimientos aparecen en `otros`

Esto significa que el clasificador no encontró suficiente información para asignar una categoría.

No necesariamente representa un error.

La categoría:

```text
otros
```

es preferible a una clasificación incorrecta.

---

## Auditar `otros`

Agrupa los movimientos por:

```text
comercio_base
```

y ordénalos por:

```text
gasto_total
```

Esto permite identificar primero los conceptos con mayor impacto económico.

Prioriza reglas generales que puedan ser útiles para diferentes usuarios.

---

# Evitar reglas demasiado personales

No agregues al clasificador general reglas basadas únicamente en:

```text
nombres de familiares
nombres de amigos
apodos
fechas personales
montos específicos
```

Si una clasificación solo tiene sentido para un usuario, debería formar parte de una futura capa de configuración personal y no del clasificador general.

---

# Demasiado dinero aparece como `efectivo`

Un retiro de efectivo solamente permite saber que el dinero salió de la cuenta.

No permite conocer en qué se utilizó posteriormente.

Por esta razón:

```text
efectivo
```

se mantiene como categoría separada.

No es correcto distribuir automáticamente ese monto entre alimentación, transporte u otras categorías sin información adicional.

---

# El presupuesto sugerido parece demasiado alto

Revisa especialmente:

```text
otros
efectivo
```

Estas categorías pueden aparecer dentro del análisis histórico, pero se consideran:

```text
requiere_revision
```

y no deben interpretarse automáticamente como una recomendación de gasto.

También revisa:

```text
gastos extraordinarios
financiamiento
transferencias
```

para confirmar que estén excluidos correctamente.

---

# El presupuesto sugerido parece demasiado bajo

Compara:

```text
Mediana histórica
Promedio últimos 3 meses
Mediana últimos 6 meses
Provisión mensual
```

El comportamiento reciente puede haber cambiado respecto al historial.

La metodología actual es una heurística y puede requerir ajustes si existe un cambio estructural en los gastos.

---

# La provisión mensual parece menor al gasto real

Esto puede ser correcto.

La provisión responde:

> ¿Cuánto habría sido necesario reservar cada mes para cubrir históricamente este gasto?

No responde:

> ¿Cuánto cuesta el gasto cuando ocurre?

Por ejemplo:

```text
Seguro anual = $12,000
```

puede producir:

```text
Mediana cuando ocurre = $12,000
Provisión mensual = $1,000
```

Ambos valores son correctos y representan conceptos diferentes.

---

# La tabla de Colab tiene texto ilegible

Google Colab puede utilizar un tema oscuro y heredar colores de texto que no funcionan bien con fondos personalizados.

Cuando se utilice:

```python
pandas.Styler
```

define explícitamente:

```text
background-color
color
```

para evitar depender del tema del navegador.

Por ejemplo:

```python
.set_properties(
    **{
        "color": "#202124"
    }
)
```

---

# Las fórmulas Markdown no se muestran correctamente en Colab

Google Colab puede tener diferencias de renderizado con algunas expresiones LaTeX.

Para fórmulas con fracciones puede utilizarse:

```markdown
$$
\mathrm{Frecuencia}
=
\frac{
\mathrm{Meses\;con\;gasto}
}{
\mathrm{Meses\;analizados}
}
$$
```

Para texto financiero simple suele ser más robusto utilizar Markdown normal.

Por ejemplo:

```markdown
**Ingreso mensual = Gastos + Ahorro + Disponible**
```

---

# `NameError` en la libreta

Un error como:

```text
NameError: name 'df_total' is not defined
```

significa que el código intenta utilizar una variable que todavía no fue creada o cuyo nombre cambió.

En notebooks esto puede ocurrir cuando:

- las celdas se ejecutan fuera de orden;
- una celda fue modificada;
- el runtime se reinició;
- una variable cambió de nombre.

Una buena práctica es ejecutar:

```text
Runtime
→ Run all
```

desde el inicio después de realizar cambios importantes.

---

# El notebook funcionaba y dejó de funcionar

Google Colab mantiene variables únicamente durante la sesión activa.

Si el runtime se reinicia:

```text
DataFrames
funciones
variables
archivos temporales
```

pueden desaparecer.

Vuelve a cargar los archivos y ejecuta las celdas desde el principio.

---

# Se está utilizando el CSV equivocado

Cuando existen varios CSV en `/content`, una búsqueda automática puede seleccionar un archivo diferente al esperado.

Revisa siempre la salida:

```text
Archivo detectado:
Ruta:
```

antes de continuar.

También puedes mostrar:

```python
print(ruta)
```

para confirmar el archivo utilizado.

---

# El consolidado parece incompleto

Antes de modificar el extractor, comprueba:

1. que el movimiento exista en el PDF;
2. que exista en el CSV individual;
3. que exista en el consolidado correcto;
4. que la libreta esté leyendo ese consolidado.

Esto evita corregir el componente equivocado.

---

# Cambié el extractor y dejaron de funcionar PDFs antiguos

BBVA ha utilizado diferentes estructuras de estados de cuenta.

Un cambio que corrige un formato reciente puede romper un formato anterior.

Por esta razón, después de modificar el extractor se recomienda ejecutar nuevamente todo el historial disponible.

Los estados de cuenta históricos funcionan como un conjunto práctico de pruebas de regresión.

---

# Warning de LF y CRLF en Git

En Windows puede aparecer:

```text
warning: LF will be replaced by CRLF
```

Esto normalmente no representa un error del código.

Git está informando que los finales de línea pueden convertirse entre:

```text
LF
```

y:

```text
CRLF
```

dependiendo de la configuración del sistema.

El archivo puede seguir versionándose normalmente.

---

# Verificar archivos antes de un commit

Antes de ejecutar:

```bash
git add .
```

revisa:

```bash
git status
```

y confirma que no aparezcan:

```text
Estados de cuenta/
csv_output/
PDF
CSV con información financiera
```

El `.gitignore` debe excluir estas rutas.

---

# Flujo de diagnóstico recomendado

Cuando algo no funciona, utiliza este orden:

```text
1. Identificar el PDF afectado.

2. Comparar el PDF contra el CSV individual.

3. Ejecutar debug_pdf_text.py si falta información.

4. Ejecutar --debug-tokens si el problema es cargo/abono.

5. Comparar cargos y abonos contra el resumen BBVA.

6. Confirmar que el periodo cuadra.

7. Revisar el consolidado.

8. Confirmar qué archivo carga la libreta.

9. Revisar limpieza y clasificación.

10. Revisar presupuesto únicamente después de validar lo anterior.
```

Este orden ayuda a evitar modificaciones innecesarias en etapas que ya funcionan correctamente.

---

# Reportar un problema

Cuando se investigue un nuevo formato de PDF o un error del extractor, resulta útil conservar:

```text
versión de Python
nombre del script
mensaje de error
periodo del estado de cuenta
salida de debug_pdf_text.py
salida relevante de --debug-tokens
diferencia de cargos
diferencia de abonos
```

Evita publicar información financiera sensible al crear issues públicos.

Anonimiza:

```text
nombres
números de cuenta
CLABE
números de tarjeta
direcciones
referencias personales
```

antes de compartir ejemplos.

---

## Más información

Para comprender cómo se extraen los movimientos:

**[Debit Extractor](debit-extractor.md)**

Para comprender las comprobaciones financieras:

**[Validation](validation.md)**

Para problemas relacionados con clasificación:

**[Transaction Classification](transaction-classification.md)**

Para comprender el cálculo del presupuesto:

**[Monthly Budget](monthly-budget.md)**