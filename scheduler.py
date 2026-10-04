"""PARTE 8 - Orquestador con la librería schedule.
Uso:   python scheduler.py            -> queda corriendo y ejecuta el ETL todos los días
       python scheduler.py --una-vez  -> ejecuta el ETL una sola vez (útil para probar)"""
import argparse
import logging
import time
import traceback
from datetime import datetime

import schedule

from etl.config import cargar_config, RAIZ
from etl.pipeline import ejecutar_pipeline

cfg = cargar_config()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler(RAIZ / cfg["rutas"]["logs"] / "etl.log", encoding="utf-8"),
              logging.StreamHandler()])
log = logging.getLogger("orquestador")


def job():
    inicio = datetime.now()
    log.info(">>> Ejecución programada iniciada")
    try:
        ejecutar_pipeline(cfg)
        log.info("<<< ETL OK en %.1f s", (datetime.now() - inicio).total_seconds())
    except Exception:
        log.error("<<< ETL FALLÓ\n%s", traceback.format_exc())   # el orquestador sigue vivo


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--una-vez", action="store_true")
    a = ap.parse_args()
    if a.una_vez:
        job()
    else:
        schedule.every().day.at(cfg["scheduler"]["hora_diaria"]).do(job)
        log.info("Orquestador activo. Próxima ejecución: %s", schedule.next_run())
        if cfg["scheduler"].get("ejecutar_al_iniciar"):
            job()
        while True:
            schedule.run_pending()
            time.sleep(30)
