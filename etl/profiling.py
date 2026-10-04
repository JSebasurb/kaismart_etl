"""PARTES 3, 4 y 5 - Comprensión, perfil de calidad y estadísticos (EDA).
Todo es de solo lectura: ninguna función modifica el DataFrame recibido."""
import pandas as pd


# ---------- PARTE 3 ----------
def clasificar_columnas(df):
    """Clasificación heurística de columnas por rol."""
    ids, fechas, numericas, categoricas = [], [], [], []
    for c in df.columns:
        nombre = str(c).lower()
        if nombre.startswith("unnamed"):
            continue
        if nombre.endswith("_id") or nombre.startswith("id_") or "guia" in nombre:
            ids.append(c)
        elif "fecha" in nombre or "hora" in nombre and "tiempo" not in nombre:
            fechas.append(c)
        elif pd.api.types.is_numeric_dtype(df[c]):
            numericas.append(c)
        else:
            categoricas.append(c)
    return {"identificadores": ids, "fechas": fechas,
            "numericas": numericas, "categoricas": categoricas}


def estructura(df):
    t = pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "no_nulos": df.notna().sum(),
        "nulos": df.isna().sum(),
    })
    t.index.name = "variable"
    return t


def rango_fechas(df, columnas=None):
    columnas = columnas or [c for c in df.columns if "fecha" in str(c).lower()]
    filas = []
    for c in columnas:
        s = pd.to_datetime(df[c], errors="coerce")
        filas.append({"columna": c, "minimo": s.min(), "maximo": s.max(),
                      "no_parseables": int(df[c].notna().sum() - s.notna().sum())})
    return pd.DataFrame(filas)


# ---------- PARTE 4 ----------
def perfil_nulos(df):
    n = df.isna().sum()
    t = pd.DataFrame({"nulos": n, "porcentaje": (n / len(df) * 100).round(2)})
    return t.sort_values("porcentaje", ascending=False)


def perfil_unicos(df):
    n = len(df)
    t = pd.DataFrame({"nunique": df.nunique(dropna=True)})
    t["pct_cardinalidad"] = (t["nunique"] / n * 100).round(2)
    t["clasificacion"] = pd.cut(
        t["pct_cardinalidad"], [-1, 1, 50, 99.9, 101],
        labels=["baja cardinalidad", "media", "alta cardinalidad", "posible identificador"])
    return t.sort_values("nunique", ascending=False)


def perfil_duplicados(df, columnas_id=()):
    out = {"filas_completamente_duplicadas": int(df.duplicated().sum())}
    for c in columnas_id:
        if c in df.columns:
            out[f"repetidos_en_{c}"] = int(df[c].duplicated().sum())
    return out


def perfil_tipos(df):
    """Muestra el dtype de Python junto a un ejemplo para juzgar coherencia."""
    return pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "ejemplo": [df[c].dropna().iloc[0] if df[c].notna().any() else None for c in df.columns],
    })


# ---------- PARTE 5 ----------
def describe_numericas(df, columnas=None):
    cols = columnas or df.select_dtypes("number").columns
    d = df[cols].describe().T
    d["mediana"] = df[cols].median()
    d["nulos"] = df[cols].isna().sum()
    return d


def frecuencias(df, col, dropna=False):
    vc = df[col].value_counts(dropna=dropna)
    return pd.DataFrame({"frecuencia": vc, "porcentaje": (vc / len(df) * 100).round(2)})


def resumen_categorica(df, col):
    vc = df[col].value_counts()
    return {"columna": col, "unicos": int(df[col].nunique()),
            "mas_frecuente": vc.index[0] if len(vc) else None,
            "frecuencia_mas_frecuente": int(vc.iloc[0]) if len(vc) else 0}
