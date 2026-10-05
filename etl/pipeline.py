"""Pipeline completo: Bronze -> Silver -> Gold (usado por el notebook y por el scheduler)."""
import logging
import pandas as pd
from .config import cargar_config, ruta
from .extract import extraer_ventas, extraer_logistica, guardar_bronze
from .transform import Decisiones, silver_ventas, silver_logistica, gold_pedidos

log = logging.getLogger(__name__)


def ejecutar_pipeline(cfg=None):
    cfg = cfg or cargar_config()
    log.info("Inicio pipeline | autores: %s", ", ".join(cfg["autores"]))

    # BRONZE
    try:
        df_ventas = extraer_ventas(cfg)
    except Exception as e:
        log.error("No se pudo extraer ventas (%s). Se continúa solo con logística.", e)
        df_ventas = None
    df_logistica = extraer_logistica(cfg)
    guardar_bronze(cfg, df_ventas, df_logistica)

    # SILVER
    dec = Decisiones()
    df_ventas_transformado = silver_ventas(df_ventas, dec) if df_ventas is not None else None
    fechas_venta = (df_ventas_transformado.set_index("pedido_id")["fecha_venta"]
                    if df_ventas_transformado is not None and "fecha_venta" in df_ventas_transformado else None)
    df_logistica_transformado = silver_logistica(df_logistica, dec, fechas_venta)
    if df_ventas_transformado is not None:
        df_ventas_transformado.to_csv(ruta(cfg, "silver", "ventas_silver.csv"), index=False)
    df_logistica_transformado.to_csv(ruta(cfg, "silver", "logistica_silver.csv"), index=False)

    # GOLD
    df_gold = gold_pedidos(df_ventas_transformado, df_logistica_transformado, dec)
    df_gold.to_csv(ruta(cfg, "gold", "pedidos_gold.csv"), index=False)
    dec.df().to_csv(ruta(cfg, "reportes", "decisiones_transformacion.csv"), index=False, encoding="utf-8-sig")

    log.info("Fin pipeline | ventas=%s | logística bronze=%s silver=%s | gold=%s",
             "OK" if df_ventas is not None else "NO DISPONIBLE", df_logistica.shape,
             df_logistica_transformado.shape, df_gold.shape)
    return dict(df_ventas=df_ventas, df_logistica=df_logistica,
                df_ventas_transformado=df_ventas_transformado,
                df_logistica_transformado=df_logistica_transformado,
                df_gold=df_gold, decisiones=dec.df())
