"""PARTE 7 - Transformación (Medallion).
Bronze  = datos crudos (extract.py)
Silver  = datos limpios y estandarizados (df_ventas_transformado, df_logistica_transformado)
Gold    = datos integrados a nivel pedido, listos para análisis.
Cada decisión queda registrada en el log de decisiones (reports/decisiones_transformacion.csv)."""
import re
import unicodedata
import numpy as np
import pandas as pd

ORDEN_ESTADOS = [
    "Pedido recibido", "Pago aprobado", "Orden enviada a logística", "En alistamiento",
    "Empacado", "Listo para despacho", "Despachado", "En tránsito",
    "En ruta de entrega", "Entregado",
]
ESTADOS_CON_TRANSPORTE = ORDEN_ESTADOS[6:]
CIUDADES = {
    "bogota": "Bogotá D.C.", "bogota dc": "Bogotá D.C.", "bogota d.c.": "Bogotá D.C.",
    "cali": "Cali", "medellin": "Medellín", "barranquilla": "Barranquilla",
    "bucaramanga": "Bucaramanga", "pereira": "Pereira",
}


class Decisiones:
    def __init__(self):
        self.filas = []

    def add(self, tabla, columna, problema, cantidad, accion, justificacion):
        self.filas.append(dict(tabla=tabla, columna=columna, problema=problema,
                               registros_afectados=int(cantidad), accion=accion,
                               justificacion=justificacion))

    def df(self):
        d = pd.DataFrame(self.filas)
        return d[d["registros_afectados"] > 0].reset_index(drop=True)


