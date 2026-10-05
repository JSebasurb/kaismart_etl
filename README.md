
# kaismart_etl
=======
# Laboratorio ETL – Kaismart Solutions S.A.S. (UAO)

Arquitectura **Medallion**: Bronze (crudo) → Silver (limpio) → Gold (integrado por pedido).

## Estructura
```
config.yaml            # autores, credenciales MySQL, rutas, hora del scheduler
scheduler.py           # PARTE 8: orquestador con la librería schedule
etl/                   # extract.py, profiling.py (EDA), transform.py (Silver/Gold), pipeline.py
notebooks/laboratorio_etl.ipynb   # Partes 1-8 + conclusiones (ENTREGABLE PRINCIPAL)
data/                  # Excel fuente + bronze/ silver/ gold/ (se generan al ejecutar)
reports/decisiones_transformacion.csv   # cada decisión de limpieza explicada
```

## Cómo ejecutar
```bash
pip install -r requirements.txt
jupyter notebook notebooks/laboratorio_etl.ipynb    # Run All
python scheduler.py --una-vez                        # ETL completo una vez
python scheduler.py                                  # ETL automático diario
```
Opcional: `KAISMART_DB_PASSWORD` sobreescribe la contraseña de `config.yaml`.

## Estado de las capas Medallion incluidas en el zip
`data/bronze`, `data/silver` y `data/gold` ya traen los archivos de **logística** (generados con el Excel real).
Los archivos de **ventas** (`ventas_raw.csv`, `ventas_silver.csv`) y el Gold integrado ventas+logística se crean al ejecutar
el notebook o `python scheduler.py --una-vez` con acceso a MySQL (el Gold actual solo tiene el resumen logístico por pedido).
>>>>>>> 67dee0c (primer commit)
