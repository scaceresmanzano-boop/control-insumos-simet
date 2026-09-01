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
    operacion TEXT,
    unidad TEXT,
    costo_unitario REAL,
    unidades_por_cambio REAL,
    frecuencia_uso_mensual REAL,
    rendimiento_probetas REAL,
    impacto_operacional INTEGER,
    tiempo_reposicion_dias REAL,
    fuente_dato TEXT,
    ubicacion TEXT,
    puntaje_ponderado REAL,
    clase_abc TEXT CHECK (clase_abc IN ('A','B','C') OR clase_abc IS NULL),
    stock_actual REAL NOT NULL DEFAULT 0,
    stock_minimo REAL,
    proveedor TEXT,
    codigo TEXT UNIQUE
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
    ram_asociado TEXT,
    observacion TEXT,
    creado_en TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    iniciales TEXT UNIQUE NOT NULL
);
"""

CATEGORIAS = [
    "Consumible de ensayo",
    "Rendimiento múltiple (herramienta)",
    "EPP-Seguridad",
    "Insumo general",
]

USUARIOS_INICIALES = [
    "GRC", "RCG", "SRS", "ARR", "DPG", "ASH", "SCM", "JAG", "MRR", "DBD",
    "ACA", "BAZ", "SML", "AVR", "CCE", "MMG", "DHU", "GCS", "PCP",
]

OTRO_USUARIO = "➕ Otro (nuevo)"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# Columnas agregadas en versiones posteriores al esquema inicial de insumos;
# se agregan solas (ALTER TABLE) a una base de datos ya existente que no las tenga.
COLUMNAS_NUEVAS_INSUMOS = {
    "codigo": "TEXT",
    "operacion": "TEXT",
    "unidades_por_cambio": "REAL",
    "rendimiento_probetas": "REAL",
    "fuente_dato": "TEXT",
    "ubicacion": "TEXT",
}


def init_schema(conn):
    conn.executescript(SCHEMA)
    columnas = {row["name"] for row in conn.execute("PRAGMA table_info(insumos)")}
    for nombre, tipo in COLUMNAS_NUEVAS_INSUMOS.items():
        if nombre not in columnas:
            conn.execute(f"ALTER TABLE insumos ADD COLUMN {nombre} {tipo}")
    if "codigo" not in columnas:
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_insumos_codigo ON insumos(codigo) WHERE codigo IS NOT NULL"
        )
    columnas_mov = {row["name"] for row in conn.execute("PRAGMA table_info(movimientos)")}
    if "ram_asociado" not in columnas_mov:
        conn.execute("ALTER TABLE movimientos ADD COLUMN ram_asociado TEXT")
    sin_usuarios = conn.execute("SELECT COUNT(*) AS n FROM usuarios").fetchone()["n"] == 0
    if sin_usuarios:
        conn.executemany(
            "INSERT OR IGNORE INTO usuarios (iniciales) VALUES (?)",
            [(i,) for i in dict.fromkeys(USUARIOS_INICIALES)],
        )
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


def get_insumo_por_codigo(conn, codigo):
    codigo = (codigo or "").strip()
    if not codigo:
        return None
    return conn.execute("SELECT * FROM insumos WHERE codigo = ?", (codigo,)).fetchone()


def _codigo_para_id(insumo_id):
    # Sin guion a propósito: algunos lectores de código de barras están
    # configurados con un layout de teclado distinto al de Windows y el
    # símbolo "-" puede llegar como otro carácter (ej. "'"). Usar solo
    # letras/números evita ese problema por completo.
    return f"INS{insumo_id:04d}"


def set_codigo(conn, insumo_id, codigo):
    codigo = codigo.strip() if codigo else None
    if codigo:
        existente = conn.execute(
            "SELECT id FROM insumos WHERE codigo = ? AND id != ?", (codigo, insumo_id)
        ).fetchone()
        if existente:
            raise ValueError(f"El código '{codigo}' ya está asignado al insumo ID {existente['id']}.")
    conn.execute("UPDATE insumos SET codigo = ? WHERE id = ?", (codigo, insumo_id))
    conn.commit()


def asignar_codigos_automaticos(conn):
    """Genera un código INS-NNNN para cada insumo que todavía no tiene uno. Devuelve cuántos asignó."""
    sin_codigo = conn.execute("SELECT id FROM insumos WHERE codigo IS NULL").fetchall()
    for row in sin_codigo:
        conn.execute("UPDATE insumos SET codigo = ? WHERE id = ?", (_codigo_para_id(row["id"]), row["id"]))
    conn.commit()
    return len(sin_codigo)


def crear_insumo(conn, nombre, categoria=None, operacion=None, unidad=None, stock_actual=0,
                  proveedor=None, costo_unitario=None, unidades_por_cambio=None,
                  frecuencia_uso_mensual=None, rendimiento_probetas=None,
                  impacto_operacional=None, tiempo_reposicion_dias=None,
                  fuente_dato=None, ubicacion=None, codigo=None):
    nombre = nombre.strip()
    if not nombre:
        raise ValueError("El nombre del insumo no puede estar vacío.")
    existente = conn.execute(
        "SELECT id FROM insumos WHERE LOWER(nombre) = LOWER(?)", (nombre,)
    ).fetchone()
    if existente:
        raise ValueError(f"Ya existe un insumo llamado '{nombre}' (ID {existente['id']}).")

    codigo = codigo.strip() if codigo else None
    if codigo:
        existente_codigo = conn.execute("SELECT id FROM insumos WHERE codigo = ?", (codigo,)).fetchone()
        if existente_codigo:
            raise ValueError(f"El código '{codigo}' ya está asignado al insumo ID {existente_codigo['id']}.")

    nuevo_id = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 AS siguiente FROM insumos").fetchone()["siguiente"]
    conn.execute(
        """
        INSERT INTO insumos (id, nombre, categoria, operacion, unidad, costo_unitario,
                              unidades_por_cambio, frecuencia_uso_mensual, rendimiento_probetas,
                              impacto_operacional, tiempo_reposicion_dias, fuente_dato, ubicacion,
                              stock_actual, proveedor, codigo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (nuevo_id, nombre, categoria, operacion, unidad, costo_unitario, unidades_por_cambio,
         frecuencia_uso_mensual, rendimiento_probetas, impacto_operacional, tiempo_reposicion_dias,
         fuente_dato, ubicacion, stock_actual, proveedor, codigo or _codigo_para_id(nuevo_id)),
    )
    conn.commit()
    return nuevo_id


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
    """resultados: lista de dicts {id, puntaje_ponderado, clase_abc, stock_minimo}."""
    conn.executemany(
        "UPDATE insumos SET puntaje_ponderado = ?, clase_abc = ?, stock_minimo = ? WHERE id = ?",
        [(r["puntaje_ponderado"], r["clase_abc"], r.get("stock_minimo"), r["id"]) for r in resultados],
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


def registrar_egreso(conn, insumo_id, cantidad, ensayo_ot, responsable, fecha, ram_asociado=None, observacion=None):
    insumo = get_insumo(conn, insumo_id)
    if insumo is None:
        raise ValueError("Insumo no encontrado.")
    if cantidad > insumo["stock_actual"]:
        raise ValueError(
            f"Stock insuficiente: disponible {insumo['stock_actual']:g}, solicitado {cantidad:g}."
        )
    conn.execute(
        "INSERT INTO movimientos (insumo_id, tipo, cantidad, fecha, ensayo_ot, responsable, ram_asociado, observacion, creado_en) "
        "VALUES (?, 'egreso', ?, ?, ?, ?, ?, ?, ?)",
        (insumo_id, cantidad, fecha, ensayo_ot, responsable, ram_asociado, observacion, datetime.now().isoformat(timespec="seconds")),
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


def get_ultimo_egreso(conn, insumo_id):
    return conn.execute(
        "SELECT * FROM movimientos WHERE insumo_id = ? AND tipo = 'egreso' ORDER BY id DESC LIMIT 1",
        (insumo_id,),
    ).fetchone()


def list_usuarios(conn):
    return [row["iniciales"] for row in conn.execute("SELECT iniciales FROM usuarios ORDER BY iniciales")]


def crear_usuario(conn, iniciales):
    iniciales = iniciales.strip().upper()
    if not iniciales:
        raise ValueError("Las iniciales no pueden estar vacías.")
    conn.execute("INSERT OR IGNORE INTO usuarios (iniciales) VALUES (?)", (iniciales,))
    conn.commit()
    return iniciales
