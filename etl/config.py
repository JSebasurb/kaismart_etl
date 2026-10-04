import os
from pathlib import Path
import yaml

RAIZ = Path(__file__).resolve().parent.parent


def cargar_config(ruta_cfg="config.yaml"):
    with open(RAIZ / ruta_cfg, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    pwd = os.getenv("KAISMART_DB_PASSWORD")
    if pwd:
        cfg["mysql"]["password"] = pwd
    for v in cfg["rutas"].values():
        (RAIZ / v).mkdir(parents=True, exist_ok=True)
    return cfg


def ruta(cfg, capa, nombre):
    return RAIZ / cfg["rutas"][capa] / nombre
