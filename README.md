# Laboratorio Práctico de ETL — Kaismart Solutions

## 📌 Descripción

Este repositorio contiene el desarrollo del **Laboratorio Práctico de ETL**, realizado en Python sobre información comercial y logística de **Kaismart Solutions S.A.S.**

El proyecto tiene como propósito desarrollar un proceso de **extracción, exploración, evaluación de calidad, transformación e integración de datos**, utilizando la metodología **Medallion Architecture**, con las capas **Bronze, Silver y Gold**.

Las fuentes de información corresponden a:

* Una base de datos **MySQL** con información de ventas.
* Un archivo **Excel** con eventos logísticos.

El proceso permite analizar inicialmente la estructura y calidad de cada fuente, identificar problemas en los datos y posteriormente generar conjuntos de datos depurados e integrados para su análisis.

---
# Laboratorio ETL – Kaismart Solutions S.A.S. (UAO)

**Autor:** Juan Sebastián Sánchez Urbano · juan_s.sanchez_u@uao.edu.co · Maestría en Ciencia de Datos e IA

Arquitectura **Medallion**: Bronze (crudo) → Silver (limpio) → Gold (integrado por pedido).

## Estructura
```
config.yaml            # autores, credenciales MySQL, rutas, hora del scheduler
scheduler.py           # PARTE 8: orquestador con la librería schedule
etl/                   # extract.py, profiling.py (EDA), transform.py (Silver/Gold), pipeline.py
notebooks/laboratorio_etl.ipynb  
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
`data/bronze`, `data/silver` y `data/gold` ya vienen pobladas (ventas + logística + Gold integrado).
`data/respaldo/ventas_mysql_export.csv` es una exportación de la tabla `ventas`: el pipeline intenta primero MySQL y,
solo si no hay conexión, usa ese archivo (configurable en `config.yaml -> ventas_csv_respaldo`).
Al ejecutar con acceso a MySQL, todas las capas se regeneran con la extracción en vivo.

## 🎯 Objetivo

Desarrollar en Python un proceso ETL que permita:

* Extraer información desde una base de datos MySQL.
* Extraer información desde un archivo Excel.
* Convertir las fuentes en DataFrames de pandas.
* Realizar una exploración inicial de los datasets.
* Evaluar la calidad de los datos.
* Identificar valores nulos, duplicados, cardinalidad y tipos de datos.
* Realizar análisis estadístico y descriptivo.
* Formular y responder preguntas de negocio.
* Limpiar y transformar los datos.
* Integrar la información comercial y logística.
* Implementar una arquitectura Medallion.
* Automatizar el pipeline ETL utilizando `Schedule`.

---

## 🏢 Contexto del proyecto

**Kaismart Solutions S.A.S.** es una empresa dedicada a la comercialización de productos de tecnología, hogar, oficina, electrodomésticos y deportes en diferentes ciudades de Colombia.

La empresa comercializa sus productos mediante diferentes canales, entre ellos tiendas físicas, página web y aplicación móvil.

La información utilizada en este laboratorio se encuentra distribuida en dos fuentes independientes:

### Fuente comercial

La información de ventas se encuentra almacenada en una base de datos relacional **MySQL**, específicamente en la base de datos `clientes` y la tabla `ventas`.

Esta fuente contiene aproximadamente **5.000 registros de ventas**.

### Fuente logística

La información logística se encuentra almacenada en el archivo:

```text
kaismart_eventos_logisticos.xlsx
```

Este archivo contiene aproximadamente **50.000 registros de eventos logísticos**.

Ambas fuentes comparten la variable:

```text
pedido_id
```

Esta variable permite realizar posteriormente la integración entre la información comercial y logística.

---

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

---

## 🥉 Arquitectura Medallion

El proyecto utiliza una arquitectura de datos basada en tres capas.

### 🥉 Bronze

La capa Bronze conserva los datos obtenidos directamente desde las fuentes originales.

Contiene los datos sin aplicar procesos de limpieza o transformación significativa.

```text
data/
└── bronze/
    ├── ventas_raw.csv
    └── logistica_raw.csv
```

### 🥈 Silver

La capa Silver contiene los datos después de aplicar los procesos de limpieza y transformación necesarios.

Entre los tratamientos considerados se encuentran:

* Manejo de valores nulos.
* Eliminación de duplicados cuando corresponda.
* Estandarización de categorías.
* Corrección de tipos de datos.
* Transformaciones necesarias para el análisis.
* Tratamiento de inconsistencias identificadas durante el EDA.

Las decisiones de imputación se realizan teniendo en cuenta el significado de cada variable y no de manera automática.

```text
data/
└── silver/
    ├── ventas_silver.csv
    └── logistica_silver.csv
