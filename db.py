"""Conexión y esquema SQLite para el control de insumos críticos."""
import sqlite3
from pathlib import Path
from datetime import datetime, date

DB_PATH = Path(__file__).parent / "data" / "insumos.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS insumos (
    id INTEGER PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    categoria TEXT,
    unidad TEXT,
    costo_unitario REAL,
    frecuencia_uso_mensual REAL,
    impacto_operacional INTEGER,
    tiempo_reposicion_dias REAL,
    puntaje_ponderado REAL,
    clase_abc TEXT CHECK (clase_abc IN ('A','B','C') OR clase_abc IS NULL),
    stock_actual REAL NOT NULL DEFAULT 0,
    stock_minimo REAL NOT NULL DEFAULT 0,
    proveedor TEXT
);

CREATE TABLE IF NOT EXISTS movimientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insumo_id INTEGER NOT NULL REFERENCES insumos(id),
    tipo TEXT CHECK (tipo IN ('ingreso','egreso')) NOT NULL,
    cantidad REAL NOT NULL,
    fecha TEXT NOT NULL,
    proveedor TEXT,
    ensayo_ot TEXT,
    responsable TEXT,
    observacion TEXT,
    creado_en TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consumo_operaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operacion TEXT,
    insumo TEXT,
    unidad TEXT,
    costo_unitario REAL,
    unidades_por_cambio REAL,
    costo_por_cambio REAL,
    rendimiento_probetas REAL,
    costo_por_probeta REAL,
    fuente_dato TEXT
);
"""

CATEGORIAS = [
    "Consumible de ensayo",
    "Rendimiento múltiple (herramienta)",
    "EPP-Seguridad",
    "Insumo general",
]


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn):
    conn.executescript(SCHEMA)
    conn.commit()


def db_exists():
    return DB_PATH.exists()


def list_insumos(conn):
    return conn.execute(
        "SELECT * FROM insumos ORDER BY "
        "CASE clase_abc WHEN 'A' THEN 1 WHEN 'B' THEN 2 WHEN 'C' THEN 3 ELSE 4 END, "
        "nombre"
    ).fetchall()


def get_insumo(conn, insumo_id):
    return conn.execute("SELECT * FROM insumos WHERE id = ?", (insumo_id,)).fetchone()


def update_insumo_campos(conn, insumo_id, **campos):
    if not campos:
        return
    set_clause = ", ".join(f"{k} = ?" for k in campos)
    conn.execute(
        f"UPDATE insumos SET {set_clause} WHERE id = ?",
        (*campos.values(), insumo_id),
    )
    conn.commit()


def update_scores_masivo(conn, resultados):
    """resultados: lista de dicts {id, puntaje_ponderado, clase_abc}."""
    conn.executemany(
        "UPDATE insumos SET puntaje_ponderado = ?, clase_abc = ? WHERE id = ?",
        [(r["puntaje_ponderado"], r["clase_abc"], r["id"]) for r in resultados],
    )
    conn.commit()


def registrar_ingreso(conn, insumo_id, cantidad, proveedor, fecha, observacion=None):
    conn.execute(
        "INSERT INTO movimientos (insumo_id, tipo, cantidad, fecha, proveedor, observacion, creado_en) "
        "VALUES (?, 'ingreso', ?, ?, ?, ?, ?)",
        (insumo_id, cantidad, fecha, proveedor, observacion, datetime.now().isoformat(timespec="seconds")),
    )
    conn.execute(
        "UPDATE insumos SET stock_actual = stock_actual + ? WHERE id = ?",
        (cantidad, insumo_id),
    )
    conn.commit()


def registrar_egreso(conn, insumo_id, cantidad, ensayo_ot, responsable, fecha, observacion=None):
    insumo = get_insumo(conn, insumo_id)
    if insumo is None:
        raise ValueError("Insumo no encontrado.")
    if cantidad > insumo["stock_actual"]:
        raise ValueError(
            f"Stock insuficiente: disponible {insumo['stock_actual']:g}, solicitado {cantidad:g}."
        )
    conn.execute(
        "INSERT INTO movimientos (insumo_id, tipo, cantidad, fecha, ensayo_ot, responsable, observacion, creado_en) "
        "VALUES (?, 'egreso', ?, ?, ?, ?, ?, ?)",
        (insumo_id, cantidad, fecha, ensayo_ot, responsable, observacion, datetime.now().isoformat(timespec="seconds")),
    )
    conn.execute(
        "UPDATE insumos SET stock_actual = stock_actual - ? WHERE id = ?",
        (cantidad, insumo_id),
    )
    conn.commit()


def list_movimientos(conn, insumo_id=None, limit=200):
    if insumo_id:
        return conn.execute(
            "SELECT m.*, i.nombre AS insumo_nombre FROM movimientos m "
            "JOIN insumos i ON i.id = m.insumo_id WHERE m.insumo_id = ? "
            "ORDER BY m.id DESC LIMIT ?",
            (insumo_id, limit),
        ).fetchall()
    return conn.execute(
        "SELECT m.*, i.nombre AS insumo_nombre FROM movimientos m "
        "JOIN insumos i ON i.id = m.insumo_id ORDER BY m.id DESC LIMIT ?",
        (limit,),
    ).fetchall()


def list_consumo_operaciones(conn):
    return conn.execute("SELECT * FROM consumo_operaciones ORDER BY operacion, insumo").fetchall()
