"""Carga inicial (idempotente) de datos desde los Excel de la tesis hacia SQLite.

Se apoya en posiciones de columna fijas (no en texto de encabezado) porque ambos
Excel tienen encabezados fuera de la fila 1 y texto con acentos/saltos de línea
que conviene no usar como clave de matching.
"""
from pathlib import Path
import openpyxl

import db

BASE_DIR = Path(__file__).parent
ARCHIVO_ABC = BASE_DIR / "Clasificacion_ABC_Multicriterio_SIMET-USACH_1.xlsx"
ARCHIVO_CONSUMO = BASE_DIR / "Ficha_Consumo_Operaciones_SIMET-USACH_2.xlsx"

HOJA_ABC = "Clasificación ABC Multicriterio"
FILA_HEADER_ABC = 11
FILA_INICIO_ABC = 13  # fila 12 es el ejemplo, se excluye

HOJA_CONSUMO = "Ficha de Consumo"
FILA_INICIO_CONSUMO = 4


def _seed_insumos(conn):
    wb = openpyxl.load_workbook(ARCHIVO_ABC, data_only=True)
    ws = wb[HOJA_ABC]
    filas = []
    for row in ws.iter_rows(min_row=FILA_INICIO_ABC, max_row=ws.max_row):
        id_val = row[0].value  # col A
        nombre = row[1].value  # col B
        if id_val is None or nombre is None or str(nombre).strip() == "":
            continue
        categoria = row[2].value  # col C
        costo = row[3].value  # col D
        frecuencia = row[4].value  # col E
        impacto = row[5].value  # col F
        tiempo_rep = row[6].value  # col G
        filas.append((int(id_val), str(nombre).strip(), categoria, costo, frecuencia, impacto, tiempo_rep))

    for id_val, nombre, categoria, costo, frecuencia, impacto, tiempo_rep in filas:
        conn.execute(
            """
            INSERT INTO insumos (id, nombre, categoria, costo_unitario, frecuencia_uso_mensual,
                                  impacto_operacional, tiempo_reposicion_dias)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET nombre = excluded.nombre
            """,
            (id_val, nombre, categoria, costo, frecuencia, impacto, tiempo_rep),
        )
    conn.commit()
    return len(filas)


def _seed_consumo_operaciones(conn):
    existentes = conn.execute("SELECT COUNT(*) AS n FROM consumo_operaciones").fetchone()["n"]
    if existentes > 0:
        return existentes

    wb = openpyxl.load_workbook(ARCHIVO_CONSUMO, data_only=True)
    ws = wb[HOJA_CONSUMO]
    filas = []
    for row in ws.iter_rows(min_row=FILA_INICIO_CONSUMO, max_row=ws.max_row):
        operacion = row[0].value  # A
        insumo = row[1].value  # B
        if operacion is None and insumo is None:
            continue
        unidad = row[2].value  # C
        costo = row[3].value  # D
        unidades_cambio = row[4].value  # E
        costo_cambio = row[5].value  # F
        rendimiento = row[6].value  # G
        costo_probeta = row[7].value  # H
        fuente = row[8].value  # I
        filas.append((operacion, insumo, unidad, costo, unidades_cambio, costo_cambio, rendimiento, costo_probeta, fuente))

    conn.executemany(
        """
        INSERT INTO consumo_operaciones (operacion, insumo, unidad, costo_unitario, unidades_por_cambio,
                                          costo_por_cambio, rendimiento_probetas, costo_por_probeta, fuente_dato)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        filas,
    )
    conn.commit()
    return len(filas)


def seed():
    conn = db.get_connection()
    db.init_schema(conn)
    n_insumos = _seed_insumos(conn)
    n_consumo = _seed_consumo_operaciones(conn)
    conn.close()
    return n_insumos, n_consumo


if __name__ == "__main__":
    n_insumos, n_consumo = seed()
    print(f"Insumos cargados/actualizados: {n_insumos}")
    print(f"Filas de consumo por operación cargadas: {n_consumo}")