```

### 🥇 Gold

La capa Gold contiene los datos preparados para análisis, después de realizar la integración entre las fuentes comercial y logística.

La integración utiliza como elemento común:

```text
pedido_id
```

```text
data/
└── gold/
    └── pedidos_gold.csv
```

---

## 📊 Exploración y análisis de datos

Antes de realizar transformaciones, se realiza un proceso de **Exploratory Data Analysis (EDA)** sobre cada fuente de manera independiente.

Para cada DataFrame se analizan aspectos como:

* Número de registros.
* Número de variables.
* Nombres de las variables.
* Tipos de datos.
* Registros no nulos.
* Variables identificadoras.
* Variables categóricas.
* Variables numéricas.
* Variables asociadas con fechas y tiempos.
* Rango de fechas cuando sea posible.
* Características generales de calidad.

Los principales DataFrames utilizados durante la extracción son:

```python
df_ventas
df_logistica
```

Posteriormente se generan los DataFrames transformados:

```python
df_ventas_transformado
df_logistica_transformado
```

---

## 🔎 Perfil de calidad de los datos

El perfil inicial de calidad permite identificar y cuantificar posibles problemas presentes en las fuentes.

### Valores nulos

Para cada variable se determina:

* Cantidad de valores nulos.
* Porcentaje de valores nulos.
* Variables con mayor proporción de datos faltantes.
* Posibles causas de los valores faltantes.

Durante esta etapa los valores nulos se identifican y analizan, pero no se modifican hasta la etapa de transformación.

### Valores únicos

Se utiliza `nunique()` para analizar:

* Cardinalidad.
* Variables con alta cardinalidad.
* Variables con baja cardinalidad.
* Posibles identificadores.
* Variables categóricas con pocos valores.

Se presta especial atención a:

```text
id_venta
pedido_id
evento_id
```

### Duplicados

Se revisan:

* Filas completamente duplicadas.
* Identificadores que deberían ser únicos.
* Registros repetidos.

Los duplicados encontrados son documentados antes de decidir el tratamiento correspondiente.

### Tipos de datos

Se verifica la coherencia entre el tipo de dato detectado por Python y el significado de cada variable.

Se presta especial atención a:

* Fechas.
* Identificadores.
* Variables monetarias.
* Variables numéricas.
* Variables categóricas.

---

## 📈 Análisis descriptivo

El proyecto contempla un análisis descriptivo independiente de las fuentes antes de realizar la integración.

Para las variables numéricas se consideran indicadores como:

* `count`
* `mean`
* `std`
* `min`
* Percentil 25
* Mediana
* Percentil 75
* `max`

También se analizan las variables categóricas mediante:

* Número de valores únicos.
* Categorías existentes.
* Frecuencia de cada categoría.
* Categoría más frecuente.

### Información de ventas

Para `df_ventas` se analizan, entre otros:

* Ventas por ciudad.
* Ventas por canal.
* Ventas por categoría.
* Cantidad de productos vendidos.
* `precio_unitario`.
* `valor_bruto`.
* `valor_descuento`.
* `valor_neto`.
* `calificacion_cliente`.

### Información logística

Para `df_logistica` se analizan, entre otros:

* Eventos por `estado_evento`.
* Eventos por `ciudad_destino`.
* Frecuencia de transportadoras.
* Frecuencia de incidencias.
* `tiempo_etapa_horas`.
* `costo_envio`.

---

## 💼 Preguntas de negocio

Como parte del análisis inicial se plantean y responden **10 preguntas de negocio** utilizando los datos originales.

Estas preguntas buscan aprovechar las capacidades de análisis de `pandas` para obtener información relevante a partir de las fuentes disponibles.

Las preguntas y respuestas serán documentadas dentro del análisis del proyecto.

---

## 🧹 Proceso de transformación

A partir de los problemas identificados durante el EDA se desarrolla el proceso de limpieza y transformación.

Los tratamientos pueden incluir:

* Imputación de valores faltantes.
* Eliminación de duplicados.
* Estandarización de categorías.
* Conversión de tipos de datos.
* Tratamiento de inconsistencias.
* Creación o modificación de variables cuando sea necesario.
* Preparación de los datos para la integración.

Las estrategias de imputación se seleccionan de acuerdo con las características de cada variable.

Entre las alternativas consideradas se encuentran:

* **Mediana:** para variables numéricas con presencia de valores atípicos.
* **Media:** cuando la distribución de la variable lo permita.
* **Moda:** para variables categóricas.
* **"NO INFORMADO":** cuando sea apropiado.
* **Mantener el nulo:** cuando represente una situación válida del proceso.

---

## ⚙️ Automatización del ETL

El pipeline ETL será automatizado utilizando la librería:

```text
Schedule
```

El objetivo es establecer un proceso que permita ejecutar de manera programada las diferentes etapas del pipeline ETL.

El proceso contempla las etapas principales de:

```text
Extracción
     ↓
