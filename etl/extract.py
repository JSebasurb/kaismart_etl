"""PARTE 1 y 2 - Extracción (capa Bronze: datos crudos, sin modificar)."""
import logging
import pandas as pd
from .config import RAIZ, ruta

log = logging.getLogger(__name__)


def extraer_ventas(cfg) -> pd.DataFrame:
    """Lee la tabla ventas de MySQL y cierra SIEMPRE la conexión."""
    m = cfg["mysql"]
    conn = None
    try:
        import mysql.connector  # solo se necesita al extraer de MySQL
        conn = mysql.connector.connect(
            host=m["host"], user=m["user"], password=m["password"],
            database=m["database"], port=m.get("port", 3306),
        )
        df = pd.read_sql(f"SELECT * FROM {m['tabla']}", conn)
        log.info("Ventas extraídas de MySQL: %s", df.shape)
        return df
    except Exception as e:
        csv = cfg.get("ventas_csv_respaldo")
        if csv:
            log.warning("Fallo MySQL (%s). Usando CSV de respaldo %s", e, csv)
            return pd.read_csv(RAIZ / csv)
        raise
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
            log.info("Conexión MySQL cerrada")


def extraer_logistica(cfg) -> pd.DataFrame:
    e = cfg["excel"]
    df = pd.read_excel(RAIZ / e["ruta"], sheet_name=e["hoja"])
    log.info("Logística extraída de Excel: %s", df.shape)
    return df


def guardar_bronze(cfg, df_ventas, df_logistica):
    """Bronze = copia fiel de la fuente (no se modifica nada)."""
    if df_ventas is not None:
        df_ventas.to_csv(ruta(cfg, "bronze", "ventas_raw.csv"), index=False)
    df_logistica.to_csv(ruta(cfg, "bronze", "logistica_raw.csv"), index=False)
    log.info("Bronze guardado")


def verificar_extraccion(df, nombre):
    print(f"===== {nombre} =====")
    print("shape:", df.shape)
    print("columns:", list(df.columns))
    print(df.head())
    print("\nMuestra aleatoria (5):")
    print(df.sample(5, random_state=42))
