# Laboratorio ETL – Kaismart Solutions S.A.S. (UAO)

**Autor:** Juan Sebastián Sánchez Urbano · juan_s.sanchez_u@uao.edu.co · Maestría en Ciencia de Datos e IA

Arquitectura **Medallion**: Bronze (crudo) → Silver (limpio) → Gold (integrado por pedido).



## 🔄 Flujo general del proceso ETL

```text
             FUENTES DE DATOS
                    │
          ┌─────────┴─────────┐
          │                   │
       MySQL                Excel
       ventas             logística
          │                   │
          └─────────┬─────────┘
                    │
                    ▼
              EXTRACCIÓN
                    │
                    ▼
               BRONZE
          Datos originales
                    │
                    ▼
             EXPLORACIÓN
                Y EDA
                    │
                    ▼
          CONTROL DE CALIDAD
                    │
                    ▼
                SILVER
        Datos limpios y depurados
                    │
                    ▼
             INTEGRACIÓN
                    │
                    ▼
                 GOLD
       Datos integrados para análisis
                    │
                    ▼
          PREGUNTAS DE NEGOCIO
                    │
                    ▼
            AUTOMATIZACIÓN
              DEL PIPELINE
```


## 1. Objetivo
Extraer, explorar, limpiar e integrar dos fuentes de Kaismart Solutions con arquitectura **Medallion** (Bronze → Silver → Gold) en Python, y automatizar el pipeline con `schedule`.

| Fuente | Origen | Tamaño |
|---|---|---|
| `df_ventas` | Tabla `ventas` en MySQL (base `clientes`) | 5.000 × 17 |
| `df_logistica` | Excel `kaismart_eventos_logisticos.xlsx` | 50.000 × 14 |

Ambas se unen por `pedido_id` (relación **1 venta : N eventos**, ~10 eventos por pedido).

## 2. Arquitectura Medallion

| Capa | Contenido | Carpeta |
|---|---|---|
| Bronze | Copia fiel de las fuentes, sin modificar | `data/bronze/` |
| Silver | `df_ventas_transformado` y `df_logistica_transformado`: sin duplicados, fechas en `datetime`, nulos tratados, categorías estandarizadas | `data/silver/` |
| Gold | Una fila por pedido: ventas + resumen logístico + indicadores | `data/gold/` |
| Reportes | Log de cada decisión de limpieza (problema, cantidad, acción, justificación) | `reports/decisiones_transformacion.csv` |

## 3. Estructura del proyecto

```
config.yaml                          # autores, conexión, rutas, hora del scheduler
scheduler.py                         # orquestador con schedule (Parte 8)
etl/                                 # extract, profiling (EDA), transform, pipeline
notebooks/laboratorio_etl.ipynb      # Partes 1 a 8 y conclusiones
data/                                # bronze / silver / gold / respaldo
reports/                             # decisiones de transformación
```

## 4. Hallazgos de `df_ventas`
1. 5.000 ventas (ene–jun 2026), 5.000 pedidos únicos, 2.292 clientes; **0 duplicados**.
2. Nulos **estructurales**, no errores: `id_tienda` 70,0 % (solo existe en tienda física) y `calificacion_cliente` 43,4 % (opcional).
3. Las cuentas cuadran al 100 %: `valor_bruto = cantidad × precio_unitario` y `valor_neto = bruto − descuento`.
4. Bogotá concentra el 33 % de las ventas y la web el 40 %; Tecnología lidera en número de ventas, pero **Deportes en valor neto**.
5. `valor_neto` sesgado a la derecha (media 633.695 vs mediana 367.110). Cada producto aparece con 5 precios unitarios distintos (a validar con comercial).

## 5. Hallazgos de `df_logistica`
1. 50.000 eventos para 5.000 pedidos: la fila es un **evento**, no un pedido.
2. **99 filas duplicadas exactas** y 100 `evento_id` repetidos → quedan 49.900 eventos únicos.
3. Columna basura de Excel (`Unnamed: 13`) y fechas almacenadas como texto.
4. Nulos normales del proceso: `incidencia` (98,98 %), `observacion` (96,55 %), `transportadora`/`numero_guia` antes del despacho (~60 %) y `tiempo_etapa_horas` en el primer evento (10 %). Nulos que sí son error: ciudad, CEDI, fecha prometida y fecha del evento (0,09 %–0,18 %).
5. `costo_envio` no depende de la ciudad (~13.500 en las 6) y ~25 % de los pedidos tiene un recargo del 10 %; solo ~1 % de los eventos tiene incidencia.

## 6. Decisiones de transformación
- **Duplicados:** se eliminan las copias exactas; ante un `evento_id` repetido se conserva la fila más completa.
- **Fechas:** `fecha_evento` nula (65) se reconstruye con la fecha de venta (10 casos) o con el evento anterior + `tiempo_etapa_horas` (55 casos), en lugar de inventarla con media o mediana.
- **Atributos fijos por pedido** (ciudad, CEDI, fecha prometida) y 140 valores de transportadora/guía posteriores al despacho: se recuperan desde el mismo pedido.
- **Nulos con significado:** se mantienen (`tiempo_etapa_horas` en "Pedido recibido", transportadora antes del despacho, `calificacion_cliente`) o se rotulan (`NO APLICA`, `SIN INCIDENCIA`, `SIN OBSERVACIÓN`).
- **Gold:** unión `one_to_one` por `pedido_id` con `n_eventos`, `entrega_a_tiempo`, `dias_hasta_entrega`, `n_incidencias`, `pedido_completo`, `valor_neto_mas_envio`, entre otros.

## 7. Validación cruzada y resultados
- Los 5.000 pedidos cruzan 1 a 1 y la ciudad de la venta coincide con la de destino en el **100 %**.
- 98 pedidos tienen el ciclo incompleto (96 con 9 estados y 2 con 8) y 10 no registran evento "Entregado".
- **82,9 %** de las entregas cumple la fecha prometida; el desempeño entre transportadoras es casi igual (82,1 %–83,5 %).
- Mediana de 1,45 días desde el primer evento hasta la entrega.

## 8. Automatización (Parte 8)
`scheduler.py` programa el pipeline completo con `schedule` (diario a las 02:00, configurable en `config.yaml`), escribe el log en `logs/etl.log` y no se detiene si una ejecución falla.

## 9. Cómo ejecutarlo

```bash
git clone https://github.com/JSebasurb/kaismart_etl.git
cd kaismart_etl
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt ipykernel

python scheduler.py --una-vez     # ejecuta el ETL una vez
python scheduler.py               # deja el orquestador activo (diario)
```

Notebook: abrir `notebooks/laboratorio_etl.ipynb`, seleccionar el kernel `.venv` y ejecutar **Run All**.

Si no hay conexión a MySQL (`107.180.112.11`), el pipeline usa el CSV de `data/respaldo/ventas_mysql_export.csv` (parámetro `ventas_csv_respaldo` en `config.yaml`) y lo deja registrado en el log.

>