Transformación
     ↓
Integración
     ↓
Generación de datos procesados
```

La automatización forma parte del alcance establecido para el laboratorio.

---

## 🛠️ Tecnologías utilizadas

Las principales tecnologías y herramientas utilizadas son:

| Tecnología       | Uso                                   |
| ---------------- | ------------------------------------- |
| Python           | Desarrollo del proceso ETL            |
| Pandas           | Manipulación y análisis de datos      |
| MySQL            | Fuente de datos comerciales           |
| Excel            | Fuente de datos logísticos            |
| Schedule         | Automatización del pipeline           |
| YAML             | Configuración del proyecto            |
| Jupyter Notebook | Exploración y análisis de datos       |
| Git              | Control de versiones                  |
| GitHub           | Gestión y publicación del repositorio |

---

## 📁 Estructura del repositorio

```text
lab2-etl/
│
├── README.md
├── config.yaml
├── requirements.txt
│
├── data/
│   ├── bronze/
│   │   ├── ventas_raw.csv
│   │   └── logistica_raw.csv
│   │
│   ├── silver/
│   │   ├── ventas_silver.csv
│   │   └── logistica_silver.csv
│   │
│   └── gold/
│       └── pedidos_gold.csv
│
├── etl/
│   ├── __init__.py
│   ├── extraction.py
│   ├── transformation.py
│   ├── quality.py
│   └── pipeline.py
│
├── notebooks/
│   └── EDA.ipynb
│
└── reports/
    └── informe.md
```

> **Nota:** La estructura puede modificarse de acuerdo con la organización final del proyecto.

---

## 🔐 Configuración y credenciales

Por seguridad, **no se deben almacenar contraseñas ni credenciales reales de la base de datos dentro del repositorio público**.

El archivo `config.yaml` puede utilizarse para almacenar información de configuración no sensible, como los nombres de los autores y parámetros generales del proyecto.

Las credenciales deberían manejarse mediante variables de entorno o un archivo local incluido en `.gitignore`.

Ejemplo:

```yaml
autores:
  - Juan Sebastián Sánchez Urbano

database:
  host: localhost
  port: 3306
  database: clientes
```

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
```

### 2. Ingresar al proyecto

```bash
cd lab2-etl
```

### 3. Crear un entorno virtual

```bash
python -m venv venv
```

### 4. Activar el entorno virtual

En Windows:

```bash
venv\Scripts\activate
```

En Linux/macOS:

```bash
source venv/bin/activate
```

### 5. Instalar las dependencias

```bash
pip install -r requirements.txt
```

---

## ▶️ Ejecución

El proceso puede ejecutarse siguiendo las diferentes etapas del pipeline:

```text
1. Extracción
2. Exploración
3. Evaluación de calidad
4. Transformación
5. Integración
6. Generación de datos Gold
7. Automatización
```

El punto de entrada del pipeline dependerá de la implementación final del proyecto.

---

## 📋 Resultados esperados

Al finalizar el laboratorio se espera contar con:

* DataFrame `df_ventas`.
* DataFrame `df_logistica`.
* DataFrames transformados.
* Perfil de calidad de ambas fuentes.
* Análisis exploratorio de datos.
* Análisis descriptivo.
* Identificación y tratamiento de problemas de calidad.
* Datos organizados bajo la metodología Medallion.
* Datos integrados en la capa Gold.
* Respuestas a 10 preguntas de negocio.
* Pipeline ETL automatizado.
* Conclusiones sobre los principales hallazgos encontrados.

---

## 📌 Hallazgos

Esta sección será actualizada después de ejecutar el proceso completo de EDA y transformación.

Se documentarán como mínimo:

### Ventas

* Hallazgo 1.
* Hallazgo 2.
* Hallazgo 3.
* Hallazgo 4.
* Hallazgo 5.

### Logística

* Hallazgo 1.
* Hallazgo 2.
* Hallazgo 3.
* Hallazgo 4.
* Hallazgo 5.

### Transformación

Se documentarán los principales cambios realizados sobre los datos y la justificación de las decisiones tomadas.

---

## 📚 Fuente del laboratorio

Este proyecto se desarrolla con base en el **Laboratorio Práctico de ETL — Kaismart Solutions S.A.S.**

El laboratorio establece como alcance la extracción, exploración, evaluación de calidad, transformación e integración de las fuentes mediante metodología Medallion, además de la automatización del proceso ETL.

---