# ---------- utilidades ----------
def _clave(x):
    """minúsculas, sin tildes, sin espacios repetidos (para detectar variantes)."""
    if pd.isna(x):
        return x
    x = unicodedata.normalize("NFKD", str(x)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", x).strip().lower()


def _limpiar_texto(df, tabla, dec):
    nulos_txt = {"", "nan", "none", "null", "n/a", "na", "s/d", "-"}
    for c in df.select_dtypes(include=["object", "string"]).columns:
        s = df[c].astype("string").str.replace(r"\s+", " ", regex=True).str.strip()
        vacios = s.str.lower().isin(nulos_txt) & s.notna()
        cambia = int((s.fillna("") != df[c].astype("string").fillna("")).sum())
        s = s.mask(vacios)
        df[c] = s.astype(object).where(s.notna(), np.nan)
        if cambia or vacios.sum():
            dec.add(tabla, c, "Espacios sobrantes / textos vacíos como 'N/A'", cambia + vacios.sum(),
                    "strip + espacios simples; vacíos -> NaN", "Evita categorías falsas por espacios y nulos disfrazados")
    return df


def _estandarizar_categoria(df, col, tabla, dec, canon=None):
    if col not in df.columns:
        return df
    claves = df[col].map(_clave)
    if canon:
        nuevo = claves.map(canon).fillna(df[col])
    else:
        frec = df.assign(_k=claves).groupby(["_k", col]).size().reset_index(name="n")
        mejor = frec.sort_values("n", ascending=False).drop_duplicates("_k").set_index("_k")[col]
        nuevo = claves.map(mejor)
    cambios = int((nuevo.fillna("") != df[col].fillna("")).sum())
    antes = df[col].nunique()
    df[col] = nuevo
    if cambios:
        dec.add(tabla, col, f"Variantes de escritura ({antes} -> {df[col].nunique()} categorías)", cambios,
                "Unificar mayúsculas/tildes a la forma canónica", "Una misma categoría no puede tener varias etiquetas")
    return df


# =====================  SILVER LOGÍSTICA  =====================
def silver_logistica(bronze: pd.DataFrame, dec: Decisiones) -> pd.DataFrame:
    t = "logistica"
    df = bronze.copy()

    # 1. columna basura
    basura = [c for c in df.columns if str(c).startswith("Unnamed")]
    if basura:
        dec.add(t, ",".join(basura), "Columna sin nombre con una fórmula residual de Excel (=AI(\"\"))",
                int(df[basura].notna().sum().sum()), "Eliminar columna", "No pertenece al modelo de datos; 99,998% nula")
        df = df.drop(columns=basura)

    df = _limpiar_texto(df, t, dec)

    # 2. duplicados
    n = len(df)
    df = df.drop_duplicates()
    dec.add(t, "(fila completa)", "Filas completamente duplicadas", n - len(df),
            "drop_duplicates()", "Un evento no puede registrarse dos veces con el mismo contenido")
    n = len(df)
    # evento_id repetido con contenido distinto (registro con nulos vs. completo): conservar el más completo
    df = (df.assign(_nn=df.notna().sum(axis=1)).sort_values(["evento_id", "_nn"], ascending=[True, False])
            .drop_duplicates("evento_id").drop(columns="_nn"))
    dec.add(t, "evento_id", "evento_id repetido con contenido diferente", n - len(df),
            "Conservar la fila con menos nulos", "evento_id debe ser único; la fila más completa es la más confiable")

    # 3. tipos
    for c in ["fecha_evento", "fecha_prometida_entrega"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    df["evento_id"] = df["evento_id"].astype("int64")
    dec.add(t, "fecha_evento, fecha_prometida_entrega", "Fechas leídas como texto", len(df),
            "Convertir a datetime", "Permite cálculos de tiempo y rangos")

    df["_orden"] = df["estado_evento"].map({e: i for i, e in enumerate(ORDEN_ESTADOS)})
    df = df.sort_values(["pedido_id", "_orden", "evento_id"]).reset_index(drop=True)
    g = df.groupby("pedido_id")

    # 4. atributos constantes por pedido -> completar con el valor del mismo pedido
    for c, motivo in [("ciudad_destino", "El destino es único por pedido"),
                      ("centro_logistico", "El CEDI es único por pedido"),
                      ("fecha_prometida_entrega", "La fecha prometida es única por pedido"),
                      ("costo_envio", "El costo de envío es único por pedido")]:
        faltan = int(df[c].isna().sum())
        if faltan:
            df[c] = df[c].fillna(g[c].transform(lambda s: s.dropna().iloc[0] if s.notna().any() else np.nan))
            dec.add(t, c, "Nulo accidental (el atributo existe en otros eventos del mismo pedido)", faltan - df[c].isna().sum(),
                    "Imputar con el valor del mismo pedido_id", motivo + " (verificado: 0 pedidos con valores distintos)")
    # centro_logistico restante: derivar de ciudad ("CEDI " + ciudad)
    resto = df["centro_logistico"].isna() & df["ciudad_destino"].notna()
    if resto.any():
        base = df["ciudad_destino"].str.replace(" D.C.", "", regex=False)
        df.loc[resto, "centro_logistico"] = "CEDI " + base[resto]
        dec.add(t, "centro_logistico", "Nulo sin otro evento del pedido", int(resto.sum()),
                "Derivar como 'CEDI ' + ciudad_destino", "Regla observada en el 100% de los datos completos")

    # transportadora / guía: son nulas ANTES del despacho (normal); después del despacho es error
    g = df.groupby("pedido_id")
    despachado = df["estado_evento"].isin(ESTADOS_CON_TRANSPORTE)
    for c in ["transportadora", "numero_guia"]:
        falta = despachado & df[c].isna()
        if falta.any():
            df.loc[falta, c] = g[c].transform(lambda s: s.dropna().iloc[0] if s.notna().any() else np.nan)[falta]
            dec.add(t, c, "Nulo en estado posterior al despacho (debería existir)", int(falta.sum()),
                    "Imputar con el valor del mismo pedido", "Una guía/transportadora se asigna una sola vez por pedido")
        previos = int((~despachado & df[c].isna()).sum())
        dec.add(t, c, "Nulo antes del despacho (comportamiento normal del proceso)", previos,
                "Mantener nulo", "Aún no hay transportadora/guía asignada; imputar crearía información falsa")

    # 5. fecha_evento: reconstruir con fecha_anterior + tiempo_etapa_horas
    faltan0 = int(df["fecha_evento"].isna().sum())
    g = df.groupby("pedido_id")
    for _ in range(5):
        td = pd.to_timedelta(df["tiempo_etapa_horas"], unit="h")
        prev = g["fecha_evento"].shift(1) + td
        sig = g["fecha_evento"].shift(-1) - pd.to_timedelta(g["tiempo_etapa_horas"].shift(-1), unit="h")
        df["fecha_evento"] = df["fecha_evento"].fillna(prev).fillna(sig)
        if df["fecha_evento"].isna().sum() == 0:
            break
    dec.add(t, "fecha_evento", "Fecha del evento nula", faltan0 - df["fecha_evento"].isna().sum(),
            "fecha = fecha del evento anterior + tiempo_etapa_horas (o siguiente - su tiempo)",
            "tiempo_etapa_horas es el tiempo desde el evento anterior; es mejor que usar media/mediana de fechas")

    # 6. tiempo_etapa_horas nulo = primer evento ('Pedido recibido'): no hay etapa previa
    es_primero = df["estado_evento"].eq("Pedido recibido")
    dec.add(t, "tiempo_etapa_horas", "Nulo en 'Pedido recibido' (no existe etapa anterior)",
            int((df["tiempo_etapa_horas"].isna() & es_primero).sum()),
            "Mantener nulo", "Nulo con interpretación válida: se mide el tiempo entre etapas")
    anom = df["tiempo_etapa_horas"].isna() & ~es_primero
    if anom.any():
        med = df.groupby("estado_evento")["tiempo_etapa_horas"].transform("median")
        df.loc[anom, "tiempo_etapa_horas"] = med[anom]
        dec.add(t, "tiempo_etapa_horas", "Nulo en una etapa que sí tiene tiempo", int(anom.sum()),
                "Mediana por estado_evento", "Distribución sesgada a la derecha -> mediana, no media")

    # 7. incidencia / observación: nulo = no hubo incidencia
    for c, etiqueta in [("incidencia", "SIN INCIDENCIA"), ("observacion", "SIN OBSERVACIÓN")]:
        k = int(df[c].isna().sum())
        df[c] = df[c].fillna(etiqueta)
        dec.add(t, c, "Nulo = el evento no tuvo novedad", k, f"Reemplazar por '{etiqueta}'",
                "Categoría explícita para poder contar/filtrar eventos sin novedad")

    # 8. categorías
    for c in ["estado_evento", "centro_logistico", "ciudad_destino", "transportadora"]:
        df = _estandarizar_categoria(df, c, t, dec)
    df["costo_envio"] = df["costo_envio"].astype("int64")

    # 9. validaciones sin modificar (solo reporte)
    inc = int((df["fecha_prometida_entrega"] < df["fecha_evento"]).sum())
    dec.add(t, "fecha_prometida_entrega", "Eventos posteriores a la fecha prometida", inc,
            "Solo se documenta (no se corrige)", "Es un retraso real del negocio, no un error de captura")
    df = df.drop(columns="_orden").sort_values("evento_id").reset_index(drop=True)
    return df


# =====================  SILVER VENTAS  =====================
COLS_NUM_VENTAS = ["cantidad", "precio_unitario", "valor_bruto", "valor_descuento", "valor_neto",
                   "calificacion_cliente"]


def silver_ventas(bronze: pd.DataFrame, dec: Decisiones) -> pd.DataFrame:
    t = "ventas"
    df = bronze.copy()
    df.columns = [re.sub(r"\s+", "_", str(c).strip().lower()) for c in df.columns]
    df = _limpiar_texto(df, t, dec)

    # duplicados
    n = len(df)
    df = df.drop_duplicates()
    dec.add(t, "(fila completa)", "Filas completamente duplicadas", n - len(df), "drop_duplicates()",
            "Una venta no puede registrarse dos veces idéntica")
    for idc in [c for c in ["id_venta"] if c in df.columns]:
        n = len(df)
        df = (df.assign(_nn=df.notna().sum(axis=1)).sort_values([idc, "_nn"], ascending=[True, False])
                .drop_duplicates(idc).drop(columns="_nn"))
        dec.add(t, idc, f"{idc} repetido con contenido distinto", n - len(df),
                "Conservar la fila más completa", f"{idc} debe ser único")

    # tipos
    for c in [c for c in df.columns if "fecha" in c]:
        bad = df[c].notna().sum()
        df[c] = pd.to_datetime(df[c], errors="coerce")
        dec.add(t, c, "Fecha como texto/objeto", int(bad), "Convertir a datetime (inválidas -> NaT)",
                "Permite filtrar y calcular periodos")
    for c in [c for c in COLS_NUM_VENTAS if c in df.columns]:
        if not pd.api.types.is_numeric_dtype(df[c]):
            antes = df[c].notna().sum()
            df[c] = pd.to_numeric(df[c].astype("string").str.replace(r"[$\s]", "", regex=True), errors="coerce")
            dec.add(t, c, "Numérica leída como texto", int(antes), "to_numeric(errors='coerce')",
                    "Necesaria para estadísticas y sumas")
        else:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # categorías
    if "ciudad" in df.columns:
        df = _estandarizar_categoria(df, "ciudad", t, dec, canon=CIUDADES)
    cat_cols = [c for c in df.select_dtypes(include="object").columns
                if not (c.startswith("id_") or c.endswith("_id") or "fecha" in c) and df[c].nunique() <= 60]
    for c in cat_cols:
        if c != "ciudad":
            df = _estandarizar_categoria(df, c, t, dec)

    # valores imposibles
    for c in ["cantidad", "precio_unitario", "valor_bruto", "valor_neto"]:
        if c in df.columns:
            neg = df[c] <= 0
            if neg.any():
                dec.add(t, c, "Valores <= 0 (imposibles en una venta)", int(neg.sum()), "Convertir a NaN y reimputar",
                        "Un valor no positivo no es una venta válida")
                df.loc[neg, c] = np.nan
    if "calificacion_cliente" in df.columns:
        fuera = df["calificacion_cliente"].notna() & ~df["calificacion_cliente"].between(1, 5)
        if fuera.any():
            dec.add(t, "calificacion_cliente", "Calificaciones fuera de la escala 1-5", int(fuera.sum()),
                    "Convertir a NaN", "Valor fuera de rango")
            df.loc[fuera, "calificacion_cliente"] = np.nan

    # nulos con regla de negocio (valor_bruto = cantidad * precio_unitario ; neto = bruto - descuento)
    def has(*c): return all(x in df.columns for x in c)
    if has("precio_unitario", "cantidad", "valor_bruto"):
        k = df["precio_unitario"].isna() & df["valor_bruto"].notna() & df["cantidad"].notna()
        df.loc[k, "precio_unitario"] = df.loc[k, "valor_bruto"] / df.loc[k, "cantidad"]
        if k.sum(): dec.add(t, "precio_unitario", "Nulo recuperable", int(k.sum()), "valor_bruto / cantidad",
                            "Relación aritmética exacta")
        k = df["valor_bruto"].isna() & df["cantidad"].notna() & df["precio_unitario"].notna()
        df.loc[k, "valor_bruto"] = df.loc[k, "cantidad"] * df.loc[k, "precio_unitario"]
        if k.sum(): dec.add(t, "valor_bruto", "Nulo recuperable", int(k.sum()), "cantidad * precio_unitario",
                            "Relación aritmética exacta")
    if has("valor_bruto", "valor_descuento", "valor_neto"):
        k = df["valor_descuento"].isna() & df["valor_bruto"].notna() & df["valor_neto"].notna()
        df.loc[k, "valor_descuento"] = df.loc[k, "valor_bruto"] - df.loc[k, "valor_neto"]
        if k.sum(): dec.add(t, "valor_descuento", "Nulo recuperable", int(k.sum()), "valor_bruto - valor_neto",
                            "Relación aritmética exacta")
        k = df["valor_descuento"].isna()
        df.loc[k, "valor_descuento"] = 0
        if k.sum(): dec.add(t, "valor_descuento", "Nulo sin forma de recuperarlo", int(k.sum()), "Imputar 0",
                            "Nulo en descuento = venta sin descuento")
        k = df["valor_neto"].isna() & df["valor_bruto"].notna()
        df.loc[k, "valor_neto"] = df.loc[k, "valor_bruto"] - df.loc[k, "valor_descuento"]
        if k.sum(): dec.add(t, "valor_neto", "Nulo recuperable", int(k.sum()), "valor_bruto - valor_descuento",
                            "Relación aritmética exacta")
        # flags de inconsistencia (se documentan, no se sobreescriben)
        df["flag_neto_inconsistente"] = ((df["valor_bruto"] - df["valor_descuento"] - df["valor_neto"]).abs() > 1)
        dec.add(t, "valor_neto", "valor_neto != bruto - descuento", int(df["flag_neto_inconsistente"].sum()),
                "Marcar con flag_neto_inconsistente (sin corregir)", "Requiere validación con el área comercial")
    if has("cantidad", "precio_unitario", "valor_bruto"):
        df["flag_bruto_inconsistente"] = ((df["cantidad"] * df["precio_unitario"] - df["valor_bruto"]).abs() > 1)
        dec.add(t, "valor_bruto", "valor_bruto != cantidad*precio_unitario", int(df["flag_bruto_inconsistente"].sum()),
                "Marcar con flag_bruto_inconsistente (sin corregir)", "Requiere validación con el área comercial")

    # nulos restantes: numéricas -> mediana (sesgo por atípicos) ; categóricas -> NO INFORMADO
    for c in df.columns:
        if df[c].isna().any() and not c.startswith(("id_", "flag_")) and not c.endswith("_id") and "fecha" not in c:
            k = int(df[c].isna().sum())
            if c == "calificacion_cliente":
                dec.add(t, c, "Nulo: el cliente no calificó", k, "Mantener nulo",
                        "Ausencia de calificación es información válida; imputar sesgaría la satisfacción")
            elif pd.api.types.is_numeric_dtype(df[c]):
                df[c] = df[c].fillna(df[c].median())
                dec.add(t, c, "Nulos en variable numérica", k, "Imputar con la mediana",
                        "Robusta a valores atípicos")
            else:
                df[c] = df[c].fillna("NO INFORMADO")
                dec.add(t, c, "Nulos en variable categórica", k, "Imputar 'NO INFORMADO'",
                        "No se inventa una categoría (la moda distorsionaría la distribución)")
    return df.reset_index(drop=True)


# =====================  GOLD  =====================
def gold_pedidos(ventas_s: pd.DataFrame, logistica_s: pd.DataFrame, dec: Decisiones) -> pd.DataFrame:
    """Una fila por pedido: ventas + resumen logístico (integración por pedido_id)."""
    l = logistica_s.copy()
    l["_o"] = l["estado_evento"].map({e: i for i, e in enumerate(ORDEN_ESTADOS)})
    l = l.sort_values(["pedido_id", "_o", "fecha_evento"])
    ult = l.groupby("pedido_id").tail(1).set_index("pedido_id")
    ent = l[l["estado_evento"] == "Entregado"].groupby("pedido_id")["fecha_evento"].min()
    agg = l.groupby("pedido_id").agg(
        n_eventos=("evento_id", "count"), n_estados_distintos=("estado_evento", "nunique"),
        fecha_primer_evento=("fecha_evento", "min"), fecha_ultimo_evento=("fecha_evento", "max"),
        horas_totales_proceso=("tiempo_etapa_horas", "sum"),
        n_incidencias=("incidencia", lambda s: int((s != "SIN INCIDENCIA").sum())),
        centro_logistico=("centro_logistico", "first"), ciudad_destino=("ciudad_destino", "first"),
        transportadora=("transportadora", lambda s: s.dropna().iloc[0] if s.notna().any() else np.nan),
        numero_guia=("numero_guia", lambda s: s.dropna().iloc[0] if s.notna().any() else np.nan),
        costo_envio=("costo_envio", "first"), fecha_prometida_entrega=("fecha_prometida_entrega", "first"),
    )
    agg["estado_final"] = ult["estado_evento"]
    agg["fecha_entrega"] = ent
    agg["entregado"] = agg["fecha_entrega"].notna()
    agg["entrega_a_tiempo"] = np.where(agg["entregado"], agg["fecha_entrega"] <= agg["fecha_prometida_entrega"], np.nan)
    agg["dias_hasta_entrega"] = (agg["fecha_entrega"] - agg["fecha_primer_evento"]).dt.total_seconds() / 86400
    agg["pedido_completo"] = agg["n_estados_distintos"] == len(ORDEN_ESTADOS)
    agg = agg.reset_index()
    if ventas_s is None:   # sin ventas disponibles: Gold solo con el resumen logístico por pedido
        dec.add("gold", "pedido_id", "Ventas no disponibles: Gold generado solo con resumen logístico", len(agg),
                "Resumen por pedido sin cruce", "Se completa al ejecutar con acceso a MySQL")
        return agg
    gold = ventas_s.merge(agg, on="pedido_id", how="outer", indicator="_origen")
    huerfanos = gold["_origen"].value_counts().to_dict()
    dec.add("gold", "pedido_id", f"Cruce ventas-logística: {huerfanos}", int((gold['_origen'] != 'both').sum()),
            "Outer join para conservar y medir pedidos sin contraparte", "Pedidos sin match indican problemas de integración")
    return gold.drop(columns="_origen")
