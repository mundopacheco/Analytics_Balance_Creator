# Analytics Balance Creator

Analytics Balance Creator es un proyecto en Python para extraer, validar,
consolidar y analizar información financiera proveniente de estados de
cuenta BBVA en formato PDF.

El flujo actualmente estable corresponde a cuentas de débito.

Además de extraer movimientos, el proyecto obtiene los saldos y resúmenes
reportados por BBVA. Esta información permite validar que los cargos y
abonos extraídos reproduzcan correctamente el cambio de saldo de cada
periodo.

El repositorio también incluye una libreta compatible con Google Colab y
Jupyter para analizar los archivos consolidados, visualizar la evolución
del saldo, clasificar gastos y generar una propuesta automática de
presupuesto mensual.

## Estado del proyecto

### Cuenta de débito

El flujo de débito incluye:

- extracción de movimientos;
- identificación de cargos y abonos;
- extracción de saldos iniciales y finales;
- extracción del resumen de cada periodo;
- validación contra los totales reportados por BBVA;
- generación de archivos individuales;
- generación de archivos consolidados;
- análisis histórico;
- clasificación automática de movimientos;
- generación de una propuesta de presupuesto mensual.

### Tarjeta de crédito

Los scripts relacionados con tarjeta de crédito (TDC) continúan en
desarrollo y no forman parte del flujo estable.

Por el momento, los pagos realizados desde la cuenta de débito hacia una
tarjeta de crédito pueden identificarse como `pago_tdc`, pero no se
analizan todavía los movimientos internos de la tarjeta.

## Flujo general

El proyecto sigue cuatro etapas principales:

1. **Extracción**  
   Los estados de cuenta PDF se convierten en información estructurada.

2. **Validación**  
   Los cargos, abonos y saldos extraídos se comparan contra los valores
   reportados por BBVA.

3. **Consolidación**  
   Los diferentes estados de cuenta se combinan para formar un historial
   financiero.

4. **Análisis**  
   La libreta de análisis utiliza el historial para estudiar saldos,
   flujo mensual, categorías de gasto y presupuesto.

## Documentación

La documentación está organizada en las siguientes secciones:

- [Getting Started](getting-started.md)
- [Debit Extractor](debit-extractor.md)
- [Output Files](output-files.md)
- [Validation](validation.md)
- [Colab Analysis](colab-analysis.md)
- [Transaction Classification](transaction-classification.md)
- [Monthly Budget](monthly-budget.md)
- [Troubleshooting](troubleshooting.md)
- [TDC Development](tdc-development.md)
